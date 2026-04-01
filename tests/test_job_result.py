import pytest
import time
from taskmq.worker import Worker
from taskmq.jobs import handlers
import threading

def test_job_result_storage(backend):
    # Register a handler that returns a value
    # We need a unique name because handlers are global
    handler_name = f"return_value_{time.time()}"
    
    @handlers.register_handler(handler_name)
    def return_value_handler(job):
        return "Success Result"

    job_id = backend.insert_job('{"task": "result"}', handler=handler_name)
    
    w = Worker(max_workers=1, backend=backend)
    t = threading.Thread(target=w.start)
    t.start()
    
    # Wait for job to complete
    for _ in range(20):
        job = backend.get_job(job_id)
        if job and job.status.value == "SUCCESS":
            break
        time.sleep(0.2)
        
    w.stop()
    t.join()
    
    job = backend.get_job(job_id)
    assert job is not None
    assert job.status.value == "SUCCESS"
    assert job.result == "Success Result"
