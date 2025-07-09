import pytest
import time
from taskmq.worker import Worker
from taskmq.storage.sqlite_backend import SQLiteBackend
from taskmq.jobs import handlers
import threading

@pytest.fixture
def backend():
    return SQLiteBackend()

def test_worker_processes_job(backend):
    handler_called_event = threading.Event()
    original_dummy_handler = handlers.HANDLERS["dummy"]

    def patched_dummy_handler(job):
        handler_called_event.set()
        return original_dummy_handler(job)

    handlers.HANDLERS["dummy"] = patched_dummy_handler
    try:
        job_id = backend.insert_job('{"task": "pytest"}', handler="dummy")
        w = Worker(max_workers=1, backend=backend)
        # Run worker in a thread for a short time
        t = threading.Thread(target=w.start)
        t.start()
        handler_called_event.wait(timeout=5)
        w.stop()
        t.join()
        assert handler_called_event.is_set(), "Handler was not called"
    finally:
        handlers.HANDLERS["dummy"] = original_dummy_handler
