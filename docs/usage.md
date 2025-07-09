# Usage Guide

## CLI Commands

- **Add a job:**
  ```bash
  task-mq add-job --payload '{"task": "do work"}' --handler dummy
  ```
- **Run workers:**
  ```bash
  task-mq run-worker --max-workers 2
  ```
- **Serve the API:**
  ```bash
  task-mq serve-api
  ```

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