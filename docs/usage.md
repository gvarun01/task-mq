# Usage Guide

Complete guide to using TaskMQ via CLI and Python.

## CLI Commands

### Running Workers

Start worker processes to consume jobs from the queue:

```bash
# Single worker (default)
taskmq run-worker

# Multiple workers
taskmq run-worker --max-workers 4

# With Redis backend
taskmq --backend redis --redis-url redis://localhost:6379/0 run-worker
```

Workers automatically handle graceful shutdown on Ctrl+C (SIGINT) or SIGTERM.

### Managing Jobs

**Add a job:**

```bash
taskmq add-job --payload '{"data": "value"}' --handler mytask

# With priority (0=Low, 10=Normal, 20=High)
taskmq add-job --payload '{"urgent": true}' --handler mytask --priority 20
```

**Get job details:**

```bash
taskmq get-job 123
```

**Inspect job timeline:**

```bash
taskmq inspect 123
```

**Search job logs:**

```bash
# By job ID
taskmq logs --job 123

# By handler name
taskmq logs --handler mytask --limit 100
```

### Dead Letter Queue

Jobs that fail all retry attempts are moved to the DLQ:

```bash
# List dead jobs
taskmq list-dead --limit 20

# Replay a dead job (resets retry count)
taskmq replay-dead 123
```

### Job Replay

Replay any job to re-run with the same parameters:

```bash
# Basic replay
taskmq replay 123

# Exact replay (fails if handler code changed)
taskmq replay 123 --exact
```

### API Server

```bash
taskmq serve-api
```

The API server runs on http://127.0.0.1:8000 by default.

## Python Library Usage

### Basic Example

```python
from taskmq.jobs.handlers import register_handler
from taskmq.worker import Worker
from taskmq.storage.sqlite_backend import SQLiteBackend

# Register a handler
@register_handler("process_data")
def process_data(job):
    """Process incoming data."""
    data = job.payload
    result = {"processed": True, "input": data}
    return result

# Create backend and add job
backend = SQLiteBackend()
job_id = backend.insert_job(
    payload='{"values": [1, 2, 3]}',
    handler="process_data"
)

# Start worker
worker = Worker(max_workers=2, backend=backend)
worker.start()  # Blocks until stopped
```

### Using Redis Backend

```python
from taskmq.storage.redis_backend import RedisBackend

backend = RedisBackend(redis_url="redis://localhost:6379/0")
job_id = backend.insert_job(payload, handler="mytask")
```

### Job Options

```python
from datetime import datetime, timedelta, UTC

# With retry policy
backend.insert_job(
    payload='{"data": "test"}',
    handler="mytask",
    retry_policy="exponential"  # or "fixed", "none"
)

# With priority
backend.insert_job(
    payload='{"urgent": true}',
    handler="mytask",
    priority=20  # High priority
)

# Scheduled for future
future_time = datetime.now(UTC) + timedelta(hours=1)
backend.insert_job(
    payload='{"scheduled": true}',
    handler="mytask",
    scheduled_for=future_time
)

# Periodic job
backend.insert_job(
    payload='{"recurring": true}',
    handler="cleanup",
    interval_seconds=3600  # Every hour
)
```

### Worker Configuration

```python
worker = Worker(
    max_workers=4,          # Thread pool size
    backend=backend,        # Storage backend
    poll_interval=1.0,      # Seconds between queue checks
    max_retries=3,          # Max retry attempts
    lock_timeout=30         # Job lock timeout in seconds
)
```

## Handler Registration

Handlers must be registered before workers start. There are two approaches:

**1. Same module (simple scripts):**

```python
from taskmq.jobs.handlers import register_handler
from taskmq.worker import Worker

@register_handler("mytask")
def my_handler(job):
    return {"done": True}

worker = Worker()
worker.start()
```

**2. Separate module (recommended for larger projects):**

```python
# handlers.py
from taskmq.jobs.handlers import register_handler

@register_handler("email")
def send_email(job):
    # email logic
    pass

@register_handler("sms")
def send_sms(job):
    # sms logic
    pass
```

```python
# worker.py
import handlers  # Import to register handlers
from taskmq.worker import Worker

worker = Worker()
worker.start()
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TASKMQ_BACKEND` | Storage backend (`sqlite` or `redis`) | `sqlite` |
| `TASKMQ_REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `TASKMQ_JWT_SECRET` | JWT signing secret for API auth | (required for API) |

## Next Steps

- [Writing Handlers](handlers.md) - Advanced handler patterns
- [API Reference](api.md) - REST API documentation
