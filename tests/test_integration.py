import pytest
import time
import threading
from taskmq.worker import Worker
from taskmq.jobs import handlers
from taskmq.storage.base import JobStatus

def test_full_lifecycle(backend):
    """
    Test the full lifecycle of a job:
    1. Insert job
    2. Worker picks it up
    3. Handler executes
    4. Result is stored
    5. Job status is SUCCESS
    """
    
    # Register a unique handler
    handler_name = f"lifecycle_{time.time()}"
    event = threading.Event()
    
    @handlers.register_handler(handler_name)
    def lifecycle_handler(job):
        event.set()
        return {"processed": True, "payload": job.payload}

    # 1. Insert job
    payload = {"data": "test_lifecycle"}
    job_id = backend.insert_job(payload, handler=handler_name)
    assert job_id is not None

    # 2. Start worker
    w = Worker(max_workers=1, backend=backend, poll_interval=0.1)
    t = threading.Thread(target=w.start)
    t.start()

    try:
        # 3. Wait for handler
        assert event.wait(timeout=5), "Handler was not called"
        
        # 4. Check result
        # Give a little time for the worker to update status after handler returns
        for _ in range(10):
            job = backend.get_job(job_id)
            if job.status == JobStatus.SUCCESS:
                break
            time.sleep(0.1)
            
        assert job.status == JobStatus.SUCCESS
        # Result is a string representation of the dict returned by handler
        # The payload inside is also a string because backend stores payload as string
        result_str = job.result
        assert "'processed': True" in result_str
        assert "test_lifecycle" in result_str

    finally:
        w.stop()
        t.join()

def test_retry_logic(backend):
    """
    Test that a failing job is retried according to policy.
    """
    from unittest.mock import patch
    
    handler_name = f"retry_{time.time()}"
    call_count = 0
    
    @handlers.register_handler(handler_name)
    def retry_handler(job):
        nonlocal call_count
        call_count += 1
        raise Exception("Fail intentionally")

    # Insert job with fixed retry policy
    job_id = backend.insert_job("fail", handler=handler_name, retry_policy="fixed")
    
    # Patch retry interval to be very short
    with patch("taskmq.worker.FIXED_RETRY_INTERVAL", 0.1):
        w = Worker(max_workers=1, backend=backend, poll_interval=0.1)
        t = threading.Thread(target=w.start)
        t.start()
        
        try:
            # Wait enough time for multiple retries
            # 0.1s retry interval + processing overhead. 2 seconds should be plenty for > 1 retry.
            time.sleep(2)
            
            w.stop()
            t.join()
            
            # Should have retried at least once (call_count > 1 means retries happened)
            assert call_count > 1, f"Expected multiple calls, got {call_count}"
            
            # Job may still be in main table (if retries < max) or moved to DLQ (if exhausted)
            job = backend.get_job(job_id)
            if job is not None:
                # Job still in main table - verify retries occurred
                assert job.retries > 0
            else:
                # Job moved to DLQ after exhausting retries - this is also valid behavior
                # The call_count assertion above already proves retries happened
                pass
            
        finally:
            if t.is_alive():
                w.stop()
                t.join()

def test_scheduled_job_execution(backend):
    """
    Test that a scheduled job is not picked up before its time.
    """
    from datetime import datetime, timedelta, UTC
    
    handler_name = f"scheduled_{time.time()}"
    event = threading.Event()
    
    @handlers.register_handler(handler_name)
    def scheduled_handler(job):
        event.set()

    # Schedule for 3 seconds in future
    future = datetime.now(UTC) + timedelta(seconds=3)
    job_id = backend.insert_job("scheduled", handler=handler_name, scheduled_for=future)
    
    w = Worker(max_workers=1, backend=backend, poll_interval=0.1)
    t = threading.Thread(target=w.start)
    t.start()
    
    try:
        # Should not run immediately
        assert not event.wait(timeout=1)
        
        # Should run after 3 seconds (total wait > 3)
        assert event.wait(timeout=4)
        
    finally:
        w.stop()
        t.join()
