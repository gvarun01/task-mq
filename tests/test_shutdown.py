import pytest
import time
import threading
import signal
import os
from taskmq.worker import Worker
from taskmq.jobs import handlers
from taskmq.storage.base import JobStatus

@handlers.register_handler("slow_job")
def slow_job(job):
    time.sleep(2)
    return "done"

def test_graceful_shutdown(backend):
    """
    Test that worker finishes active jobs on shutdown.
    """
    # 1. Insert a slow job
    job_id = backend.insert_job("slow", handler="slow_job")
    
    w = Worker(max_workers=1, backend=backend, poll_interval=0.1)
    
    # Start worker in a thread
    t = threading.Thread(target=w.start)
    t.start()
    
    # Wait for job to be picked up (status RUNNING)
    start_time = time.time()
    while time.time() - start_time < 5:
        job = backend.get_job(job_id)
        if job.status == JobStatus.RUNNING:
            break
        time.sleep(0.1)
        
    assert job.status == JobStatus.RUNNING
    
    # 2. Initiate shutdown (simulate signal or call stop)
    # Since we can't easily send signal to thread, we call stop() directly
    # which sets the event, mimicking the signal handler.
    print("Stopping worker...")
    w.stop()
    
    # 3. Wait for worker thread to finish
    t.join()
    
    # 4. Verify job finished successfully
    job = backend.get_job(job_id)
    assert job.status == JobStatus.SUCCESS
    assert job.result == "done"
