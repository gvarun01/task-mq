# API Reference

TaskMQ provides a REST API for job management, built with FastAPI.

## Starting the API Server

```bash
taskmq serve-api
```

The server starts at http://127.0.0.1:8000. Interactive documentation is available at:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Authentication

All endpoints (except `/health` and `/monitor/metrics`) require JWT authentication.

### Getting a Token

Generate a JWT token with your secret key:

```python
import jwt
from datetime import datetime, timedelta, UTC

secret = "your-secret-key"  # Same as TASKMQ_JWT_SECRET env var
payload = {
    "sub": "admin",
    "role": "admin",
    "exp": datetime.now(UTC) + timedelta(hours=24)
}
token = jwt.encode(payload, secret, algorithm="HS256")
print(token)
```

### Using the Token

Include the token in the `Authorization` header:

```bash
curl -X POST http://127.0.0.1:8000/add-job \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"payload": {"task": "test"}, "handler": "dummy"}'
```

### Roles

| Role | Permissions |
|------|-------------|
| `admin` | All operations (add, cancel, retry jobs) |
| `worker` | Retry jobs only |

## Endpoints

### Health Check

Check if the API and database are healthy.

```
GET /health
```

**Response:**

```json
{
  "status": "ok"
}
```

No authentication required.

---

### Add Job

Add a new job to the queue.

```
POST /add-job
```

**Request Body:**

```json
{
  "payload": {"key": "value"},
  "handler": "handler_name",
  "priority": 10,
  "retry_policy": "fixed",
  "scheduled_for": "2026-04-01T12:00:00Z",
  "interval_seconds": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `payload` | object | Yes | Job data |
| `handler` | string | Yes | Handler name |
| `priority` | int | No | 0 (Low), 10 (Normal), 20 (High). Default: 0 |
| `retry_policy` | string | No | `fixed`, `exponential`, or `none`. Default: `fixed` |
| `scheduled_for` | string | No | ISO 8601 datetime for delayed execution |
| `interval_seconds` | int | No | Repeat interval for periodic jobs |

**Response:**

```json
{
  "status": "ok",
  "job_id": 123
}
```

**Auth:** admin

---

### Cancel Job

Cancel a pending job.

```
POST /cancel
```

**Request Body:**

```json
{
  "job_id": 123
}
```

**Response:**

```json
{
  "status": "cancelled",
  "job_id": 123
}
```

**Auth:** admin

**Note:** Only pending jobs can be cancelled. Running jobs complete normally.

---

### Retry Job

Retry a failed job.

```
POST /retry
```

**Request Body:**

```json
{
  "job_id": 123
}
```

**Response:**

```json
{
  "status": "retrying",
  "job_id": 123
}
```

**Auth:** admin, worker

---

### Metrics

Prometheus-formatted metrics for monitoring.

```
GET /monitor/metrics
```

**Response:**

```
# HELP taskmq_jobs_total Total number of jobs processed
# TYPE taskmq_jobs_total counter
taskmq_jobs_total{status="success"} 150
taskmq_jobs_total{status="failed"} 5

# HELP taskmq_job_duration_seconds Job processing duration
# TYPE taskmq_job_duration_seconds histogram
taskmq_job_duration_seconds_bucket{le="0.1"} 50
...
```

No authentication required.

---

## Python Client Examples

### Using httpx

```python
import httpx

BASE_URL = "http://127.0.0.1:8000"
TOKEN = "your-jwt-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Add a job
response = httpx.post(
    f"{BASE_URL}/add-job",
    json={"payload": {"task": "process"}, "handler": "mytask"},
    headers=HEADERS
)
job_id = response.json()["job_id"]
print(f"Created job: {job_id}")

# Cancel a job
response = httpx.post(
    f"{BASE_URL}/cancel",
    json={"job_id": job_id},
    headers=HEADERS
)
print(response.json())
```

### Using requests

```python
import requests

BASE_URL = "http://127.0.0.1:8000"
TOKEN = "your-jwt-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Add a scheduled job
from datetime import datetime, timedelta, UTC

future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
response = requests.post(
    f"{BASE_URL}/add-job",
    json={
        "payload": {"scheduled": True},
        "handler": "mytask",
        "scheduled_for": future
    },
    headers=HEADERS
)
print(response.json())
```

### Async Client

```python
import asyncio
import httpx

async def add_jobs():
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": "Bearer your-token"}
        
        tasks = []
        for i in range(10):
            task = client.post(
                "http://127.0.0.1:8000/add-job",
                json={"payload": {"index": i}, "handler": "batch"},
                headers=headers
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        for r in responses:
            print(r.json())

asyncio.run(add_jobs())
```

## Error Responses

### 401 Unauthorized

```json
{
  "detail": "Invalid or missing token"
}
```

### 403 Forbidden

```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found

```json
{
  "detail": "Job not found"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "handler"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TASKMQ_JWT_SECRET` | Secret key for JWT signing | Yes |
| `TASKMQ_BACKEND` | Storage backend (`sqlite` or `redis`) | No |
| `TASKMQ_REDIS_URL` | Redis connection URL | If using Redis |

### Example Setup

```bash
export TASKMQ_JWT_SECRET="your-secure-secret-key"
export TASKMQ_BACKEND="redis"
export TASKMQ_REDIS_URL="redis://localhost:6379/0"

taskmq serve-api
```

## Next Steps

- [Writing Handlers](handlers.md) - Create custom job handlers
- [Usage Guide](usage.md) - CLI commands and Python usage
