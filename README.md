# TaskForge

[![CI](https://github.com/yourusername/taskmq/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/taskmq/actions)

TaskForge is a Python-based task queue system designed for robust and extensible background job processing. It features a command-line interface (CLI) for managing workers and jobs, a RESTful API for programmatic interaction, a flexible job handler registry, JWT-based authentication, Prometheus monitoring, and uses SQLite as its default storage backend.

## Features

*   🌀 **Task Queue Engine**:
    *   Supports job retries with configurable policies (none, fixed, exponential).
    *   Allows scheduling of jobs for future execution.
    *   Enables periodic job execution at defined intervals.
    *   Concurrent task processing using a thread pool for workers.
*   🖥️ **Command-Line Interface (CLI)**: Powered by Click, the `taskmq` CLI allows you to:
    *   Run worker processes (`run-worker`).
    *   Add new jobs to the queue (`add-job`).
    *   Start the API server (`serve-api`).
*   🔐 **Authentication**:
    *   Secure API endpoints using JSON Web Tokens (JWT).
    *   Role-based access control for API operations (roles defined in `users.json`).
*   📦 **Storage**:
    *   **SQLite Backend**: Default, fully implemented job storage using SQLite.
    *   **Redis Backend**: A stub (`redis_backend.py`) is present, indicating potential for future Redis support, but it is not currently implemented.
*   📊 **Monitoring**:
    *   Exposes Prometheus metrics from both the API server and workers for observing queue depth, job statuses, task durations, and more.
    *   API metrics available at the `/monitor/metrics` endpoint when the API server is running.
*   🧩 **Handler Registry**:
    *   Dynamically register custom Python functions to handle specific job types.
    *   Jobs can be dispatched to their registered handlers by name.
*   🐳 **Containerization**:
    *   Includes a `Dockerfile` for building a container image for the application.
    *   A `docker-compose.yml` file is provided with the intent to orchestrate API and worker services. (Note: Users should review and potentially update the Docker Compose configuration to ensure it aligns with the current application structure and commands, particularly regarding module paths, database file paths, and CLI commands used.)

## Tech Stack

*   **Language**: Python (>=3.8)
*   **API Framework**: FastAPI
*   **CLI Framework**: Click
*   **Authentication**: JSON Web Tokens (JWT) via PyJWT/Python-JOSE
*   **Default Database**: SQLite (using Python's built-in `sqlite3` module)
*   **Monitoring**: Prometheus (via `prometheus-client`)
*   **HTTP Client (for tests/internal use)**: HTTPX

## Prerequisites

*   Python 3.8 or newer.
*   `pip` for installing Python packages.

## Installation

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd taskmq
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```

3.  **Install the package and its dependencies:**
    ```bash
    pip install -e .
    ```

## Running the Application

### 1. Initialize the Database
The SQLite database (`taskmq.db`) will be automatically created in the root directory when the application first tries to access it (e.g., when adding a job or starting a worker).

### 2. Run the Worker
To start a worker process that consumes jobs from the queue:
```bash
taskmq run-worker --max-workers 2 # Example with 2 concurrent worker threads
```
The worker will look for jobs in the `taskmq.db` SQLite database.

### 3. Serve the API
To start the FastAPI server:
```bash
taskmq serve-api
```
The API server will be available at `http://127.0.0.1:8000`.
*   API documentation (Swagger UI) can be accessed at `http://127.0.0.1:8000/docs`.
*   Prometheus metrics are exposed at `http://127.0.0.1:8000/monitor/metrics`.

### 4. Add a Job (via CLI)
To add a new job to the queue:
```bash
taskmq add-job --payload '{"message": "Hello from CLI"}' --handler dummy
```
This adds a job with the specified JSON payload, to be processed by the "dummy" handler. The `dummy` handler is pre-registered for testing and prints the job details.

## Usage Examples

### CLI

*   **Add a job with a specific handler:**
    ```bash
    taskmq add-job --payload '{"data": "important_task"}' --handler my_custom_handler
    ```

*   **Run a worker with a specific number of threads:**
    ```bash
    taskmq run-worker --max-workers 4
    ```

*   **Start the API server (default port 8000):**
    ```bash
    taskmq serve-api
    ```

### API
Once the API server is running (`taskmq serve-api`), you can interact with it using any HTTP client (e.g., `curl`, Postman, or `httpx` in Python).

*   **Login (to obtain a JWT token):**
    *   Endpoint: `POST /login`
    *   Request Body (JSON): `{"username": "your_username", "password": "your_password"}` (Credentials from `users.json`)
    *   Response: `{"access_token": "your_jwt_token"}`

*   **Add a Job (requires authentication):**
    *   Endpoint: `POST /add-job`
    *   Headers: `Authorization: Bearer your_jwt_token`
    *   Request Body (JSON): `{"payload": {"task_type": "process_data", "value": 42}, "handler": "data_processor_handler"}`
    *   Response: `{"status": "ok", "job_id": 123, "payload": ...}`

*   **Check API Health:**
    *   Endpoint: `GET /health`
    *   Response: `{"status": "ok", "worker": "alive"}` (or other statuses depending on worker heartbeat)

*   **View API Documentation:**
    *   Open `http://127.0.0.1:8000/docs` in your browser.

## Handler Registry

You can define custom Python functions to process specific types of jobs.

1.  **Create or modify `taskmq/jobs/handlers.py`:**

    ```python
    from taskmq.jobs.handlers import register_handler
    import json # Or any other library you need

    @register_handler("my_custom_handler")
    def custom_task_processor(job):
        print(f"Processing job ID: {job.id}")
        payload_data = json.loads(job.payload) # Assuming payload is JSON string
        print(f"Payload: {payload_data}")
        # ... your custom logic here ...
        if "error" in payload_data:
            raise Exception("Simulated error in processing")
        print(f"Job {job.id} completed successfully.")

    @register_handler("another_handler")
    def another_task_function(job):
        # ...
        pass
    ```

2.  **Ensure your worker can find these handlers.** The application automatically discovers handlers registered in `taskmq.jobs.handlers.py`.

3.  **Add jobs specifying your handler:**
    *   Via CLI: `taskmq add-job --payload '{"data": "important_task"}' --handler my_custom_handler`
    *   Via API: When adding a job, include `"handler": "my_custom_handler"` in the request body.

## Testing

The project uses `pytest` for testing.

1.  **Install test dependencies (including pytest):**
    ```bash
    pip install pytest httpx # Add other test dependencies if needed
    ```
    (Note: The CI workflow uses `pip install .[test]`, but the `test` extra is not currently defined in `setup.py`. Installing `pytest` manually is recommended for local testing.)

2.  **Run tests:**
    ```bash
    pytest -v
    ```
    Tests are located in the `tests/` directory.

## Continuous Integration (CI)

*   GitHub Actions is configured to run tests automatically on every push and pull request to the `main` branch.
*   The workflow configuration can be found in `.github/workflows/ci.yml`.

## Project Structure (Overview)

```
.
├── .github/workflows/ci.yml  # GitHub Actions CI configuration
├── Dockerfile                # Docker image definition
├── docker-compose.yml        # Docker services orchestration
├── LICENSE                   # Project License
├── pyproject.toml            # Python project configuration (PEP 517/518)
├── README.md                 # This file
├── requirements.txt          # Main application dependencies
├── setup.py                  # Setuptools script for packaging
├── taskmq/                # Main application package
│   ├── __init__.py
│   ├── api_server.py         # FastAPI application, endpoints
│   ├── cli.py                # Click-based command-line interface
│   ├── main.py               # Older argparse-based CLI (less used now)
│   ├── worker.py             # Task queue worker logic
│   ├── users.json            # Example user credentials for API auth
│   ├── jobs/
│   │   ├── __init__.py
│   │   └── handlers.py       # Job handler registration and definitions
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── base.py           # Base storage interfaces, Job dataclass
│   │   ├── sqlite_backend.py # SQLite storage implementation
│   │   └── redis_backend.py  # Stub for Redis storage
│   └── utils/
│       ├── __init__.py
│       └── heartbeat.py      # Worker heartbeat logic
└── tests/                    # Pytest tests
    ├── test_api_auth.py
    ├── test_cli.py
    ├── test_storage.py
    └── test_worker.py
```

## Contributing

Pull requests and issues are welcome! Please:
*   Add tests for new features or bug fixes.
*   Follow the existing code style.
*   Ensure tests pass locally before submitting.

## License

This project is licensed under the Apache License 2.0. See the `LICENSE` file for details.

## Author

This project is maintained by "Varun Gupta".
