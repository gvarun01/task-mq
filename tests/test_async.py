import pytest
import asyncio
import threading
import time
from taskmq.worker import Worker
from taskmq.jobs import handlers
from taskmq.storage.base import JobStatus

@handlers.register_handler("async_test")
async def async_handler(job):
    await asyncio.sleep(0.1)
    return "async_success"

def test_async_handler(backend):
    """
    Test that the worker can execute an async handler.
    """
    job_id = backend.insert_job("test_payload", handler="async_test")
    
    w = Worker(max_workers=1, backend=backend, poll_interval=0.1)
    t = threading.Thread(target=w.start)
    t.start()
    
    try:
        # Poll for success
        start_time = time.time()
        while time.time() - start_time < 5:
            job = backend.get_job(job_id)
            if job.status == JobStatus.SUCCESS:
                assert job.result == "async_success"
                return
            if job.status == JobStatus.FAILED:
                assert False, f"Job failed with error: {job.error_log}"
            time.sleep(0.1)
            
        assert False, "Timeout waiting for async job"
    finally:
        w.stop()
        t.join()
