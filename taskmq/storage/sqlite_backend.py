import sqlite3
from datetime import datetime, UTC, timedelta
from typing import Optional, Any
from taskmq.storage.base import Job, JobStatus
from abc import ABC, abstractmethod

DB_PATH = 'taskmq.db'

class QueueBackend(ABC):
    @abstractmethod
    def insert_job(self, payload: Any, retry_policy: str = "exponential", scheduled_for: Optional[datetime] = None, interval_seconds: Optional[int] = None) -> int:
        pass

    @abstractmethod
    def fetch_job(self) -> Optional[Job]:
        pass

    @abstractmethod
    def update_status(self, job_id: int, status: JobStatus, retries: int = 0, error_log: Optional[str] = None):
        pass

    @abstractmethod
    def get_job(self, job_id: int) -> Optional[Job]:
        pass

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
                lock_expires_at TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def insert_job(self, payload: Any, retry_policy: str = "exponential", scheduled_for: Optional[datetime] = None, interval_seconds: Optional[int] = None, handler: Optional[str] = None, locked_by: Optional[str] = None, lock_expires_at: Optional[datetime] = None) -> int:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = datetime.now(UTC).isoformat()
        scheduled = (scheduled_for or datetime.now(UTC)).isoformat()
        c.execute(
            'INSERT INTO jobs (status, payload, created_at, retries, error_log, retry_policy, scheduled_for, interval_seconds, handler, locked_by, lock_expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (JobStatus.PENDING.value, str(payload), now, 0, None, retry_policy, scheduled, interval_seconds, handler, locked_by, lock_expires_at.isoformat() if lock_expires_at else None)
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
        c.execute('''
            SELECT * FROM jobs WHERE status = ? AND scheduled_for <= ? AND 
            (locked_by IS NULL OR lock_expires_at IS NULL OR lock_expires_at <= ?)
            ORDER BY scheduled_for, created_at LIMIT 1
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
                lock_expires_at=datetime.fromisoformat(row[11]) if len(row) > 11 and row[11] else None
            )
        return None

    def update_status(self, job_id: int, status: JobStatus, retries: int = 0, error_log: Optional[str] = None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            'UPDATE jobs SET status = ?, retries = ?, error_log = ? WHERE id = ?',
            (status.value, retries, error_log, job_id)
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
                lock_expires_at=datetime.fromisoformat(row[11]) if len(row) > 11 and row[11] else None
            )
        return None

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