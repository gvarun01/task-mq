import redis
import json
from datetime import datetime, timedelta, UTC
from typing import Optional, Any
from taskmq.storage.base import QueueBackend, Job, JobStatus
import time

class RedisBackend(QueueBackend):
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = redis.from_url(redis_url)
        self.prefix = "taskmq:"

    def _key(self, key):
        return f"{self.prefix}{key}"

    def insert_job(self, payload: Any, retry_policy: str = "exponential", scheduled_for: Optional[datetime] = None, interval_seconds: Optional[int] = None, handler: Optional[str] = None, locked_by: Optional[str] = None, lock_expires_at: Optional[datetime] = None, priority: int = 0) -> int:
        job_id = self.redis.incr(self._key("job_id_counter"))
        now = datetime.now(UTC)
        scheduled = scheduled_for or now
        
        job_data = {
            "id": job_id,
            "status": JobStatus.PENDING.value,
            "payload": str(payload),
            "created_at": now.isoformat(),
            "retries": 0,
            "retry_policy": retry_policy,
            "scheduled_for": scheduled.isoformat(),
            "interval_seconds": interval_seconds if interval_seconds is not None else "",
            "handler": handler or "",
            "locked_by": locked_by or "",
            "lock_expires_at": lock_expires_at.isoformat() if lock_expires_at else "",
            "priority": priority
        }
        
        # Store job details
        self.redis.hset(self._key(f"job:{job_id}"), mapping=job_data)
        
        # Add to pending queue (sorted set)
        # Score calculation:
        # We want High Priority first. ZREVRANGE gives high scores first.
        # We want Older Jobs first (within same priority).
        # Score = Priority * 10^12 + (MAX_TIMESTAMP - timestamp)
        # Max timestamp (year 3000) approx 32503680000. 10^12 is safe.
        
        MAX_TIMESTAMP = 32503680000 # Year 3000
        timestamp = scheduled.timestamp()
        score = (priority * 1000000000000) + (MAX_TIMESTAMP - timestamp)
        
        self.redis.zadd(self._key("queue:pending"), {str(job_id): score})
        
        # Track periodic jobs
        if interval_seconds:
            self.redis.sadd(self._key("jobs:periodic"), job_id)
        
        return job_id

    def fetch_job(self, worker_id: str, lock_timeout: int = 30) -> Optional[Job]:
        now_ts = datetime.now(UTC).timestamp()
        
        # Lua script to atomically fetch and move to processing
        # We use ZREVRANGEBYSCORE to get highest priority first
        # But wait, we need to filter by scheduled time <= now.
        # Our score is mixed.
        # If we use mixed score, we can't easily filter by time using ZRANGEBYSCORE.
        # Alternative: Use separate queues for priorities? Or just scan?
        # Scanning is slow.
        # 
        # Let's rethink Redis priority.
        # If we use ZRANGE (low score first), we want High Priority to have LOW score.
        # Score = (MAX_PRIORITY - priority) * 10^12 + timestamp.
        # Then ZRANGE gives lowest score: Highest Priority (smallest prefix) + Smallest Timestamp (oldest).
        # This works perfectly with ZRANGEBYSCORE if we just want "top job".
        # But we also need "scheduled_for <= now".
        # The timestamp part of the score is the scheduled time.
        # So Score <= (MAX_PRIORITY - priority) * 10^12 + now_ts.
        # But we have multiple priority levels.
        # We would need to check each priority range.
        # 
        # Simpler approach for Redis:
        # Just use the timestamp as score (like before).
        # But store priority in the job hash.
        # When fetching, we get the top N jobs (by time), and then sort them by priority in Lua?
        # No, that's not true priority queue.
        #
        # Best approach for Redis: Multiple Queues.
        # queue:pending:high
        # queue:pending:normal
        # queue:pending:low
        #
        # But then we have to poll multiple queues.
        #
        # Let's stick to the single queue but with the "Low Score = High Priority" formula.
        # Score = (MAX_PRIORITY - priority) * 10^12 + timestamp.
        # MAX_PRIORITY = 100.
        # High (20) -> (100-20)*... = 80...
        # Normal (10) -> (100-10)*... = 90...
        # Low (0) -> (100-0)*... = 100...
        #
        # So High priority comes first in ZRANGE.
        #
        # Now, how to filter `scheduled_for <= now`?
        # We can't simply use ZRANGEBYSCORE -inf now_ts because the score is huge.
        # We have to check ranges.
        # Range 1 (High): [80...0, 80...now]
        # Range 2 (Normal): [90...0, 90...now]
        # Range 3 (Low): [100...0, 100...now]
        #
        # We can iterate through these ranges in the Lua script.
        
        script = """
        local pending_key = KEYS[1]
        local processing_key = KEYS[2]
        local job_key_prefix = ARGV[1]
        local now_ts = tonumber(ARGV[2])
        local lock_timeout = tonumber(ARGV[3])
        local worker_id = ARGV[4]
        local lock_expires_ts = now_ts + lock_timeout
        local lock_expires_iso = ARGV[5]
        
        local priorities = {20, 10, 0} -- High, Normal, Low
        local max_priority = 100
        local multiplier = 1000000000000
        
        for _, prio in ipairs(priorities) do
            local base_score = (max_priority - prio) * multiplier
            local max_score = base_score + now_ts
            
            local jobs = redis.call('ZRANGEBYSCORE', pending_key, '-inf', max_score, 'LIMIT', 0, 1)
            if #jobs > 0 then
                local job_id = jobs[1]
                redis.call('ZREM', pending_key, job_id)
                redis.call('ZADD', processing_key, lock_expires_ts, job_id)
                redis.call('HSET', job_key_prefix .. job_id, 'locked_by', worker_id, 'lock_expires_at', lock_expires_iso, 'status', 'RUNNING')
                return job_id
            end
        end
        
        return nil
        """
        
        now = datetime.now(UTC)
        lock_expires = (now + timedelta(seconds=lock_timeout)).isoformat()
        
        cmd = self.redis.register_script(script)
        job_id = cmd(keys=[self._key("queue:pending"), self._key("queue:processing")], 
                     args=[self._key("job:"), now_ts, lock_timeout, worker_id, lock_expires])
        
        if job_id:
            return self.get_job(int(job_id))
        return None

    def update_status(self, job_id: int, status: JobStatus, retries: int = 0, error_log: Optional[str] = None, result: Any = None, handler_hash: Optional[str] = None):
        updates = {
            "status": status.value,
            "retries": retries
        }
        if error_log:
            updates["error_log"] = error_log
        if result is not None:
            updates["result"] = str(result)
        if handler_hash:
            updates["handler_hash"] = handler_hash
            
        self.redis.hset(self._key(f"job:{job_id}"), mapping=updates)
        
        # Remove from processing queue
        self.redis.zrem(self._key("queue:processing"), str(job_id))
        
        if status == JobStatus.PENDING:
            # Add back to pending queue
            # We need scheduled_for and priority. Fetch them.
            job_data = self.redis.hmget(self._key(f"job:{job_id}"), "scheduled_for", "priority")
            scheduled_for_str = job_data[0]
            priority = int(job_data[1]) if job_data[1] else 0
            
            if scheduled_for_str:
                scheduled_ts = datetime.fromisoformat(scheduled_for_str.decode('utf-8')).timestamp()
            else:
                scheduled_ts = datetime.now(UTC).timestamp()
            
            # Recalculate score
            MAX_PRIORITY = 100
            MULTIPLIER = 1000000000000
            score = (MAX_PRIORITY - priority) * MULTIPLIER + scheduled_ts
                
            self.redis.zadd(self._key("queue:pending"), {str(job_id): score})
            
            # Clear lock
            self.redis.hset(self._key(f"job:{job_id}"), mapping={"locked_by": "", "lock_expires_at": ""})

    def get_job(self, job_id: int) -> Optional[Job]:
        data = self.redis.hgetall(self._key(f"job:{job_id}"))
        if not data:
            return None
            
        # Decode bytes to strings
        data = {k.decode('utf-8'): v.decode('utf-8') for k, v in data.items()}
        
        return Job(
            id=int(data["id"]),
            status=JobStatus(data["status"]),
            payload=data.get("payload"),
            created_at=datetime.fromisoformat(data["created_at"]),
            retries=int(data["retries"]),
            error_log=data.get("error_log"),
            retry_policy=data.get("retry_policy", "exponential"),
            scheduled_for=datetime.fromisoformat(data["scheduled_for"]) if data.get("scheduled_for") else datetime.now(UTC),
            interval_seconds=int(data["interval_seconds"]) if data.get("interval_seconds") else None,
            handler=data.get("handler"),
            locked_by=data.get("locked_by"),
            lock_expires_at=datetime.fromisoformat(data["lock_expires_at"]) if data.get("lock_expires_at") else None,
            result=data.get("result"),
            priority=int(data.get("priority", 0)),
            handler_hash=data.get("handler_hash")
        )

    def requeue_expired_locks(self):
        now_ts = datetime.now(UTC).timestamp()
        
        # Find expired jobs in processing queue
        expired_jobs = self.redis.zrangebyscore(self._key("queue:processing"), "-inf", now_ts)
        
        for job_id in expired_jobs:
            job_id = job_id.decode('utf-8')
            # Move back to pending
            self.redis.zrem(self._key("queue:processing"), job_id)
            
            # We need to recalculate score for pending queue
            job_data = self.redis.hmget(self._key(f"job:{job_id}"), "scheduled_for", "priority")
            scheduled_for_str = job_data[0]
            priority = int(job_data[1]) if job_data[1] else 0
            
            if scheduled_for_str:
                scheduled_ts = datetime.fromisoformat(scheduled_for_str.decode('utf-8')).timestamp()
            else:
                scheduled_ts = now_ts
                
            MAX_PRIORITY = 100
            MULTIPLIER = 1000000000000
            score = (MAX_PRIORITY - priority) * MULTIPLIER + scheduled_ts
            
            self.redis.zadd(self._key("queue:pending"), {job_id: score})
            
            # Update status and clear lock
            self.redis.hset(self._key(f"job:{job_id}"), mapping={
                "status": JobStatus.PENDING.value,
                "locked_by": "",
                "lock_expires_at": ""
            })

    def reschedule_periodic_jobs(self):
        # Iterate over all periodic jobs
        periodic_jobs = self.redis.smembers(self._key("jobs:periodic"))
        
        for job_id in periodic_jobs:
            job_id = job_id.decode('utf-8')
            data = self.redis.hmget(self._key(f"job:{job_id}"), "status", "interval_seconds", "priority")
            status = data[0].decode('utf-8') if data[0] else None
            interval = int(data[1].decode('utf-8')) if data[1] else None
            priority = int(data[2].decode('utf-8')) if data[2] else 0
            
            if status == JobStatus.SUCCESS.value and interval:
                next_time = datetime.now(UTC) + timedelta(seconds=interval)
                
                # Update job
                self.redis.hset(self._key(f"job:{job_id}"), mapping={
                    "status": JobStatus.PENDING.value,
                    "scheduled_for": next_time.isoformat(),
                    "retries": 0,
                    "error_log": ""
                })
                
                # Add to pending queue
                MAX_PRIORITY = 100
                MULTIPLIER = 1000000000000
                score = (MAX_PRIORITY - priority) * MULTIPLIER + next_time.timestamp()
                
                self.redis.zadd(self._key("queue:pending"), {job_id: score})

    def get_queue_depth(self) -> int:
        return self.redis.zcard(self._key("queue:pending"))

    def check_health(self) -> bool:
        try:
            return self.redis.ping()
        except redis.RedisError:
            return False
    
    def move_to_dlq(self, job_id: int, error_log: Optional[str] = None):
        # Update job status and error log
        self.redis.hset(self._key(f"job:{job_id}"), mapping={
            "status": JobStatus.FAILED.value,
            "error_log": error_log or ""
        })
        # Remove from pending/running queues
        self.redis.zrem(self._key("queue:pending"), str(job_id))
        # Add to dead letter queue (ZSet for ordering)
        now_score = datetime.now(UTC).timestamp()
        self.redis.zadd(self._key("queue:dead"), {str(job_id): now_score})

    def list_dead_jobs(self, limit: int = 100, offset: int = 0) -> list[Job]:
        # ZREVRANGE to get newest dead jobs first
        job_ids = self.redis.zrevrange(self._key("queue:dead"), offset, offset + limit - 1)
        jobs = []
        for job_id in job_ids:
            job = self.get_job(int(job_id))
            if job:
                jobs.append(job)
        return jobs

    def replay_dead_job(self, job_id: int) -> Optional[int]:
        # Check if in dead queue
        score = self.redis.zscore(self._key("queue:dead"), str(job_id))
        if score is None:
            return None
            
        # Get job data
        job = self.get_job(job_id)
        if not job:
            return None
            
        # Create new job (replay)
        new_id = self.insert_job(
            payload=job.payload,
            retry_policy=job.retry_policy,
            handler=job.handler,
            priority=job.priority,
            interval_seconds=job.interval_seconds
        )
        
        # Remove from dead queue
        self.redis.zrem(self._key("queue:dead"), str(job_id))
        # Delete the old job data
        self.redis.delete(self._key(f"job:{job_id}"))
        
        return new_id

    def add_log(self, job_id: int, level: str, message: str, handler: Optional[str] = None):
        log_entry = {
            "job_id": job_id,
            "handler": handler,
            "level": level,
            "message": message,
            "timestamp": datetime.now(UTC).isoformat()
        }
        # Store in a list for the job
        self.redis.rpush(self._key(f"logs:job:{job_id}"), json.dumps(log_entry))
        
        # If handler is provided, we could index it, but for simplicity we'll just rely on job logs for now
        # Or we can have a global log list for search?
        # Let's just store per job for now as that's the primary access pattern for "inspect"
        # For "logs --handler", we would need a secondary index.
        if handler:
             self.redis.rpush(self._key(f"logs:handler:{handler}"), json.dumps(log_entry))

    def get_logs(self, job_id: Optional[int] = None, handler: Optional[str] = None, limit: int = 100) -> list[dict]:
        logs = []
        if job_id:
            raw_logs = self.redis.lrange(self._key(f"logs:job:{job_id}"), 0, limit - 1)
            logs.extend([json.loads(l) for l in raw_logs])
        elif handler:
            raw_logs = self.redis.lrange(self._key(f"logs:handler:{handler}"), 0, limit - 1)
            logs.extend([json.loads(l) for l in raw_logs])
        
        # Sort by timestamp if needed, but they are appended in order
        return logs
