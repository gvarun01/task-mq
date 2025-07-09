import argparse
import time
from taskmq.storage import sqlite_backend
from taskmq import worker
import sys


def print_job(job):
    print(f"Processing job {job.id}: {job.payload}")
    time.sleep(1)

def run_worker(args):
    w = worker.Worker(print_job, max_workers=args.max_workers)
    print(f"Starting worker pool with {args.max_workers} worker(s)... Press Ctrl+C to stop.")
    try:
        w.start()
    except KeyboardInterrupt:
        print("Stopping worker...")
        w.stop()

def serve_api(args):
    import uvicorn
    print("Starting API server on http://127.0.0.1:8000 ...")
    uvicorn.run("taskmq.api_server:app", host="127.0.0.1", port=8000, reload=False)

def add_job(args):
    backend = sqlite_backend.SQLiteBackend()
    payload = args.payload or f"Sample payload at {time.time()}"
    job_id = backend.insert_job(payload)
    print(f"Inserted job with ID: {job_id} and payload: {payload}")

def main():
    parser = argparse.ArgumentParser(description="TaskForge CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    worker_parser = subparsers.add_parser("run-worker", help="Start the worker pool to consume jobs")
    worker_parser.add_argument('--max-workers', type=int, default=1, help='Number of worker threads (default: 1)')
    worker_parser.set_defaults(func=run_worker)

    api_parser = subparsers.add_parser("serve-api", help="Start the FastAPI server")
    api_parser.set_defaults(func=serve_api)

    addjob_parser = subparsers.add_parser("add-job", help="Add a job to the queue")
    addjob_parser.add_argument('--payload', type=str, help='Payload for the job')
    addjob_parser.set_defaults(func=add_job)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main() 