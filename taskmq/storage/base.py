from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, UTC
from typing import Any, Optional
from abc import ABC, abstractmethod


def _utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(UTC)

class JobStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

@dataclass
class Job:
    id: int
    status: JobStatus = JobStatus.PENDING
    payload: Any = None
    created_at: datetime = field(default_factory=_utc_now)
    retries: int = 0
    error_log: Optional[str] = None
    retry_policy: str = "exponential"  # 'fixed', 'exponential', 'none'
    scheduled_for: datetime = field(default_factory=_utc_now)
    interval_seconds: Optional[int] = None 
    handler: Optional[str] = None 
    locked_by: Optional[str] = None
    lock_expires_at: Optional[datetime] = None
    result: Any = None
    priority: int = 0  # 0=Low, 10=Normal, 20=High
    handler_hash: Optional[str] = None

class QueueBackend(ABC):
    @abstractmethod
    def insert_job(self, payload: Any, retry_policy: str = "exponential", scheduled_for: Optional[datetime] = None, interval_seconds: Optional[int] = None, handler: Optional[str] = None, priority: int = 0) -> int:
        pass

    @abstractmethod
    def fetch_job(self, worker_id: str, lock_timeout: int = 30) -> Optional[Job]:
        pass

    @abstractmethod
    def update_status(self, job_id: int, status: JobStatus, retries: int = 0, error_log: Optional[str] = None, result: Any = None, handler_hash: Optional[str] = None):
        pass

    @abstractmethod
    def move_to_dlq(self, job_id: int, error_log: Optional[str] = None) -> None:
        pass

    @abstractmethod
    def list_dead_jobs(self, limit: int = 100, offset: int = 0) -> list[Job]:
        pass

    @abstractmethod
    def replay_dead_job(self, job_id: int) -> Optional[int]:
        pass

    @abstractmethod
    def get_job(self, job_id: int) -> Optional[Job]:
        pass

    @abstractmethod
    def add_log(self, job_id: int, level: str, message: str, handler: Optional[str] = None):
        pass

    @abstractmethod
    def get_logs(self, job_id: Optional[int] = None, handler: Optional[str] = None, limit: int = 100) -> list[dict]:
        pass

    @abstractmethod
    def requeue_expired_locks(self):
        pass

    @abstractmethod
    def reschedule_periodic_jobs(self):
        pass

    @abstractmethod
    def get_queue_depth(self) -> int:
        pass

    @abstractmethod
    def check_health(self) -> bool:
        pass