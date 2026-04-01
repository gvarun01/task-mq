import asyncio
import inspect
import logging
import os
import signal
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Callable, Optional

from prometheus_client import Counter, Gauge, Summary

from taskmq.jobs.handlers import get_handler, get_handler_hash
from taskmq.storage import get_backend
from taskmq.storage.base import JobStatus, QueueBackend

logger = logging.getLogger(__name__)

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

class Worker:
    def __init__(self, func: Callable = None, backend: QueueBackend = None, max_retries: int = 3, poll_interval: float = 1.0, max_workers: int = 1, worker_id: Optional[str] = None, lock_timeout: int = 30):
        self.func = func
        self.backend = backend or get_backend()
        self.max_retries = max_retries
        self.poll_interval = poll_interval
        self.max_workers = max_workers
        self.worker_id = worker_id or str(uuid.uuid4())
        self.lock_timeout = lock_timeout
        self._stop_event = threading.Event()
        self._active_jobs = 0
        self._active_lock = threading.Lock()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._periodic_thread = threading.Thread(target=self._periodic_loop, daemon=True)
        self._lock_requeue_thread = threading.Thread(target=self._lock_requeue_loop, daemon=True)

    @property
    def active_jobs(self):
        with self._active_lock:
            return self._active_jobs

    def _signal_handler(self, signum, frame):
        print(f"\n🛑 Received signal {signum}. Initiating graceful shutdown...")
        self.stop()
        print(f"Waiting for {self.active_jobs} active jobs to complete...")

    def start(self):
        # Register signal handlers for graceful shutdown
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except ValueError:
            # Signals only work in main thread
            pass

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
                            self.backend.add_log(job.id, "INFO", "Job started", job.handler)
                            with self._active_lock:
                                self._active_jobs += 1
                            executor.submit(self._process_job_wrapper, job)
                        else:
                            time.sleep(self.poll_interval)
            else:
                while not self._stop_event.is_set():
                    self._update_queue_depth()
                    try:
                        job = self.backend.fetch_job(self.worker_id, self.lock_timeout)
                    except Exception as e:
                        print(f"Error fetching job: {e}")
                        time.sleep(self.poll_interval)
                        continue
                        
                    if job:
                        self.backend.update_status(job.id, JobStatus.RUNNING, job.retries, None)
                        self.backend.add_log(job.id, "INFO", "Job started", job.handler)
                        with self._active_lock:
                            self._active_jobs += 1
                        self._process_job_wrapper(job)
                    else:
                        time.sleep(self.poll_interval)
        finally:
            self._stop_event.set()
            self._remove_heartbeat()

    def _process_job_wrapper(self, job):
        try:
            self._process_job(job)
        finally:
            with self._active_lock:
                self._active_jobs -= 1

    def stop(self):
        self._stop_event.set()
        self._remove_heartbeat()

    def _heartbeat_loop(self):
        while not self._stop_event.is_set():
            with open(HEARTBEAT_PATH, 'w') as f:
                f.write(datetime.now(UTC).isoformat())
            time.sleep(HEARTBEAT_INTERVAL)

    def _periodic_loop(self):
        while not self._stop_event.is_set():
            try:
                self.backend.reschedule_periodic_jobs()
            except Exception:
                logger.debug("Error rescheduling periodic jobs", exc_info=True)
            time.sleep(1)

    @TASK_DURATION.time()
    def _process_job(self, job):
        result = None
        handler_hash = None
        try:
            handler_name = getattr(job, 'handler', None)
            if handler_name:
                handler = get_handler(handler_name)
                if not handler:
                    raise Exception(f"Unknown handler: {handler_name}")
                
                handler_hash = get_handler_hash(handler_name)
                
                if inspect.iscoroutinefunction(handler):
                    result = asyncio.run(handler(job))
                else:
                    result = handler(job)
                    if inspect.iscoroutine(result):
                        result = asyncio.run(result)
            elif self.func:
                # If using a direct function (not recommended for replay/hash), we can't easily get hash unless we inspect self.func
                # But self.func is usually passed to Worker constructor, not registered by name.
                if inspect.iscoroutinefunction(self.func):
                    result = asyncio.run(self.func(job))
                else:
                    result = self.func(job)
                    if inspect.iscoroutine(result):
                        result = asyncio.run(result)
            else:
                raise Exception("No handler specified for job and no default func provided.")
            self.backend.update_status(job.id, JobStatus.SUCCESS, job.retries, None, result=result, handler_hash=handler_hash)
            self.backend.add_log(job.id, "INFO", "Job finished successfully", job.handler)
            JOBS_PROCESSED.inc()
        except Exception as e:
            job.retries += 1
            RETRIES.inc()
            error_log = str(e)
            self.backend.add_log(job.id, "ERROR", f"Job failed: {error_log}", job.handler)
            # Retry policy logic
            if job.retry_policy == "none":
                self.backend.move_to_dlq(job.id, error_log)
                self._log_failed_job(job, error_log)
                FAILURES.inc()
                return
            if job.retries >= self.max_retries:
                self.backend.move_to_dlq(job.id, error_log)
                self._log_failed_job(job, error_log)
                FAILURES.inc()
            else:
                self.backend.update_status(job.id, JobStatus.PENDING, job.retries, error_log)
                self.backend.add_log(job.id, "WARNING", f"Job scheduled for retry ({job.retries}/{self.max_retries})", job.handler)
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
        try:
            count = self.backend.get_queue_depth()
            QUEUE_DEPTH.set(count)
        except Exception:
            logger.debug("Error updating queue depth", exc_info=True)

    def _remove_heartbeat(self):
        try:
            os.remove(HEARTBEAT_PATH)
        except FileNotFoundError:
            pass 

    def _lock_requeue_loop(self):
        while not self._stop_event.is_set():
            self.backend.requeue_expired_locks()
            time.sleep(2) 