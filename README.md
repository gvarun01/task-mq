# taskforge

[![CI](https://github.com/yourusername/taskforge/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/taskforge/actions)

A robust, extensible Python task queue with CLI, REST API, handler registry, authentication, monitoring, and pluggable storage backends.

---

## Features

- 🌀 **Task queue engine**: retries, scheduling, concurrency, periodic jobs
- 🖥️ **CLI**: `taskforge` for running workers, adding jobs, serving API
- 🔐 **Auth**: JWT-based authentication, role-based access
- 📦 **Storage**: SQLite backend (Redis stub included)
- 📊 **Monitoring**: Prometheus metrics
- 🧩 **Handler registry**: Register and dispatch custom job handlers
- 🧪 **Tests & CI**: Pytest suite, GitHub Actions workflow

---

## Quickstart

### 1. Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

### 2. CLI Usage

```bash
# Add a job
taskforge add-job --payload '{"task": "hello"}' --handler dummy

# Run the worker
taskforge run-worker --max-workers 2

# Serve the API
taskforge serve-api
```

### 3. API Usage

- Start the API: `taskforge serve-api`
- Add jobs, check health, and more via FastAPI endpoints (see `/docs` when running)

---

## Directory Structure

```
taskforge/
├── __init__.py
├── cli.py
├── worker.py
├── api_server.py
├── storage/
│   ├── __init__.py
│   ├── base.py
│   ├── sqlite_backend.py
│   └── redis_backend.py
├── utils/
│   └── heartbeat.py
├── jobs/
│   └── handlers.py
├── main.py
├── requirements.txt
├── users.json
├── README.md
└── ...
```

---

## Handler Registry Example

Register a handler in `taskforge/jobs/handlers.py`:

```python
from taskforge.jobs.handlers import register_handler

@register_handler("mytask")
def my_handler(job):
    print(f"Processing job {job.id} with payload: {job.payload}")
```

Add a job with this handler:

```bash
taskforge add-job --payload '{"task": "do something"}' --handler mytask
```

---

## Testing & CI

- Run all tests:
  ```bash
  pytest -v
  ```
- CI: GitHub Actions runs tests on every push/PR (see `.github/workflows/ci.yml`)

---

## Contributing

Pull requests and issues are welcome! Please add tests for new features and follow the existing code style.

---

## License

MIT License 