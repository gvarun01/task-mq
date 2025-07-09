# Contributing

Thank you for your interest in contributing to TaskMQ!

## Setting Up for Development

1. **Clone the repo:**
   ```bash
   git clone https://github.com/gvarun01/task-mq.git
   cd task-mq
   ```
2. **Create a virtual environment:**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -e .[dev]
   ```
3. **Install test/dev dependencies:**
   ```bash
   pip install pytest mkdocs mkdocs-material
   ```

## Running Tests

```bash
PYTHONPATH=. pytest -v
```

## Building Docs

```bash
mkdocs serve
```

## Submitting Pull Requests

- Fork the repo and create a feature branch.
- Add tests for new features or bugfixes.
- Follow the existing code style (PEP8, docstrings).
- Open a pull request with a clear description.

## Code Style

- Use type hints and docstrings where possible.
- Keep handlers and CLI logic modular.
- Add comments for complex logic.

---

We welcome all contributions, bug reports, and feature requests! 