# API Reference

> 📚 **Full documentation:** [https://gvarun01.github.io/task-mq/](https://gvarun01.github.io/task-mq/)

TaskMQ exposes a REST API for job management, monitoring, and health checks.

## Main Endpoints

### Add a Job
- **POST** `/add-job`
- **Auth:** admin
- **Body:** `{ "payload": ..., "handler": ... }`
- **Returns:** `{ "status": "ok", "job_id": ... }`

### Cancel a Job
- **POST** `/cancel`
- **Auth:** admin
- **Body:** `{ "job_id": ... }`

### Retry a Job
- **POST** `/retry`
- **Auth:** admin, worker
- **Body:** `{ "job_id": ... }`

### Metrics
- **GET** `/monitor/metrics`
- Prometheus metrics for jobs, failures, retries, durations

### Health
- **GET** `/health`
- Returns 200 if the API and DB are healthy

---

## Authentication
- All endpoints require a JWT token in the `Authorization: Bearer ...` header.
- See `users.json` for example users and roles.

## Handler Requirement
- The handler you specify must be registered and importable by the worker process.

## Python API Client Example

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

## Full API Docs

- Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) when running the API for interactive OpenAPI docs. 