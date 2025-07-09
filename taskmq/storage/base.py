from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Any, Optional
from abc import ABC, abstractmethod

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
    created_at: datetime = field(default_factory=datetime.utcnow)
    retries: int = 0
    error_log: Optional[str] = None
    retry_policy: str = "exponential"  # 'fixed', 'exponential', 'none'
    scheduled_for: datetime = field(default_factory=datetime.utcnow)
    interval_seconds: Optional[int] = None 
    handler: Optional[str] = None 
    locked_by: Optional[str] = None
    lock_expires_at: Optional[datetime] = None 

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