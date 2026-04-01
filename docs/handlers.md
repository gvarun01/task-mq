# Writing Handlers

Handlers are Python functions that process jobs. This guide covers handler registration, patterns, and best practices.

## Basic Handler

Register a handler using the `@register_handler` decorator:

```python
from taskmq.jobs.handlers import register_handler

@register_handler("send_email")
def send_email(job):
    """Send an email based on job payload.
    
    Args:
        job: Job object with id, payload, status, and other attributes.
        
    Returns:
        A result dict that will be stored with the job.
    """
    payload = job.payload
    to = payload.get("to")
    subject = payload.get("subject")
    body = payload.get("body")
    
    # Your email sending logic here
    print(f"Sending email to {to}: {subject}")
    
    return {"status": "sent", "recipient": to}
```

## Job Object

The `job` parameter provides access to job data:

| Attribute | Type | Description |
|-----------|------|-------------|
| `job.id` | int | Unique job identifier |
| `job.payload` | dict/str | Job data (parsed JSON or string) |
| `job.status` | JobStatus | Current status (PENDING, RUNNING, etc.) |
| `job.handler` | str | Handler name |
| `job.priority` | int | Priority level (0, 10, 20) |
| `job.retries` | int | Number of retry attempts |
| `job.created_at` | datetime | When the job was created |
| `job.result` | str | Result from previous execution (if any) |
| `job.error_log` | str | Error message (if failed) |

## Async Handlers

TaskMQ supports async handlers natively:

```python
import asyncio
import httpx
from taskmq.jobs.handlers import register_handler

@register_handler("fetch_data")
async def fetch_data(job):
    """Fetch data from an external API."""
    url = job.payload.get("url")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
    
    return {"fetched": True, "data_size": len(data)}
```

## Handler Return Values

Handlers can return various types:

```python
@register_handler("example")
def example_handler(job):
    # Return a dict (recommended)
    return {"status": "success", "count": 42}
    
    # Return a string
    return "Task completed"
    
    # Return None (no result stored)
    return None
```

The return value is converted to a string and stored in `job.result`.

## Error Handling

Unhandled exceptions trigger the retry policy:

```python
@register_handler("risky_task")
def risky_task(job):
    """Task that might fail."""
    if some_condition:
        raise ValueError("Something went wrong")
    
    return {"status": "ok"}
```

For controlled failures without retry:

```python
@register_handler("validate")
def validate(job):
    """Validate data, fail fast on invalid input."""
    data = job.payload
    
    if not data.get("required_field"):
        # Log the error but don't raise (won't trigger retry)
        return {"status": "failed", "reason": "missing required_field"}
    
    return {"status": "valid"}
```

## Handler Patterns

### Processing with External Services

```python
import httpx
from taskmq.jobs.handlers import register_handler

@register_handler("webhook")
def send_webhook(job):
    """Send a webhook notification."""
    url = job.payload.get("url")
    data = job.payload.get("data")
    
    response = httpx.post(url, json=data, timeout=30)
    response.raise_for_status()
    
    return {
        "status_code": response.status_code,
        "delivered": True
    }
```

### Batch Processing

```python
@register_handler("batch_process")
def batch_process(job):
    """Process multiple items in a single job."""
    items = job.payload.get("items", [])
    results = []
    
    for item in items:
        result = process_item(item)
        results.append(result)
    
    return {
        "processed": len(results),
        "results": results
    }
```

### Chaining Jobs

```python
from taskmq.storage import get_backend

@register_handler("step1")
def step1(job):
    """First step, creates next job."""
    result = do_step1(job.payload)
    
    # Queue the next step
    backend = get_backend()
    backend.insert_job(
        payload=result,
        handler="step2"
    )
    
    return {"step": 1, "next_queued": True}

@register_handler("step2")
def step2(job):
    """Second step."""
    return {"step": 2, "complete": True}
```

## Best Practices

1. **Keep handlers focused** - One handler, one responsibility

2. **Make handlers idempotent** - Safe to run multiple times with same input

3. **Handle timeouts** - Set appropriate timeouts for external calls

4. **Return meaningful results** - Include status and relevant data

5. **Use structured payloads** - Prefer dicts over strings for payload

6. **Log important events** - Use Python logging for debugging

```python
import logging
from taskmq.jobs.handlers import register_handler

logger = logging.getLogger(__name__)

@register_handler("important_task")
def important_task(job):
    logger.info(f"Starting job {job.id}")
    
    try:
        result = do_work(job.payload)
        logger.info(f"Job {job.id} completed successfully")
        return result
    except Exception as e:
        logger.error(f"Job {job.id} failed: {e}")
        raise
```

## Handler Discovery

Handlers must be imported before workers start. Common patterns:

**Option 1: Import in worker script**

```python
# worker.py
import myapp.handlers  # Registers all handlers
from taskmq.worker import Worker

Worker().start()
```

**Option 2: Package __init__.py**

```python
# myapp/handlers/__init__.py
from .email import send_email
from .sms import send_sms
from .webhooks import send_webhook
```

**Option 3: Entry point registration** (advanced)

Define handlers as package entry points for automatic discovery.

## Testing Handlers

```python
import pytest
from taskmq.storage.base import Job, JobStatus
from myapp.handlers import send_email

def test_send_email():
    """Test email handler."""
    job = Job(
        id=1,
        payload={"to": "test@example.com", "subject": "Test"},
        status=JobStatus.RUNNING
    )
    
    result = send_email(job)
    
    assert result["status"] == "sent"
    assert result["recipient"] == "test@example.com"
```

## Next Steps

- [API Reference](api.md) - REST API documentation
- [Usage Guide](usage.md) - CLI and configuration options
