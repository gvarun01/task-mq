import pytest
import time
import threading
from taskmq.worker import Worker
from taskmq.jobs import handlers
from taskmq.storage.base import JobStatus
import hashlib

# Define a handler
@handlers.register_handler("replay_test")
def replay_handler(job):
    return "original"

def test_replay_exact(backend):
    """
    Test exact replay functionality.
    """
    # 1. Run a job to establish history
    job_id = backend.insert_job("payload", handler="replay_test")
    
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
        assert job.handler_hash is not None
        original_hash = job.handler_hash
        
        # 2. Verify current hash matches
        current_hash = handlers.get_handler_hash("replay_test")
        assert current_hash == original_hash
        
        # 3. Simulate "Exact Replay" logic (like CLI)
        # Case A: Match
        if current_hash == job.handler_hash:
            new_id = backend.insert_job(job.payload, handler=job.handler)
            assert new_id is not None
            
        # Case B: Mismatch (Simulate code change)
        # We manually change the hash in the registry to simulate a change
        handlers.HANDLER_HASHES["replay_test"] = "different_hash"
        
        current_hash_new = handlers.get_handler_hash("replay_test")
        assert current_hash_new != job.handler_hash
        
        # This should fail the check
        check_passed = False
        if current_hash_new == job.handler_hash:
            check_passed = True
        assert not check_passed
        
    finally:
        w.stop()
        t.join()
        # Restore hash
        handlers.register_handler("replay_test")(replay_handler)
