import sqlite3
from datetime import datetime, UTC, timedelta
from typing import Optional, Any
from taskmq.storage.base import Job, JobStatus, QueueBackend

DB_PATH = 'taskmq.db'


class SQLiteBackend(QueueBackend):
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL,
                payload TEXT,
                created_at TEXT NOT NULL,
                retries INTEGER NOT NULL,
                error_log TEXT,
                retry_policy TEXT DEFAULT 'exponential',
                scheduled_for TEXT NOT NULL DEFAULT '',
                interval_seconds INTEGER,
                handler TEXT,
                locked_by TEXT,
                lock_expires_at TEXT,
                result TEXT,
                priority INTEGER DEFAULT 0
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS dead_jobs (
                id INTEGER PRIMARY KEY,
                status TEXT NOT NULL,
                payload TEXT,
                created_at TEXT NOT NULL,
                retries INTEGER NOT NULL,
                error_log TEXT,
                retry_policy TEXT DEFAULT 'exponential',
                scheduled_for TEXT NOT NULL DEFAULT '',
                interval_seconds INTEGER,
                handler TEXT,
                locked_by TEXT,
                lock_expires_at TEXT,
                result TEXT,
                priority INTEGER DEFAULT 0
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS job_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                handler TEXT,
                level TEXT,
                message TEXT,
                timestamp TEXT
            )
        ''')
        try:
            c.execute('ALTER TABLE jobs ADD COLUMN result TEXT')
        except sqlite3.OperationalError:
            pass 
        try:
            c.execute('ALTER TABLE jobs ADD COLUMN priority INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        try:
            c.execute('ALTER TABLE jobs ADD COLUMN handler_hash TEXT')
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()

    def insert_job(self, payload: Any, retry_policy: str = "exponential", scheduled_for: Optional[datetime] = None, interval_seconds: Optional[int] = None, handler: Optional[str] = None, locked_by: Optional[str] = None, lock_expires_at: Optional[datetime] = None, priority: int = 0) -> int:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = datetime.now(UTC).isoformat()
        scheduled = (scheduled_for or datetime.now(UTC)).isoformat()
        c.execute(
            'INSERT INTO jobs (status, payload, created_at, retries, error_log, retry_policy, scheduled_for, interval_seconds, handler, locked_by, lock_expires_at, priority) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (JobStatus.PENDING.value, str(payload), now, 0, None, retry_policy, scheduled, interval_seconds, handler, locked_by, lock_expires_at.isoformat() if lock_expires_at else None, priority)
        )
        job_id = c.lastrowid
        conn.commit()
        conn.close()
        return job_id

    def fetch_job(self, worker_id: str, lock_timeout: int = 30) -> Optional[Job]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = datetime.now(UTC)
        now_iso = now.isoformat()
        # Only fetch jobs that are not locked or whose lock has expired
        # Order by priority DESC (higher first), then scheduled_for ASC (older first)
        c.execute('''
            SELECT * FROM jobs WHERE status = ? AND scheduled_for <= ? AND 
            (locked_by IS NULL OR lock_expires_at IS NULL OR lock_expires_at <= ?)
            ORDER BY priority DESC, scheduled_for ASC, created_at ASC LIMIT 1
        ''', (JobStatus.PENDING.value, now_iso, now_iso))
        row = c.fetchone()
        if row:
            job_id = row[0]
            # Set lock
            lock_expires = (now + timedelta(seconds=lock_timeout)).isoformat()
            c.execute('UPDATE jobs SET locked_by = ?, lock_expires_at = ? WHERE id = ?', (worker_id, lock_expires, job_id))
            conn.commit()
            # Re-fetch with lock set
            c.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
            row = c.fetchone()
        conn.close()
        if row:
            return self._row_to_job(row)
        return None

    def update_status(self, job_id: int, status: JobStatus, retries: int = 0, error_log: Optional[str] = None, result: Any = None, handler_hash: Optional[str] = None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Clear lock when updating status
        # Also update handler_hash if provided
        if handler_hash:
            c.execute(
                'UPDATE jobs SET status = ?, retries = ?, error_log = ?, result = ?, locked_by = NULL, lock_expires_at = NULL, handler_hash = ? WHERE id = ?',
                (status.value, retries, error_log, str(result) if result is not None else None, handler_hash, job_id)
            )
        else:
            c.execute(
                'UPDATE jobs SET status = ?, retries = ?, error_log = ?, result = ?, locked_by = NULL, lock_expires_at = NULL WHERE id = ?',
                (status.value, retries, error_log, str(result) if result is not None else None, job_id)
            )
        conn.commit()
        conn.close()

    def get_job(self, job_id: int) -> Optional[Job]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return self._row_to_job(row)
        return None

    def _row_to_job(self, row) -> Job:
        return Job(
            id=row[0],
            status=JobStatus(row[1]),
            payload=row[2],
            created_at=datetime.fromisoformat(row[3]),
            retries=row[4],
            error_log=row[5],
            retry_policy=row[6] if len(row) > 6 and row[6] else "exponential",
            scheduled_for=datetime.fromisoformat(row[7]) if row[7] else datetime.now(UTC),
            interval_seconds=row[8] if len(row) > 8 else None,
            handler=row[9] if len(row) > 9 else None,
            locked_by=row[10] if len(row) > 10 else None,
            lock_expires_at=datetime.fromisoformat(row[11]) if len(row) > 11 and row[11] else None,
            result=row[12] if len(row) > 12 else None,
            priority=row[13] if len(row) > 13 else 0,
            handler_hash=row[14] if len(row) > 14 else None
        )

    def requeue_expired_locks(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = datetime.now(UTC).isoformat()
        c.execute('''
            UPDATE jobs SET status = ?, locked_by = NULL, lock_expires_at = NULL 
            WHERE status = ? AND lock_expires_at IS NOT NULL AND lock_expires_at <= ?
        ''', (JobStatus.PENDING.value, JobStatus.RUNNING.value, now))
        conn.commit()
        conn.close()

    def reschedule_periodic_jobs(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT id, interval_seconds FROM jobs WHERE interval_seconds IS NOT NULL AND status = ?', (JobStatus.SUCCESS.value,))
        for row in c.fetchall():
            job_id, interval = row
            if interval:
                # Reschedule job
                next_time = (datetime.now(UTC) + timedelta(seconds=interval)).isoformat()
                c.execute('UPDATE jobs SET status = ?, scheduled_for = ?, retries = 0, error_log = NULL WHERE id = ?', (JobStatus.PENDING.value, next_time, job_id))
        conn.commit()
        conn.close()

    def get_queue_depth(self) -> int:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM jobs WHERE status = ?', (JobStatus.PENDING.value,))
        count = c.fetchone()[0]
        conn.close()
        return count

    def check_health(self) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("SELECT 1")
            conn.close()
            return True
        except sqlite3.Error:
            return False

    def move_to_dlq(self, job_id: int, error_log: Optional[str] = None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
        row = c.fetchone()
        if row:
            # Insert into dead_jobs
            c.execute('''
                INSERT INTO dead_jobs (id, status, payload, created_at, retries, error_log, retry_policy, scheduled_for, interval_seconds, handler, locked_by, lock_expires_at, result, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (row[0], JobStatus.FAILED.value, row[2], row[3], row[4], error_log or row[5], row[6], row[7], row[8], row[9], None, None, row[12], row[13]))
            c.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
            conn.commit()
        conn.close()

    def list_dead_jobs(self, limit: int = 100, offset: int = 0) -> list[Job]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM dead_jobs ORDER BY created_at DESC LIMIT ? OFFSET ?', (limit, offset))
        rows = c.fetchall()
        conn.close()
        return [self._row_to_job(row) for row in rows]

    def replay_dead_job(self, job_id: int) -> Optional[int]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM dead_jobs WHERE id = ?', (job_id,))
        row = c.fetchone()
        new_id = None
        if row:
            now = datetime.now(UTC).isoformat()
            c.execute('''
                INSERT INTO jobs (status, payload, created_at, retries, error_log, retry_policy, scheduled_for, interval_seconds, handler, locked_by, lock_expires_at, result, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (JobStatus.PENDING.value, row[2], now, 0, None, row[6], now, row[8], row[9], None, None, None, row[13]))
            new_id = c.lastrowid
            c.execute('DELETE FROM dead_jobs WHERE id = ?', (job_id,))
            conn.commit()
        conn.close()
        return new_id

    def add_log(self, job_id: int, level: str, message: str, handler: Optional[str] = None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = datetime.now(UTC).isoformat()
        c.execute(
            'INSERT INTO job_logs (job_id, handler, level, message, timestamp) VALUES (?, ?, ?, ?, ?)',
            (job_id, handler, level, message, now)
        )
        conn.commit()
        conn.close()

    def get_logs(self, job_id: Optional[int] = None, handler: Optional[str] = None, limit: int = 100) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        query = 'SELECT * FROM job_logs WHERE 1=1'
        params = []
        if job_id:
            query += ' AND job_id = ?'
            params.append(job_id)
        if handler:
            query += ' AND handler = ?'
            params.append(handler)
        query += ' ORDER BY timestamp ASC LIMIT ?'
        params.append(limit)
        
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "job_id": row[1],
                "handler": row[2],
                "level": row[3],
                "message": row[4],
                "timestamp": row[5]
            }
            for row in rows
        ]
