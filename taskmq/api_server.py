from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prometheus_client import make_asgi_app, Counter, Summary
import os
from datetime import datetime, timedelta, UTC
import json
import jwt
from taskmq.storage import base, get_backend

app = FastAPI()

HEARTBEAT_PATH = 'worker_heartbeat.txt'
HEARTBEAT_TIMEOUT = 10  # seconds
JWT_SECRET = os.environ.get('TASKMQ_JWT_SECRET', 'supersecretkey-change-in-production')
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
        'exp': datetime.now(UTC) + timedelta(hours=1)
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
    backend = get_backend()
    payload = data.get('payload')
    priority = data.get('priority', 0)
    if not payload:
        raise HTTPException(status_code=400, detail='Missing payload')
    job_id = backend.insert_job(payload, priority=priority)
    queue_jobs_total.inc()
    return {'status': 'ok', 'job_id': job_id, 'payload': payload, 'priority': priority}

@app.post('/cancel')
def cancel_job(data: dict, user=Depends(require_role(['admin']))):
    backend = get_backend()
    job_id = data.get('job_id')
    job = backend.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    backend.update_status(job_id, base.JobStatus.FAILED, job.retries, 'Cancelled by admin')
    queue_jobs_failed.inc()
    return {'status': 'cancelled', 'job_id': job_id}

@app.post('/retry')
def retry_job(data: dict, user=Depends(require_role(['admin', 'worker']))):
    backend = get_backend()
    job_id = data.get('job_id')
    job = backend.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    backend.update_status(job_id, base.JobStatus.PENDING, job.retries + 1, 'Retry requested')
    queue_jobs_retried.inc()
    return {'status': 'retrying', 'job_id': job_id}

@app.get('/job/{job_id}')
def get_job(job_id: int, user=Depends(require_role(['admin', 'worker']))):
    backend = get_backend()
    job = backend.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return {
        'id': job.id,
        'status': job.status.value,
        'priority': job.priority,
        'payload': job.payload,
        'result': job.result,
        'error_log': job.error_log,
        'retries': job.retries,
        'created_at': job.created_at.isoformat(),
        'scheduled_for': job.scheduled_for.isoformat()
    }

@app.get("/health")
def health():
    backend = get_backend()
    if not backend.check_health():
        return JSONResponse(status_code=500, content={"status": "db_error"})
    
    # Only check heartbeat file if using SQLite (assuming local worker)
    # Or just keep it as is, but handle missing file gracefully
    try:
        if os.path.exists(HEARTBEAT_PATH):
            with open(HEARTBEAT_PATH, 'r') as f:
                timestamp_str = f.read().strip()
                last_seen = datetime.fromisoformat(timestamp_str)
                # Ensure last_seen is timezone-aware for comparison
                if last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=UTC)
                if datetime.now(UTC) - last_seen < timedelta(seconds=HEARTBEAT_TIMEOUT):
                    return {"status": "ok", "worker": "alive"}
                else:
                    return {"status": "degraded", "worker": "not_recently_alive"}
        else:
             return {"status": "ok", "worker": "unknown"} # If no file, maybe worker is remote
    except (OSError, ValueError):
        return {"status": "error", "worker": "not_reporting"}

metrics_app = make_asgi_app()
app.mount("/monitor/metrics", metrics_app) 