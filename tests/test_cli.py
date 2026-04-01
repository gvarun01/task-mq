import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from taskmq.cli import cli
from taskmq.storage.base import Job, JobStatus
from datetime import datetime, UTC
import json

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_backend():
    with patch("taskmq.cli.get_backend") as mock:
        backend_instance = MagicMock()
        mock.return_value = backend_instance
        yield backend_instance

def test_add_job(runner, mock_backend):
    mock_backend.insert_job.return_value = 100
    
    result = runner.invoke(cli, ['add-job', '--payload', '{"task": "cli"}', '--handler', 'test'])
    
    assert result.exit_code == 0
    assert "Inserted job with ID: 100" in result.output
    mock_backend.insert_job.assert_called_once()

def test_get_job(runner, mock_backend):
    job = Job(
        id=100,
        status=JobStatus.SUCCESS,
        payload={"task": "cli"},
        created_at=datetime.now(UTC),
        result="CLI Result"
    )
    mock_backend.get_job.return_value = job
    
    result = runner.invoke(cli, ['get-job', '100'])
    
    assert result.exit_code == 0
    assert "Job ID: 100" in result.output
    assert "Result: CLI Result" in result.output

def test_run_worker(runner):
    # This is harder to test because it starts a loop.
    # We can mock Worker class.
    with patch("taskmq.cli.worker.Worker") as MockWorker:
        worker_instance = MockWorker.return_value
        
        # We need to interrupt the worker, but run_worker catches KeyboardInterrupt
        # So we can just let it run start() and verify it was called.
        # But start() blocks.
        # We can make start() raise KeyboardInterrupt immediately.
        worker_instance.start.side_effect = KeyboardInterrupt
        
        result = runner.invoke(cli, ['run-worker', '--max-workers', '2'])
        
        assert result.exit_code == 0
        assert "Starting worker pool" in result.output
        assert "Stopping worker..." in result.output
        MockWorker.assert_called_with(max_workers=2)
        worker_instance.start.assert_called_once()
        worker_instance.stop.assert_called_once()
