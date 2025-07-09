# Writing Handlers

> 📚 **Full documentation:** [https://gvarun01.github.io/task-mq/](https://gvarun01.github.io/task-mq/)

TaskMQ lets you register custom Python functions as job handlers. This makes it easy to add your own business logic for any job type.

## Registering a Handler

In any Python file that will be imported before starting the worker:

```python
from taskmq.jobs.handlers import register_handler

@register_handler("mytask")
def my_handler(job):
    print(f"Processing job {job.id} with payload: {job.payload}")
```

## Handler Discovery & Best Practices

- Handlers must be registered (imported) before starting workers.
- If you define handlers in your own module, import them before running the worker or API.
- Keep handlers small and focused.
- Use the handler registry for modular, testable code.
- You can register as many handlers as you like!

## Using a Handler

Add a job with your handler:

```bash
taskmq add-job --payload '{"task": "do something"}' --handler mytask
```

## Python Library Usage Example

```python
from taskmq.jobs.handlers import register_handler
from taskmq.worker import Worker
from taskmq.storage.sqlite_backend import SQLiteBackend

@register_handler("mytask")
def my_handler(job):
    print("Processing:", job.payload)

backend = SQLiteBackend()
backend.insert_job('{"task": "from script"}', handler="mytask")

worker = Worker(max_workers=1, backend=backend)
worker.start()
```

## Handler Arguments

- The handler receives a `job` object with:
  - `job.id`: Job ID
  - `job.payload`: The payload (as a string or dict)
  - `job.status`, `job.retries`, etc.

## Example: Dummy Handler

A simple handler is already registered for testing:

```python
@register_handler("dummy")
def dummy_handler(job):
    print(f"[DUMMY HANDLER] Executed for job {job.id} with payload: {job.payload}")
``` 