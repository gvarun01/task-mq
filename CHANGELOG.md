# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2025-08-27

### 📚 Documentation & Project Enhancement

#### Added
- **Comprehensive Project Metadata**: Enhanced `pyproject.toml` with professional description, keywords, and PyPI classifiers
- **Development Tools Configuration**: Added complete tooling setup for black, isort, mypy, pytest, and coverage
- **Extended Optional Dependencies**: Added development, testing, Redis, and documentation dependency groups
- **Professional PyPI Presence**: Improved package discoverability with proper keywords and categorization
- **Enhanced URL Links**: Added comprehensive project links including documentation, issues, and changelog

#### Changed
- **Improved Package Description**: Updated from basic description to comprehensive, professional project summary
- **CLI Entry Point**: Standardized command from `task-mq` to `taskmq` for consistency
- **Dependency Specifications**: Added version pinning for all dependencies to ensure stability
- **Enhanced FastAPI Support**: Added `uvicorn[standard]` and `python-jose[cryptography]` for better production readiness

#### Fixed
- **Project Metadata Completeness**: Added missing maintainer information and license references
- **Development Workflow**: Configured comprehensive testing, linting, and formatting tools

### 🔧 Technical Improvements
- **Better Type Safety**: Added mypy configuration with strict type checking
- **Code Quality**: Configured black, isort, and flake8 for consistent code formatting
- **Test Coverage**: Enhanced pytest configuration with coverage reporting and custom markers
- **PyPI Compatibility**: Improved package metadata for better PyPI integration

---

## [0.1.0] - 2025-08-27

### 🎉 Initial Release

#### Added
- **Core Task Queue Engine**: Background job processing with worker pools
- **CLI Interface**: Complete command-line interface for job management
- **REST API**: FastAPI-based API with JWT authentication
- **Handler System**: Decorator-based job handler registration
- **Storage Backends**: SQLite backend with Redis stub for future expansion
- **Monitoring**: Prometheus metrics integration
- **Docker Support**: Dockerfile and docker-compose configuration
- **Retry Policies**: Configurable retry strategies (fixed, exponential, none)
- **Job Scheduling**: Support for future and periodic job execution
- **Documentation**: Comprehensive documentation with MkDocs

#### Features
- Multi-threaded worker processing
- Secure JWT-based API authentication
- Pluggable storage architecture
- Production-ready monitoring and metrics
- Easy deployment with Docker
- Comprehensive test suite
- Developer-friendly CLI tools

---

## Legend
- 🎉 Major features or initial releases
- 📚 Documentation improvements
- 🔧 Technical improvements and fixes
- 🚀 Performance improvements
- 🔐 Security enhancements
- 🐛 Bug fixes
- ⚠️ Breaking changes
