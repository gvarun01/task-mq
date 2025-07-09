import pytest
from taskmq.storage.sqlite_backend import SQLiteBackend
from taskmq.storage.base import JobStatus

@pytest.fixture
def backend():
    return SQLiteBackend()

def test_insert_and_fetch_job(backend):
    job_id = backend.insert_job('{"task": "storage test"}', handler="dummy")
    job = backend.get_job(job_id)
    assert job is not None
    assert job.id == job_id
    assert job.status == JobStatus.PENDING
    assert job.handler == "dummy"

def test_update_status(backend):
    job_id = backend.insert_job('{"task": "update test"}', handler="dummy")
    backend.update_status(job_id, JobStatus.SUCCESS, retries=1, error_log="done")
    job = backend.get_job(job_id)
    assert job.status == JobStatus.SUCCESS
    assert job.retries == 1
    assert job.error_log == "done"
