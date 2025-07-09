from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prometheus_client import make_asgi_app, Counter, Summary
import sqlite3
import os
import time
from datetime import datetime, timedelta
import json
import jwt
from taskmq.storage import sqlite_backend, base

app = FastAPI()

HEARTBEAT_PATH = 'worker_heartbeat.txt'
HEARTBEAT_TIMEOUT = 10  # seconds
JWT_SECRET = 'supersecretkey'  # In production, use env var
JWT_ALGO = 'HS256'
USERS_PATH = os.path.join(os.path.dirname(__file__), 'users.json')

class CustomHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        if "authorization" not in request.headers:
            raise HTTPException(status_code=401, detail="Not authenticated")
        credentials = await super().__call__(request)
        if credentials is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return credentials

security = CustomHTTPBearer()

# Prometheus metrics
queue_jobs_total = Counter('queue_jobs_total', 'Total jobs added to the queue')
queue_jobs_failed = Counter('queue_jobs_failed', 'Total jobs marked as failed')
queue_jobs_retried = Counter('queue_jobs_retried', 'Total jobs retried')
queue_processing_duration_seconds = Summary('queue_processing_duration_seconds', 'Job processing duration in seconds')

# Load users from users.json
def load_users():
    with open(USERS_PATH) as f:
        return json.load(f)

# JWT encode/decode helpers
def create_token(username, role):
    payload = {
        'sub': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def decode_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expired')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid token')

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_token(credentials.credentials)
    return payload

def require_role(required_roles):
    def role_checker(user=Depends(get_current_user)):
        if user['role'] not in required_roles:
            raise HTTPException(status_code=403, detail='Insufficient role')
        return user
    return role_checker

@app.post('/login')
def login(data: dict):
    users = load_users()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        raise HTTPException(status_code=400, detail='Missing username or password')
    user = users.get(username)
    if not user or user['password'] != password:
        raise HTTPException(status_code=401, detail='Invalid credentials')
    token = create_token(username, user['role'])
    return {'access_token': token}

@app.post('/add-job')
def add_job(data: dict, user=Depends(require_role(['admin']))):
    backend = sqlite_backend.SQLiteBackend()
    payload = data.get('payload')
    if not payload:
        raise HTTPException(status_code=400, detail='Missing payload')
    job_id = backend.insert_job(payload)
    queue_jobs_total.inc()
    return {'status': 'ok', 'job_id': job_id, 'payload': payload}

@app.post('/cancel')
def cancel_job(data: dict, user=Depends(require_role(['admin']))):
    backend = sqlite_backend.SQLiteBackend()
    job_id = data.get('job_id')
    job = backend.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    backend.update_status(job_id, base.JobStatus.FAILED, job.retries, 'Cancelled by admin')
    queue_jobs_failed.inc()
    return {'status': 'cancelled', 'job_id': job_id}

@app.post('/retry')
def retry_job(data: dict, user=Depends(require_role(['admin', 'worker']))):
    backend = sqlite_backend.SQLiteBackend()
    job_id = data.get('job_id')
    job = backend.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    backend.update_status(job_id, base.JobStatus.PENDING, job.retries + 1, 'Retry requested')
    queue_jobs_retried.inc()
    return {'status': 'retrying', 'job_id': job_id}

@app.get("/health")
def health():
    try:
        conn = sqlite3.connect(base.DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
    except Exception:
        return JSONResponse(status_code=500, content={"status": "db_error"})
    try:
        with open(HEARTBEAT_PATH, 'r') as f:
            timestamp_str = f.read().strip()
            last_seen = datetime.fromisoformat(timestamp_str)
            if datetime.utcnow() - last_seen < timedelta(seconds=HEARTBEAT_TIMEOUT):
                return {"status": "ok", "worker": "alive"}
            else:
                return {"status": "degraded", "worker": "not_recently_alive"}
    except Exception:
        return {"status": "error", "worker": "not_reporting"}

metrics_app = make_asgi_app()
app.mount("/monitor/metrics", metrics_app) 