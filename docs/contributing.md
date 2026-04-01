# Contributing

Thank you for your interest in contributing to TaskMQ! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Redis (optional, for running Redis tests)

### Clone and Install

```bash
git clone https://github.com/gvarun01/task-mq.git
cd task-mq

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Run tests
pytest -v

# Run linting
ruff check taskmq tests

# Run type checking
mypy taskmq
```

## Project Structure

```
task-mq/
├── taskmq/                 # Main package
│   ├── __init__.py
│   ├── cli.py              # CLI commands
│   ├── api_server.py       # FastAPI application
│   ├── worker.py           # Job processing worker
│   ├── jobs/
│   │   └── handlers.py     # Handler registry
│   └── storage/
│       ├── base.py         # Abstract backend interface
│       ├── sqlite_backend.py
│       └── redis_backend.py
├── tests/                  # Test suite
├── docs/                   # Documentation
├── pyproject.toml          # Project configuration
└── README.md
```

## Running Tests

### All Tests

```bash
pytest -v
```

### Specific Test File

```bash
pytest tests/test_worker.py -v
```

### With Coverage

```bash
pytest --cov=taskmq --cov-report=html
# Open htmlcov/index.html in browser
```

### Redis Tests

Redis tests require a running Redis instance:

```bash
# Start Redis (Docker)
docker run -d -p 6379:6379 redis:latest

# Run all tests including Redis
TASKMQ_REDIS_URL=redis://localhost:6379/0 pytest -v
```

## Code Style

TaskMQ uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

### Check for Issues

```bash
ruff check taskmq tests
```

### Auto-fix Issues

```bash
ruff check --fix taskmq tests
```

### Format Code

```bash
ruff format taskmq tests
```

### Type Checking

```bash
mypy taskmq
```

## Writing Code

### Style Guidelines

- Follow PEP 8 conventions
- Use type hints for function signatures
- Write Google-style docstrings for public functions
- Keep functions focused and small
- Prefer explicit over implicit

### Example Function

```python
from __future__ import annotations

from typing import Optional


def process_item(
    item_id: int,
    options: Optional[dict] = None
) -> dict:
    """Process a single item with the given options.
    
    Args:
        item_id: The unique identifier for the item.
        options: Optional processing options.
        
    Returns:
        A dict containing the processing result with keys:
        - 'status': Either 'success' or 'failed'
        - 'item_id': The processed item ID
        
    Raises:
        ValueError: If item_id is negative.
    """
    if item_id < 0:
        raise ValueError("item_id must be non-negative")
        
    options = options or {}
    # Processing logic here
    return {"status": "success", "item_id": item_id}
```

## Writing Tests

### Test Structure

```python
import pytest
from taskmq.storage.base import Job, JobStatus


class TestWorker:
    """Tests for the Worker class."""
    
    def test_processes_job_successfully(self, sqlite_backend):
        """Worker should process a job and update its status."""
        # Arrange
        job_id = sqlite_backend.insert_job('{"test": true}', handler="dummy")
        
        # Act
        # ... run worker ...
        
        # Assert
        job = sqlite_backend.get_job(job_id)
        assert job.status == JobStatus.SUCCESS
```

### Using Fixtures

TaskMQ provides test fixtures in `tests/conftest.py`:

- `sqlite_backend` - Isolated SQLite backend (cleaned up after test)
- `redis_backend` - Isolated Redis backend (skipped if Redis unavailable)
- `backend` - Parametrized fixture that runs tests with both backends

## Pull Request Process

### Before Submitting

1. **Fork the repository** and create a feature branch

2. **Write tests** for new functionality or bug fixes

3. **Run the test suite** and ensure all tests pass:
   ```bash
   pytest -v
   ```

4. **Run linting and type checking**:
   ```bash
   ruff check taskmq tests
   mypy taskmq
   ```

5. **Update documentation** if needed

### Submitting

1. Push your branch to your fork

2. Open a pull request against `main`

3. Fill out the PR template with:
   - Description of changes
   - Related issue (if any)
   - Testing performed

4. Wait for CI checks to pass

5. Address review feedback

### Commit Messages

Follow conventional commit format:

```
type: short description

Longer explanation if needed.

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or fixes
- `refactor`: Code refactoring
- `chore`: Build/tooling changes

## Building Documentation

Documentation is built with MkDocs:

```bash
# Install docs dependencies
pip install -e ".[docs]"

# Serve locally (with hot reload)
mkdocs serve

# Build static site
mkdocs build
```

## Reporting Issues

When reporting bugs, please include:

1. Python version (`python --version`)
2. TaskMQ version (`pip show task-mq`)
3. Operating system
4. Steps to reproduce
5. Expected vs actual behavior
6. Error messages or logs

## Getting Help

- [GitHub Issues](https://github.com/gvarun01/task-mq/issues) - Bug reports and feature requests
- [Discussions](https://github.com/gvarun01/task-mq/discussions) - Questions and general discussion

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
