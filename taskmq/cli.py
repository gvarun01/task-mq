import click
import time
import os
from taskmq.storage import get_backend
from taskmq import worker
import json
from taskmq.jobs.handlers import register_handler, get_handler_hash

@click.group()
@click.option('--backend', type=click.Choice(['sqlite', 'redis']), default='sqlite', help='Storage backend')
@click.option('--redis-url', default='redis://localhost:6379/0', help='Redis URL (if backend is redis)')
def cli(backend, redis_url):
    """TaskForge CLI"""
    os.environ["TASKMQ_BACKEND"] = backend
    os.environ["TASKMQ_REDIS_URL"] = redis_url

@cli.command()
@click.option('--max-workers', default=1, show_default=True, help='Number of worker threads')
def run_worker(max_workers):
    """Start the worker pool to consume jobs."""
    w = worker.Worker(max_workers=max_workers)
    click.echo(f"Starting worker pool with {max_workers} worker(s) using {os.environ.get('TASKMQ_BACKEND')} backend... Press Ctrl+C to stop.")
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
@click.option('--priority', default=0, help='Job priority (0=Low, 10=Normal, 20=High)')
def add_job(payload, handler, priority):
    """Add a job to the queue."""
    backend = get_backend()
    if payload:
        try:
            payload_obj = json.loads(payload)
        except Exception as e:
            click.echo(f"Invalid JSON for payload: {e}")
            return
    else:
        payload_obj = {"task": f"Sample at {time.time()}"}
    job_id = backend.insert_job(json.dumps(payload_obj), handler=handler, priority=priority)
    click.echo(f"Inserted job with ID: {job_id}, handler: {handler}, priority: {priority}, payload: {payload_obj}")

@cli.command()
def register_dummy_handler():
    """Register a dummy handler for testing."""
    @register_handler("dummy")
    def dummy_handler(job):
        click.echo(f"[DUMMY HANDLER] Executed for job {job.id} with payload: {job.payload}")
    click.echo("Dummy handler 'dummy' registered.")


@cli.command()
@click.argument('job_id', type=int)
def get_job(job_id):
    """Get job details and result."""
    backend = get_backend()
    job = backend.get_job(job_id)
    if not job:
        click.echo(f"Job {job_id} not found.")
        return
    
    click.echo(f"Job ID: {job.id}")
    click.echo(f"Status: {job.status.value}")
    click.echo(f"Priority: {job.priority}")
    click.echo(f"Payload: {job.payload}")
    click.echo(f"Result: {job.result}")
    if job.error_log:
        click.echo(f"Error: {job.error_log}")
    click.echo(f"Retries: {job.retries}")

@cli.command()
@click.option('--limit', default=20, help='Number of jobs to list')
@click.option('--offset', default=0, help='Offset for pagination')
def list_dead(limit, offset):
    """List jobs in the Dead Letter Queue."""
    backend = get_backend()
    jobs = backend.list_dead_jobs(limit=limit, offset=offset)
    if not jobs:
        click.echo("No dead jobs found.")
        return
    
    click.echo(f"Found {len(jobs)} dead jobs:")
    for job in jobs:
        click.echo(f"ID: {job.id} | Created: {job.created_at} | Handler: {job.handler} | Error: {job.error_log}")

@cli.command()
@click.argument('job_id', type=int)
def replay_dead(job_id):
    """Replay a job from the Dead Letter Queue."""
    backend = get_backend()
    new_id = backend.replay_dead_job(job_id)
    if new_id:
        click.echo(f"Job {job_id} replayed successfully. New Job ID: {new_id}")
    else:
        click.echo(f"Job {job_id} not found in DLQ or could not be replayed.")

@cli.command()
@click.argument('job_id', type=int)
@click.option('--exact', is_flag=True, help='Ensure handler code matches the original job execution.')
def replay(job_id, exact):
    """Replay any job by creating a copy."""
    backend = get_backend()
    job = backend.get_job(job_id)
    if not job:
        click.echo(f"Job {job_id} not found.")
        return

    if exact:
        if not job.handler_hash:
            click.echo("Error: Original job has no handler hash stored. Cannot perform exact replay.")
            return
        
        current_hash = get_handler_hash(job.handler)
        if not current_hash:
            click.echo(f"Error: Handler '{job.handler}' not found in current process. Cannot verify hash.")
            return
            
        if current_hash != job.handler_hash:
            click.echo(f"Error: Handler hash mismatch.\nOriginal: {job.handler_hash}\nCurrent:  {current_hash}\nCode has changed since the job ran.")
            return
        
        click.echo("Handler hash verified. Code matches.")

    # Create new job
    new_id = backend.insert_job(
        payload=job.payload,
        retry_policy=job.retry_policy,
        handler=job.handler,
        priority=job.priority,
        interval_seconds=job.interval_seconds
    )
    click.echo(f"Job {job_id} replayed. New Job ID: {new_id}")

@cli.command()
@click.argument('job_id', type=int)
def inspect(job_id):
    """Inspect job execution timeline."""
    backend = get_backend()
    job = backend.get_job(job_id)
    if not job:
        click.echo(f"Job {job_id} not found.")
        return
    
    click.echo(f"Job ID: {job.id}")
    click.echo(f"Status: {job.status.value}")
    click.echo(f"Handler: {job.handler}")
    click.echo(f"Payload: {job.payload}")
    click.echo("-" * 40)
    click.echo("Execution Timeline:")
    
    # Get logs for this job
    logs = backend.get_logs(job_id=job_id)
    
    # Add creation time as first event
    click.echo(f"[{job.created_at.isoformat()}] Queued")
    
    for log in logs:
        click.echo(f"[{log['timestamp']}] {log['message']}")

@cli.command()
@click.option('--job', type=int, help='Filter logs by Job ID')
@click.option('--handler', type=str, help='Filter logs by Handler name')
@click.option('--limit', default=50, help='Number of logs to show')
def logs(job, handler, limit):
    """Search structured job logs."""
    backend = get_backend()
    if not job and not handler:
        click.echo("Please specify --job or --handler")
        return
        
    logs = backend.get_logs(job_id=job, handler=handler, limit=limit)
    if not logs:
        click.echo("No logs found.")
        return
        
    for log in logs:
        click.echo(f"[{log['timestamp']}] [Job {log['job_id']}] [{log['level']}] {log['message']}")

def main():
    cli()

if __name__ == "__main__":
    main()
