import pytest
from click.testing import CliRunner
from taskmq.cli import cli
from taskmq.storage.sqlite_backend import SQLiteBackend
import time
import threading
from taskmq.worker import Worker
from taskmq.jobs.handlers import register_handler

handler_called_event = threading.Event()
handler_payload = {}

@register_handler("cli_test")
def cli_test_handler(job):
    handler_payload['job'] = job.payload
    handler_called_event.set()

@pytest.fixture
def backend():
    return SQLiteBackend()

def test_cli_add_job_and_worker(backend):
    runner = CliRunner()
    # Add a job with the cli_test handler
    result = runner.invoke(cli, ["add-job", "--payload", '{"task": "cli test"}', "--handler", "cli_test"])
    assert result.exit_code == 0
    assert "Inserted job with ID" in result.output
    # Now run the worker in a thread
    w = Worker(max_workers=1, backend=backend)
    t = threading.Thread(target=w.start)
    t.start()
    # Wait for handler to be called or timeout
    handler_called_event.wait(timeout=5)
    w.stop()
    t.join()
    assert handler_called_event.is_set(), "Handler was not called"
    assert handler_payload['job'] == '{"task": "cli test"}'
