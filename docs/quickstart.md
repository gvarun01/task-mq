# Quickstart

## 1. Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## 2. Add a Job

```bash
task-mq add-job --payload '{"task": "hello world"}' --handler dummy
```

## 3. Run a Worker

```bash
task-mq run-worker --max-workers 1
```

## 4. Serve the API

```bash
task-mq serve-api
```

Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the interactive API docs.

## 5. Run Tests

```bash
PYTHONPATH=. pytest -v
``` 