import pytest
import time
import threading
from taskmq.worker import Worker
from taskmq.jobs import handlers
from taskmq.storage.base import JobStatus

@handlers.register_handler("fail_handler")
def fail_handler(job):
    raise Exception("I failed!")

def test_dlq_workflow(backend):
    """
    Test DLQ workflow: Fail -> DLQ -> List -> Replay -> Pending
    """
    # 1. Insert a job that will fail immediately (retry_policy='none')
    job_id = backend.insert_job("fail_payload", handler="fail_handler", retry_policy="none")
    
    # 2. Run worker to process it
    w = Worker(max_workers=1, backend=backend, poll_interval=0.1)
    t = threading.Thread(target=w.start)
    t.start()
    
    try:
        # Wait for job to be processed and moved to DLQ
        # We can poll list_dead_jobs
        dead_jobs = []
        start_time = time.time()
        while time.time() - start_time < 5:
            dead_jobs = backend.list_dead_jobs()
            if dead_jobs:
                break
            time.sleep(0.1)
            
        assert len(dead_jobs) == 1
        dead_job = dead_jobs[0]
        assert dead_job.id == job_id
        assert dead_job.payload == "fail_payload"
        assert "I failed!" in dead_job.error_log
        
        # 3. Replay the job
        new_id = backend.replay_dead_job(job_id)
        assert new_id is not None
        
        # 4. Verify it's gone from DLQ
        dead_jobs = backend.list_dead_jobs()
        assert len(dead_jobs) == 0
        
        # 5. Verify it's back in the queue (we can fetch it or check status)
        # Since we are using the same backend instance, we can check get_job(new_id)
        replayed_job = backend.get_job(new_id)
        assert replayed_job is not None
        assert replayed_job.status == JobStatus.PENDING
        assert replayed_job.retries == 0
        
    finally:
        w.stop()
        t.join()
