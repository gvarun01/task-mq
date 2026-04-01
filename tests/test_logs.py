import pytest
import time
import threading
from taskmq.worker import Worker
from taskmq.jobs import handlers
from taskmq.storage.base import JobStatus

@handlers.register_handler("log_test")
def log_test(job):
    return "success"

def test_job_logs(backend):
    """
    Test that job logs are created and retrievable.
    """
    job_id = backend.insert_job("payload", handler="log_test")
    
    w = Worker(max_workers=1, backend=backend, poll_interval=0.1)
    t = threading.Thread(target=w.start)
    t.start()
    
    try:
        # Wait for completion
        start_time = time.time()
        while time.time() - start_time < 5:
            job = backend.get_job(job_id)
            if job.status == JobStatus.SUCCESS:
                break
            time.sleep(0.1)
            
        assert job.status == JobStatus.SUCCESS
        
        # Check logs
        logs = backend.get_logs(job_id=job_id)
        assert len(logs) >= 2 # Started, Finished
        
        messages = [l['message'] for l in logs]
        assert "Job started" in messages
        assert "Job finished successfully" in messages
        
        # Check handler filter (if supported by backend implementation logic)
        # SQLite supports it. Redis supports it via our implementation.
        logs_handler = backend.get_logs(handler="log_test")
        assert len(logs_handler) >= 2
        
    finally:
        w.stop()
        t.join()
