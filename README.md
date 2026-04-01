# TaskMQ

[![PyPI version](https://img.shields.io/pypi/v/task-mq.svg)](https://pypi.org/project/task-mq/)
[![CI](https://github.com/gvarun01/task-mq/actions/workflows/ci.yml/badge.svg)](https://github.com/gvarun01/task-mq/actions)
[![Docs](https://img.shields.io/badge/docs-latest-blue.svg)](https://gvarun01.github.io/task-mq/)
[![Python Versions](https://img.shields.io/pypi/pyversions/task-mq.svg)](https://pypi.org/project/task-mq/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**TaskMQ** is a modern, developer-friendly Python task queue and job processing framework. It helps you run background jobs, automate workflows, and build scalable systems with ease.

**Key Features:**

- Simple CLI and REST API for adding and running jobs
- Decorator-based handler registration for custom task logic
- Multiple storage backends (SQLite for development, Redis for production)
- Retry policies with fixed, exponential backoff, or no-retry options
- Job scheduling for future execution and periodic/recurring jobs
- Dead Letter Queue (DLQ) for failed job inspection and replay
- JWT-based authentication for API security
- Prometheus metrics for monitoring and observability
- Graceful shutdown with in-flight job completion
- Full async handler support

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Python Library Usage](#python-library-usage)
- [CLI Reference](#cli-reference)
- [Advanced Features](#advanced-features)
- [API Usage](#api-usage)
- [Docker Deployment](#docker-deployment)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Requirements

- Python 3.8 or higher
- SQLite (included with Python) or Redis 4.0+ for production workloads

---

## Installation

### From PyPI (Recommended)

```bash
pip install task-mq

# With Redis support
pip install task-mq[redis]

# With development tools
pip install task-mq[dev]
```

### From Source

```bash
git clone https://github.com/gvarun01/task-mq.git
cd task-mq
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Quick Start

### 1. Start a Worker

```bash
taskmq run-worker --max-workers 2
```

### 2. Add a Job

```bash
taskmq add-job --payload '{"task": "hello"}' --handler dummy
```

### 3. Check Job Status

```bash
taskmq get-job 1
```

### 4. Start the REST API

```bash
taskmq serve-api
```

Visit http://127.0.0.1:8000/docs for interactive API documentation.

---

## Python Library Usage

TaskMQ can be used directly in Python applications:

```python
from taskmq.jobs.handlers import register_handler
from taskmq.worker import Worker
from taskmq.storage.sqlite_backend import SQLiteBackend

# Define a custom handler
@register_handler("email")
def send_email(job):
    """Process an email sending job."""
    payload = job.payload
    print(f"Sending email to {payload.get('to')}")
    return {"status": "sent", "to": payload.get("to")}

# Create backend and insert a job
backend = SQLiteBackend()
job_id = backend.insert_job(
    payload='{"to": "user@example.com", "subject": "Hello"}',
    handler="email"
)
print(f"Created job: {job_id}")

# Start the worker (blocks until stopped)
worker = Worker(max_workers=2, backend=backend)
worker.start()
```

**Important:** Handlers must be imported/registered before starting workers.

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `taskmq run-worker` | Start the worker pool to process jobs |
| `taskmq serve-api` | Start the REST API server |
| `taskmq add-job` | Add a new job to the queue |
| `taskmq get-job <id>` | Get job details and result |
| `taskmq inspect <id>` | View job execution timeline |
| `taskmq logs --job <id>` | Search structured job logs |
| `taskmq list-dead` | List jobs in the Dead Letter Queue |
| `taskmq replay <id>` | Replay any job |
| `taskmq replay-dead <id>` | Replay a job from the DLQ |

### Backend Selection

```bash
# Use SQLite (default)
taskmq run-worker

# Use Redis
taskmq --backend redis --redis-url redis://localhost:6379/0 run-worker
```

---

## Advanced Features

### Retry Policies

Configure how failed jobs are retried:

```python
# Fixed interval retries (default: 60 seconds between attempts)
backend.insert_job(payload, handler="mytask", retry_policy="fixed")

# Exponential backoff (doubles each retry)
backend.insert_job(payload, handler="mytask", retry_policy="exponential")

# No retries (move to DLQ on first failure)
backend.insert_job(payload, handler="mytask", retry_policy="none")
```

### Job Priority

Higher priority jobs are processed first:

```python
# Priority levels: 0 (Low), 10 (Normal), 20 (High)
backend.insert_job(payload, handler="urgent", priority=20)
```

### Scheduled Jobs

Execute jobs at a specific time:

```python
from datetime import datetime, timedelta, UTC

# Run 1 hour from now
future = datetime.now(UTC) + timedelta(hours=1)
backend.insert_job(payload, handler="mytask", scheduled_for=future)
```

### Periodic Jobs

Create recurring jobs:

```python
# Run every 300 seconds (5 minutes)
backend.insert_job(payload, handler="cleanup", interval_seconds=300)
```

### Async Handlers

TaskMQ supports async handlers natively:

```python
import asyncio
from taskmq.jobs.handlers import register_handler

@register_handler("async_task")
async def async_handler(job):
    await asyncio.sleep(1)
    return {"status": "completed"}
```

### Dead Letter Queue

Jobs that exhaust retries are moved to the DLQ for inspection:

```bash
# List failed jobs
taskmq list-dead

# Replay a failed job (resets retry count)
taskmq replay-dead 123
```

### Handler Versioning

Ensure replay uses the exact same handler code:

```bash
# Fails if handler code has changed since original execution
taskmq replay 123 --exact
```

### Graceful Shutdown

Workers handle SIGINT/SIGTERM gracefully, completing in-flight jobs before exiting:

```
^C
Received signal 2. Initiating graceful shutdown...
Waiting for 2 active jobs to complete...
```

### Job Inspection

View the complete execution timeline:

```bash
taskmq inspect 123
```

Output:
```
Job ID: 123
Status: SUCCESS
Handler: email
Payload: {'to': 'user@example.com'}
----------------------------------------
Execution Timeline:
[2026-03-15T10:00:00+00:00] Queued
[2026-03-15T10:00:01+00:00] Job started
[2026-03-15T10:00:02+00:00] Job finished successfully
```

---

## API Usage

### Authentication

All API endpoints require JWT authentication:

```python
import httpx

headers = {"Authorization": "Bearer <your_jwt_token>"}
```

### Add a Job

```python
response = httpx.post(
    "http://127.0.0.1:8000/add-job",
    json={"payload": {"task": "process"}, "handler": "mytask"},
    headers=headers
)
print(response.json())
# {"status": "ok", "job_id": 1}
```

### API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | None | Health check |
| `/add-job` | POST | admin | Add a new job |
| `/cancel` | POST | admin | Cancel a job |
| `/retry` | POST | admin/worker | Retry a failed job |
| `/monitor/metrics` | GET | None | Prometheus metrics |

See http://127.0.0.1:8000/docs for complete OpenAPI documentation.

---

## Docker Deployment

### Build and Run

```bash
docker build -t taskmq .
docker run --rm -p 8000:8000 taskmq serve-api
```

### Using Docker Compose

```bash
docker-compose up
```

This starts both the API server and a worker process.

---

## Documentation

- [Quick Start Guide](docs/quickstart.md)
- [Usage Guide](docs/usage.md)
- [Writing Handlers](docs/handlers.md)
- [API Reference](docs/api.md)
- [Contributing](docs/contributing.md)

Full documentation: https://gvarun01.github.io/task-mq/

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/contributing.md) for guidelines.

```bash
# Setup development environment
git clone https://github.com/gvarun01/task-mq.git
cd task-mq
pip install -e ".[dev]"

# Run tests
pytest -v

# Run linting
ruff check taskmq tests
```

---

## License

TaskMQ is released under the [MIT License](LICENSE).

---

**Author:** [Varun Gupta](https://github.com/gvarun01)
