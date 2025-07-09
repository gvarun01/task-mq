# TaskMQ

**TaskMQ** is a modern, developer-friendly Python task queue and job processing framework. It helps you run background jobs, automate workflows, and build scalable systems with ease.

- 🚀 Simple CLI and API for adding and running jobs
- 🧩 Register custom Python handlers for any task
- 🔐 Secure, observable, and production-ready
- 📦 Pluggable storage backends (SQLite, Redis stub)
- 🧪 Full test suite and CI

---

## Get Started

- [Quickstart](quickstart.md)
- [Usage Guide](usage.md)
- [Writing Handlers](handlers.md)
- [API Reference](api.md)
- [Contributing](contributing.md)

---

TaskMQ is open source and built for real-world developer needs. [View on GitHub](https://github.com/gvarun01/task-mq)

---

**Author:** Varun Gupta ([gvarun01](https://github.com/gvarun01))

---

This error means that `pytest` is **not installed** in your GitHub Actions environment, even though your workflow tries to run it.

### **Why?**
- Your workflow runs:  
  `pip install .[test]`
- But your `pyproject.toml` (and/or `setup.py`) does **not** define a `test` extra, so `pytest` is not installed.

---

## **How to Fix**

### 1. **Add test dependencies to `pyproject.toml`**

Add this section to your `pyproject.toml`:
```toml
[project.optional-dependencies]
test = [
    "pytest",
    "httpx"
]
```
Add any other test dependencies you use (e.g., `pytest-cov`, etc.).

---

### 2. **(Optional) Add to `setup.py` for legacy support**
If you want to support `pip install .[test]` for both modern and legacy setups, add:
```python
extras_require={
    "test": [
        "pytest",
        "httpx"
    ]
}
```
to your `setup()` call in `setup.py`.

---

### 3. **Commit and Push**
- Commit the changes to `pyproject.toml` (and `setup.py` if you add it).
- Push to GitHub.
- Your CI will now install `pytest` and the error will be resolved.

---

## **Summary Table**

| Step                | Action Needed? | Notes                                  |
|---------------------|---------------|----------------------------------------|
| Add test extra      | ✅            | In `pyproject.toml`                    |
| CI test step        | ✅            | Will work after above fix              |
| Code change         | ✅            | Required in config, not in workflow    |

---

**Would you like me to make this change to your `pyproject.toml` now?**
