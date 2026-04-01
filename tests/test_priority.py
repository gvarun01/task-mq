import pytest
import time
import threading
from taskmq.worker import Worker
from taskmq.jobs import handlers
from taskmq.storage.base import JobStatus

def test_job_priority(backend):
    """
    Test that high priority jobs are processed before low priority jobs.
    """
    # We need to insert jobs and then start the worker.
    # To ensure order, we insert them, then start worker.
    
    processed_order = []
    event = threading.Event()
    
    @handlers.register_handler("priority_test")
    def priority_handler(job):
        processed_order.append(job.payload)
        if len(processed_order) == 3:
            event.set()

    # Insert Low, High, Normal
    # We use a slight delay to ensure created_at is different if backend sorts by that too
    # But our priority sort should override created_at
    
    backend.insert_job("low", handler="priority_test", priority=0)
    time.sleep(0.1)
    backend.insert_job("high", handler="priority_test", priority=20)
    time.sleep(0.1)
    backend.insert_job("normal", handler="priority_test", priority=10)
    
    w = Worker(max_workers=1, backend=backend, poll_interval=0.1)
    t = threading.Thread(target=w.start)
    t.start()
    
    try:
        if not event.wait(timeout=5):
            assert False, f"Timeout. Processed: {processed_order}"
        
        # Expected order: High, Normal, Low
        assert processed_order == ["high", "normal", "low"]
        
    finally:
        w.stop()
        t.join()
