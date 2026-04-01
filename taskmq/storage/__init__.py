import os
from taskmq.storage.sqlite_backend import SQLiteBackend

def get_backend():
    backend_type = os.getenv("TASKMQ_BACKEND", "sqlite")
    if backend_type == "redis":
        try:
            from taskmq.storage.redis_backend import RedisBackend
        except ImportError:
            raise ImportError("Redis backend requires 'redis' package. Install it with 'pip install task-mq[redis]'")
        
        redis_url = os.getenv("TASKMQ_REDIS_URL", "redis://localhost:6379/0")
        return RedisBackend(redis_url=redis_url)
    else:
        return SQLiteBackend()
