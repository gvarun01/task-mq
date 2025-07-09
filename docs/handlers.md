# Writing Handlers

TaskMQ lets you register custom Python functions as job handlers. This makes it easy to add your own business logic for any job type.

## Registering a Handler

In `taskmq/jobs/handlers.py`:

```python
from taskmq.jobs.handlers import register_handler

@register_handler("mytask")
def my_handler(job):
    print(f"Processing job {job.id} with payload: {job.payload}")
```

## Using a Handler

Add a job with your handler:

```bash
task-mq add-job --payload '{"task": "do something"}' --handler mytask
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

## Best Practices

- Keep handlers small and focused.
- Use the handler registry for modular, testable code.
- You can register as many handlers as you like! 