import pytest
import time
from taskmq.worker import Worker
from taskmq.storage.sqlite_backend import SQLiteBackend
from taskmq.jobs.handlers import HANDLERS, register_handler

@pytest.fixture
def backend():
    return SQLiteBackend()

def test_worker_processes_job(backend, capsys):
    job_id = backend.insert_job('{"task": "pytest"}', handler="dummy")
    w = Worker(max_workers=1, backend=backend)
    # Run worker in a thread for a short time
    import threading
    t = threading.Thread(target=w.start)
    t.start()
    time.sleep(2)
    w.stop()
    t.join()
    # Check output
    captured = capsys.readouterr()
    assert "[DUMMY HANDLER] Executed for job" in captured.out
