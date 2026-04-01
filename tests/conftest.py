import pytest
import os
import uuid
from taskmq.storage.sqlite_backend import SQLiteBackend

# Check if Redis is available
redis_url = os.getenv("TASKMQ_REDIS_URL", "redis://localhost:6379/0")
redis_available = False
RedisBackend = None
try:
    import redis
    from taskmq.storage.redis_backend import RedisBackend
    r = redis.from_url(redis_url)
    r.ping()
    redis_available = True
except Exception:
    pass

@pytest.fixture(params=["sqlite", "redis"])
def backend(request):
    if request.param == "sqlite":
        db_path = f"test_taskmq_{uuid.uuid4()}.db"
        backend = SQLiteBackend(db_path=db_path)
        yield backend
        if os.path.exists(db_path):
            os.remove(db_path)
    elif request.param == "redis":
        if not redis_available:
            pytest.skip("Redis not available")
        backend = RedisBackend(redis_url=redis_url)
        # Use a unique prefix for tests to avoid collisions
        backend.prefix = f"test_taskmq:{uuid.uuid4()}:"
        yield backend
        # Cleanup
        keys = backend.redis.keys(f"{backend.prefix}*")
        if keys:
            backend.redis.delete(*keys)

@pytest.fixture
def sqlite_backend():
    db_path = f"test_taskmq_{uuid.uuid4()}.db"
    backend = SQLiteBackend(db_path=db_path)
    yield backend
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture
def redis_backend():
    if not redis_available:
        pytest.skip("Redis not available")
    backend = RedisBackend(redis_url=redis_url)
    backend.prefix = f"test_taskmq:{uuid.uuid4()}:"
    yield backend
    keys = backend.redis.keys(f"{backend.prefix}*")
    if keys:
        backend.redis.delete(*keys)
