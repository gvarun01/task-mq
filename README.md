# TaskMQ

[![PyPI version](https://img.shields.io/pypi/v/task-mq.svg)](https://pypi.org/project/task-mq/)
[![CI](https://github.com/gvarun01/task-mq/actions/workflows/ci.yml/badge.svg)](https://github.com/gvarun01/task-mq/actions)

**TaskMQ** is a modern, developer-friendly Python task queue and job processing framework. It helps you run background jobs, automate workflows, and build scalable systems with ease.

- 🚀 Simple CLI and API for adding and running jobs
- 🧩 Register custom Python handlers for any task
- 🔐 Secure, observable, and production-ready
- 📦 Pluggable storage backends (SQLite, Redis stub)
- 🧪 Full test suite and CI

---

## Installation

### From PyPI (Recommended)

```bash
pip install task-mq
```

### From Source (for development)

```bash
git clone https://github.com/gvarun01/task-mq.git
cd task-mq
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

---

## Quickstart

### CLI Usage

Add a job:
```bash
taskmq add-job --payload '{"task": "hello world"}' --handler dummy
```

Run a worker:
```bash
taskmq run-worker --max-workers 1
```

Serve the API:
```bash
taskmq serve-api
```

### Python Library Usage

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

## Features

* **Task Queue Engine**: Retries, scheduling, periodic jobs, concurrent workers
* **CLI**: Add jobs, run workers, serve API
* **API**: RESTful endpoints, JWT auth, Prometheus metrics
* **Handler Registry**: Register custom Python functions for job types
* **Storage**: SQLite backend (default), Redis stub for future
* **Monitoring**: Prometheus metrics for jobs, queue, durations
* **Docker**: Dockerfile and docker-compose for easy deployment

---

## Handler Registration & Discovery

- Register handlers using `@register_handler("name")` in any imported module.
- **Important:** Handlers must be registered (imported) before starting workers.
- If you define handlers in your own module, import them before running the worker or API.

---

## Advanced Usage

### Scheduling & Periodic Jobs
- Schedule jobs for the future or set as periodic (see API/handler docs for details).
- Example:
  ```python
  backend.insert_job('{"task": "future"}', handler="mytask", scheduled_for=datetime.datetime(2024, 12, 31, 12, 0, 0))
  ```

### Retry Policies
- Supported: `fixed`, `exponential`, `none` (set per job)
- Example:
  ```python
  backend.insert_job('{"task": "retry"}', handler="mytask", retry_policy="fixed")
  ```

### Monitoring
- Prometheus metrics at `/monitor/metrics` (API) and via worker process

---

## Docker Usage

Build and run with Docker:
```bash
docker build -t taskmq .
docker run --rm -p 8000:8000 taskmq serve-api
```

Or use docker-compose:
```bash
docker-compose up
```

---

## API Usage Example (Python)

```python
import httpx

# Add a job via API (requires JWT token)
response = httpx.post(
    "http://127.0.0.1:8000/add-job",
    json={"payload": {"task": "api"}, "handler": "dummy"},
    headers={"Authorization": "Bearer <your_token>"}
)
print(response.json())
```

---

## Documentation

- [Quickstart](docs/quickstart.md)
- [Usage Guide](docs/usage.md)
- [Writing Handlers](docs/handlers.md)
- [API Reference](docs/api.md)
- [Full Docs (mkdocs)](docs/index.md)

---

## Contributing

Pull requests and issues are welcome! See [CONTRIBUTING.md](docs/contributing.md) for guidelines.

---

## License

MIT License. See [LICENSE](LICENSE).

---

**Author:** Varun Gupta ([gvarun01](https://github.com/gvarun01))
