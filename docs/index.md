# TaskMQ Documentation

[![PyPI version](https://img.shields.io/pypi/v/task-mq.svg)](https://pypi.org/project/task-mq/)
[![CI](https://github.com/gvarun01/task-mq/actions/workflows/ci.yml/badge.svg)](https://github.com/gvarun01/task-mq/actions)

**TaskMQ** is a modern, developer-friendly Python task queue and job processing framework for background jobs, automation, and scalable systems.

## Features

- Simple CLI and REST API for job management
- Decorator-based custom handler registration
- Pluggable storage backends (SQLite, Redis)
- Configurable retry policies and job scheduling
- JWT authentication and Prometheus metrics
- Full async handler support

## Documentation

| Guide | Description |
|-------|-------------|
| [Quick Start](quickstart.md) | Get up and running in 5 minutes |
| [Usage Guide](usage.md) | Detailed CLI and library usage |
| [Writing Handlers](handlers.md) | Create custom job handlers |
| [API Reference](api.md) | REST API endpoints and authentication |
| [Contributing](contributing.md) | Development setup and guidelines |

## Installation

```bash
pip install task-mq

# With Redis support
pip install task-mq[redis]
```

## Quick Example

```python
from taskmq.jobs.handlers import register_handler
from taskmq.worker import Worker
from taskmq.storage.sqlite_backend import SQLiteBackend

@register_handler("greet")
def greet_handler(job):
    name = job.payload.get("name", "World")
    return f"Hello, {name}!"

backend = SQLiteBackend()
backend.insert_job('{"name": "TaskMQ"}', handler="greet")

worker = Worker(max_workers=1, backend=backend)
worker.start()
```

## Links

- [GitHub Repository](https://github.com/gvarun01/task-mq)
- [PyPI Package](https://pypi.org/project/task-mq/)
- [Issue Tracker](https://github.com/gvarun01/task-mq/issues)

---

**Author:** [Varun Gupta](https://github.com/gvarun01)
