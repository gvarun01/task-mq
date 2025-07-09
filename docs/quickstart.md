# Quickstart

> 📚 **Full documentation:** [https://gvarun01.github.io/task-mq/](https://gvarun01.github.io/task-mq/)

## 1. Install

From PyPI (recommended):
```bash
pip install task-mq
```

Or from source (for development):
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## 2. Add a Job

```bash
taskmq add-job --payload '{"task": "hello world"}' --handler dummy
```

## 3. Run a Worker

```bash
taskmq run-worker --max-workers 1
```

## 4. Serve the API

```bash
taskmq serve-api
```

Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the interactive API docs.

## 5. Run Tests

```bash
pytest -v
``` 