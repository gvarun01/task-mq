import click
import time
from taskmq.storage import sqlite_backend
from taskmq import worker
import json
from taskmq.jobs.handlers import register_handler, HANDLERS

@click.group()
def cli():
    """TaskForge CLI"""
    pass

@cli.command()
@click.option('--max-workers', default=1, show_default=True, help='Number of worker threads')
def run_worker(max_workers):
    """Start the worker pool to consume jobs."""
    w = worker.Worker(max_workers=max_workers)
    click.echo(f"Starting worker pool with {max_workers} worker(s)... Press Ctrl+C to stop.")
    try:
        w.start()
    except KeyboardInterrupt:
        click.echo("Stopping worker...")
        w.stop()

@cli.command()
def serve_api():
    """Start the FastAPI server."""
    import uvicorn
    click.echo("Starting API server on http://127.0.0.1:8000 ...")
    uvicorn.run("taskmq.api_server:app", host="127.0.0.1", port=8000, reload=False)

@cli.command()
@click.option('--payload', default=None, help='Payload for the job (as JSON string)')
@click.option('--handler', default=None, help='Handler name for the job')
def add_job(payload, handler):
    """Add a job to the queue."""
    backend = sqlite_backend.SQLiteBackend()
    if payload:
        try:
            payload_obj = json.loads(payload)
        except Exception as e:
            click.echo(f"Invalid JSON for payload: {e}")
            return
    else:
        payload_obj = {"task": f"Sample at {time.time()}"}
    job_id = backend.insert_job(json.dumps(payload_obj), handler=handler)
    click.echo(f"Inserted job with ID: {job_id}, handler: {handler}, payload: {payload_obj}")

@cli.command()
def register_dummy_handler():
    """Register a dummy handler for testing."""
    @register_handler("dummy")
    def dummy_handler(job):
        click.echo(f"[DUMMY HANDLER] Executed for job {job.id} with payload: {job.payload}")
    click.echo("Dummy handler 'dummy' registered.")


def main():
    cli()

if __name__ == "__main__":
    main()
