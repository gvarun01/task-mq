FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for SQLite
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Create a non-root user for running the app (for SQLite file permissions)
RUN useradd -ms /bin/bash appuser
RUN chown -R appuser /app
USER appuser

# Expose ports for API and metrics
EXPOSE 8000 9090

# Entrypoint is set in docker-compose.yml
CMD ["python", "main.py"] 