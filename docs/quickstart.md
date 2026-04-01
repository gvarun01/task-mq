# Quick Start

Get TaskMQ running in under 5 minutes.

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

```bash
pip install task-mq
```

For Redis support:

```bash
pip install task-mq[redis]
```

## Step 1: Start a Worker

Open a terminal and start a worker process:

```bash
taskmq run-worker --max-workers 1
```

You should see:

```
Starting worker pool with 1 worker(s) using sqlite backend... Press Ctrl+C to stop.
```

## Step 2: Add a Job

Open another terminal and add a job:

```bash
taskmq add-job --payload '{"message": "Hello, World!"}' --handler dummy
```

Output:

```
Inserted job with ID: 1, handler: dummy, priority: 0, payload: {'message': 'Hello, World!'}
```

## Step 3: Check Job Status

```bash
taskmq get-job 1
```

Output:

```
Job ID: 1
Status: success
Priority: 0
Payload: {"message": "Hello, World!"}
Result: {'executed': True, 'job_id': 1}
Retries: 0
```

## Step 4: Start the API Server

```bash
taskmq serve-api
```

Visit http://127.0.0.1:8000/docs for interactive API documentation.

## Using Redis Backend

For production workloads, use Redis:

```bash
# Start worker with Redis
taskmq --backend redis --redis-url redis://localhost:6379/0 run-worker

# Add job with Redis
taskmq --backend redis --redis-url redis://localhost:6379/0 add-job --payload '{"task": "test"}' --handler dummy
```

## Running Tests

```bash
pip install task-mq[dev]
pytest -v
```

## Next Steps

- [Usage Guide](usage.md) - Learn about all CLI commands and options
- [Writing Handlers](handlers.md) - Create custom job handlers
- [API Reference](api.md) - Use the REST API
