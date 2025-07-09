# TaskMQ

[![PyPI version](https://img.shields.io/pypi/v/task-mq.svg)](https://pypi.org/project/task-mq/)
[![CI](https://github.com/gvarun01/task-mq/actions/workflows/ci.yml/badge.svg)](https://github.com/gvarun01/task-mq/actions)

**TaskMQ** is a modern, developer-friendly Python task queue and job processing framework for background jobs, automation, and scalable systems.

- 🚀 Simple CLI and API for adding and running jobs
- 🧩 Register custom Python handlers for any task
- 🔐 Secure, observable, and production-ready
- 📦 Pluggable storage backends (SQLite, Redis stub)
- 🧪 Full test suite and CI

---

## 📚 Documentation

- **Full documentation:** [https://gvarun01.github.io/task-mq/](https://gvarun01.github.io/task-mq/)
- [Quickstart](quickstart.md)
- [Usage Guide](usage.md)
- [Writing Handlers](handlers.md)
- [API Reference](api.md)

---

## Getting Started

### Install from PyPI

```bash
pip install task-mq
```

### Or install from source (for development)

```bash
git clone https://github.com/gvarun01/task-mq.git
cd task-mq
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

---

## Python Library Usage

You can use TaskMQ directly in your own Python scripts:

```python
from taskmq.jobs.handlers import register_handler
from taskmq.worker import Worker
from taskmq.storage.sqlite_backend import SQLiteBackend

@register_handler("mytask")
def my_handler(job):
    print("Processing:", job.payload)

backend = SQLiteBackend()
job_id = backend.insert_job('{"task": "from script"}', handler="mytask")

worker = Worker(max_workers=1, backend=backend)
worker.start()
```

---

TaskMQ is open source and built for real-world developer needs. [View on GitHub](https://github.com/gvarun01/task-mq)

**Author:** Varun Gupta ([gvarun01](https://github.com/gvarun01))