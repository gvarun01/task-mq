import pytest
from click.testing import CliRunner
from taskmq.cli import cli
from taskmq.storage.sqlite_backend import SQLiteBackend
import threading
from taskmq.worker import Worker
from taskmq.jobs import handlers

@pytest.fixture
def backend():
    return SQLiteBackend()

def test_cli_add_job_and_worker(backend):
    handler_called_event = threading.Event()
    original_dummy_handler = handlers.HANDLERS["dummy"]
    
    def patched_dummy_handler(job):
        handler_called_event.set()
        return original_dummy_handler(job)
    
    handlers.HANDLERS["dummy"] = patched_dummy_handler
    try:
        runner = CliRunner()
        # Add a job with the persistent 'dummy' handler
        result = runner.invoke(cli, ["add-job", "--payload", '{"task": "cli test"}', "--handler", "dummy"])
        assert result.exit_code == 0
        assert "Inserted job with ID" in result.output
        # Now run the worker in a thread
        w = Worker(max_workers=1, backend=backend)
        t = threading.Thread(target=w.start)
        t.start()
        # Wait for the handler to be called or timeout
        handler_called_event.wait(timeout=5)
        w.stop()
        t.join()
        assert handler_called_event.is_set(), "Handler was not called"
    finally:
        handlers.HANDLERS["dummy"] = original_dummy_handler
