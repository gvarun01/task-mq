# Usage Guide

> 📚 **Full documentation:** [https://gvarun01.github.io/task-mq/](https://gvarun01.github.io/task-mq/)

## CLI Commands

- **Add a job:**
  ```bash
  taskmq add-job --payload '{"task": "do work"}' --handler dummy
  ```
- **Run workers:**
  ```bash
  taskmq run-worker --max-workers 2
  ```
- **Serve the API:**
  ```bash
  taskmq serve-api
  ```

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

## Handler Registration & Discovery

- Register handlers using `@register_handler("name")` in any imported module.
- **Important:** Handlers must be registered (imported) before starting workers.
- If you define handlers in your own module, import them before running the worker or API.

## API Endpoints

- **Add a job:** `POST /add-job` (admin only)
- **Cancel a job:** `POST /cancel` (admin only)
- **Retry a job:** `POST /retry` (admin/worker)
- **Metrics:** `GET /monitor/metrics`
- **Health:** `GET /health`

See [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for full OpenAPI docs.

## Job Scheduling

- Jobs can be scheduled for the future or set as periodic (see API/handler docs for details).
- Retry policies: `fixed`, `exponential`, `none` (set per job).

## Authentication

- All API endpoints require a JWT token.
- Roles: `admin`, `worker` (see `users.json` for example users).
- Pass the token in the `Authorization: Bearer ...` header. 