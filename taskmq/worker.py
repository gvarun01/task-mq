import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional
from taskmq.storage.base import JobStatus
from datetime import datetime, UTC, timedelta
import os
from prometheus_client import Counter, Gauge, Summary
from taskmq.storage.sqlite_backend import QueueBackend, SQLiteBackend
import uuid
from taskmq.jobs.handlers import HANDLERS, register_handler, get_handler

FAILED_LOG_PATH = 'failed_jobs.log'
HEARTBEAT_PATH = 'worker_heartbeat.txt'
HEARTBEAT_INTERVAL = 5  # seconds
FIXED_RETRY_INTERVAL = 2  # seconds
EXPONENTIAL_BASE = 2

# Prometheus metrics
JOBS_PROCESSED = Counter('jobs_processed_total', 'Total jobs processed')
QUEUE_DEPTH = Gauge('queue_depth', 'Current queue depth')
TASK_DURATION = Summary('task_duration_seconds', 'Task duration in seconds')
RETRIES = Counter('job_retries_total', 'Total number of job retries')
FAILURES = Counter('job_failures_total', 'Total number of job failures')

HANDLERS = {}

def register_handler(name):
    def decorator(func):
        HANDLERS[name] = func
        return func
    return decorator

class Worker:
    def __init__(self, func: Callable = None, backend: QueueBackend = None, max_retries: int = 3, poll_interval: float = 1.0, max_workers: int = 1, worker_id: Optional[str] = None, lock_timeout: int = 30):
        self.func = func
        self.backend = backend or SQLiteBackend()
        self.max_retries = max_retries
        self.poll_interval = poll_interval
        self.max_workers = max_workers
        self.worker_id = worker_id or str(uuid.uuid4())
        self.lock_timeout = lock_timeout
        self._stop_event = threading.Event()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._periodic_thread = threading.Thread(target=self._periodic_loop, daemon=True)
        self._lock_requeue_thread = threading.Thread(target=self._lock_requeue_loop, daemon=True)

    def start(self):
        self._heartbeat_thread.start()
        self._periodic_thread.start()
        self._lock_requeue_thread.start()
        try:
            if self.max_workers > 1:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    while not self._stop_event.is_set():
                        self._update_queue_depth()
                        job = self.backend.fetch_job(self.worker_id, self.lock_timeout)
                        if job:
                            self.backend.update_status(job.id, JobStatus.RUNNING, job.retries, None)
                            executor.submit(self._process_job, job)
                        else:
                            time.sleep(self.poll_interval)
            else:
                while not self._stop_event.is_set():
                    self._update_queue_depth()
                    job = self.backend.fetch_job(self.worker_id, self.lock_timeout)
                    if job:
                        self.backend.update_status(job.id, JobStatus.RUNNING, job.retries, None)
                        self._process_job(job)
                    else:
                        time.sleep(self.poll_interval)
        finally:
            self._stop_event.set()
            self._remove_heartbeat()

    def stop(self):
        self._stop_event.set()
        self._remove_heartbeat()

    def _heartbeat_loop(self):
        while not self._stop_event.is_set():
            with open(HEARTBEAT_PATH, 'w') as f:
                f.write(datetime.now(UTC).isoformat())
            time.sleep(HEARTBEAT_INTERVAL)

    def _periodic_loop(self):
        import sqlite3
        while not self._stop_event.is_set():
            # Scan for periodic jobs that are SUCCESS and have interval_seconds set
            conn = None
            try:
                conn = self.backend.db_path and sqlite3.connect(self.backend.db_path)
                if conn:
                    c = conn.cursor()
                    c.execute('SELECT id, interval_seconds FROM jobs WHERE interval_seconds IS NOT NULL AND status = ?', (JobStatus.SUCCESS.value,))
                    for row in c.fetchall():
                        job_id, interval = row
                        if interval:
                            # Reschedule job
                            next_time = (datetime.now(UTC) + timedelta(seconds=interval)).isoformat()
                            c.execute('UPDATE jobs SET status = ?, scheduled_for = ?, retries = 0, error_log = NULL WHERE id = ?', (JobStatus.PENDING.value, next_time, job_id))
                    conn.commit()
            except Exception as e:
                pass
            finally:
                if conn:
                    conn.close()
            time.sleep(1)

    @TASK_DURATION.time()
    def _process_job(self, job):
        try:
            handler_name = getattr(job, 'handler', None)
            if handler_name:
                handler = get_handler(handler_name)
                if not handler:
                    raise Exception(f"Unknown handler: {handler_name}")
                handler(job)
            elif self.func:
                self.func(job)
            else:
                raise Exception("No handler specified for job and no default func provided.")
            self.backend.update_status(job.id, JobStatus.SUCCESS, job.retries, None)
            JOBS_PROCESSED.inc()
        except Exception as e:
            job.retries += 1
            RETRIES.inc()
            error_log = str(e)
            # Retry policy logic
            if job.retry_policy == "none":
                self.backend.update_status(job.id, JobStatus.FAILED, job.retries, error_log)
                self._log_failed_job(job, error_log)
                FAILURES.inc()
                return
            if job.retries >= self.max_retries:
                self.backend.update_status(job.id, JobStatus.FAILED, job.retries, error_log)
                self._log_failed_job(job, error_log)
                FAILURES.inc()
            else:
                self.backend.update_status(job.id, JobStatus.PENDING, job.retries, error_log)
                # Backoff based on policy
                if job.retry_policy == "fixed":
                    time.sleep(FIXED_RETRY_INTERVAL)
                elif job.retry_policy == "exponential":
                    time.sleep(EXPONENTIAL_BASE ** job.retries)
                else:
                    pass  # No sleep for unknown policy

    def _log_failed_job(self, job, error_log):
        with open(FAILED_LOG_PATH, 'a') as f:
            f.write(f"[{datetime.now(UTC).isoformat()}] Job ID: {job.id}, Payload: {job.payload}, Retries: {job.retries}, Error: {error_log}\n")

    def _update_queue_depth(self):
        # Count jobs with PENDING status
        import sqlite3
        conn = sqlite3.connect(self.backend.db_path)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM jobs WHERE status = ?', (JobStatus.PENDING.value,))
        count = c.fetchone()[0]
        conn.close()
        QUEUE_DEPTH.set(count)

    def _remove_heartbeat(self):
        try:
            os.remove(HEARTBEAT_PATH)
        except FileNotFoundError:
            pass 

    def _lock_requeue_loop(self):
        while not self._stop_event.is_set():
            self.backend.requeue_expired_locks()
            time.sleep(2) 