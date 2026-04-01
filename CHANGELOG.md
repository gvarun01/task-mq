# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2025-04-01

### Added
- Google-style docstrings for public API functions
- `py.typed` marker file for PEP 561 compliance
- Ruff configuration for linting and formatting
- Comprehensive test suite expansion with new test files

### Changed
- Replaced deprecated `datetime.utcnow()` with timezone-aware `datetime.now(UTC)`
- Improved test isolation with unique database files per test
- CLI now properly handles KeyboardInterrupt for graceful shutdown
- Complete documentation rewrite with professional formatting

### Fixed
- Removed duplicate `QueueBackend` abstract class definitions
- Fixed bare except clauses with specific exception types
- Removed unused imports across codebase
- Fixed failing tests (retry logic, worker isolation, CLI interrupt handling)

### Security
- JWT secret key now reads from `TASKMQ_JWT_SECRET` environment variable

## [0.1.1] - 2024-12-18

### Added
- Comprehensive project metadata in `pyproject.toml`
- Development tools configuration (ruff, mypy, pytest, coverage)
- Extended optional dependencies for dev, test, redis, and docs
- Professional PyPI classifiers and keywords

### Changed
- CLI entry point standardized from `task-mq` to `taskmq`
- Added version pinning for all dependencies
- Enhanced FastAPI support with `uvicorn[standard]` and `python-jose[cryptography]`

### Fixed
- Added missing maintainer information and license references
- Configured comprehensive testing and linting tools

## [0.1.0] - 2024-12-15

### Added
- Core task queue engine with background job processing
- Multi-threaded worker pool with configurable concurrency
- CLI interface for job management (`add-job`, `run-worker`, `serve-api`)
- REST API with FastAPI and automatic OpenAPI documentation
- JWT-based authentication with role-based access control
- Decorator-based handler registration system
- SQLite storage backend (default)
- Redis storage backend for production workloads
- Prometheus metrics integration (`/monitor/metrics`)
- Retry policies: fixed interval, exponential backoff, none
- Job scheduling for future execution
- Periodic/recurring job support
- Job priority levels (Low, Normal, High)
- Dead Letter Queue (DLQ) for failed jobs
- Job replay functionality with handler versioning
- Graceful shutdown with in-flight job completion
- Per-job execution timeline and structured logging
- Docker and docker-compose configuration
- Comprehensive test suite with pytest
- MkDocs documentation site

[Unreleased]: https://github.com/gvarun01/task-mq/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/gvarun01/task-mq/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/gvarun01/task-mq/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/gvarun01/task-mq/releases/tag/v0.1.0
