import pytest
import time
from datetime import datetime, timedelta, UTC
from taskmq.storage.redis_backend import RedisBackend
from taskmq.storage.base import JobStatus
import os

# Skip if redis is not available or not configured
redis_url = os.getenv("TASKMQ_REDIS_URL", "redis://localhost:6379/0")

@pytest.fixture
def redis_backend():
    try:
        backend = RedisBackend(redis_url=redis_url)
        if not backend.check_health():
            pytest.skip("Redis not available")
        # Clean up
        backend.redis.flushdb()
        return backend
    except ImportError:
        pytest.skip("Redis package not installed")
    except Exception:
        pytest.skip("Redis connection failed")

def test_insert_and_fetch_job(redis_backend):
    job_id = redis_backend.insert_job({"task": "test"}, handler="dummy")
    assert job_id > 0
    
    # Fetch
    job = redis_backend.fetch_job("worker1")
    assert job is not None
    assert job.id == job_id
    assert job.status == JobStatus.RUNNING # fetch_job sets status to RUNNING in my implementation? 
    # Wait, my fetch_job implementation sets status to RUNNING in Lua script!
    # "redis.call('HSET', job_key_prefix .. job_id, 'locked_by', worker_id, 'lock_expires_at', lock_expires_iso, 'status', 'RUNNING')"
    
    assert job.locked_by == "worker1"

def test_scheduled_job(redis_backend):
    future = datetime.now(UTC) + timedelta(seconds=2)
    job_id = redis_backend.insert_job({"task": "future"}, scheduled_for=future)
    
    # Should not fetch yet
    job = redis_backend.fetch_job("worker1")
    assert job is None
    
    # Wait
    time.sleep(2.5)
    job = redis_backend.fetch_job("worker1")
    assert job is not None
    assert job.id == job_id

def test_periodic_job(redis_backend):
    job_id = redis_backend.insert_job({"task": "periodic"}, interval_seconds=1)
    
    # Fetch and complete
    job = redis_backend.fetch_job("worker1")
    assert job is not None
    
    redis_backend.update_status(job.id, JobStatus.SUCCESS)
    
    # Reschedule
    redis_backend.reschedule_periodic_jobs()
    
    # Should be pending again (but scheduled in future)
    # We need to wait for interval (1s)
    time.sleep(1.5)
    
    # Fetch again
    job = redis_backend.fetch_job("worker1")
    assert job is not None
    assert job.id == job_id
