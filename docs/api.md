# API Reference

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

---

## Full API Docs

- Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) when running the API for interactive OpenAPI docs. 