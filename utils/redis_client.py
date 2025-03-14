import redis
import json
from typing import Dict, Any, Optional, List, Union
import logging
from datetime import datetime, timedelta

from config import Config

logger = logging.getLogger("dopcast.redis")

class RedisClient:
    """
    Redis client for DopCast system.
    Provides caching, message queuing, and job tracking functionality.
    """
    
    def __init__(self):
        """
        Initialize the Redis client.
        """
        self.enabled = Config.REDIS_ENABLED
        self.client = None
        
        if self.enabled:
            try:
                self.client = redis.Redis(
                    host=Config.REDIS_HOST,
                    port=Config.REDIS_PORT,
                    db=Config.REDIS_DB,
                    password=Config.REDIS_PASSWORD,
                    decode_responses=True  # Automatically decode responses to strings
                )
                self.client.ping()  # Test connection
                logger.info(f"Connected to Redis at {Config.REDIS_HOST}:{Config.REDIS_PORT}")
            except redis.ConnectionError as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                self.enabled = False
    
    def is_connected(self) -> bool:
        """
        Check if Redis connection is active.
        
        Returns:
            True if connected, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            return self.client.ping()
        except:
            return False
    
    def set_cache(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            expire_seconds: Optional expiration time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            serialized = json.dumps(value)
            result = self.client.set(key, serialized)
            
            if expire_seconds is not None:
                self.client.expire(key, expire_seconds)
            
            return result
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
            return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.is_connected():
            return None
        
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            return json.loads(value)
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None
    
    def delete_cache(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    def publish_message(self, channel: str, message: Dict[str, Any]) -> bool:
        """
        Publish a message to a channel.
        
        Args:
            channel: Channel name
            message: Message to publish (will be JSON serialized)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            serialized = json.dumps(message)
            subscribers = self.client.publish(channel, serialized)
            return subscribers > 0
        except Exception as e:
            logger.error(f"Error publishing to channel {channel}: {str(e)}")
            return False
    
    def add_job(self, queue_name: str, job_data: Dict[str, Any], job_id: Optional[str] = None) -> Optional[str]:
        """
        Add a job to a queue.
        
        Args:
            queue_name: Name of the queue
            job_data: Job data (will be JSON serialized)
            job_id: Optional job ID (generated if not provided)
            
        Returns:
            Job ID if successful, None otherwise
        """
        if not self.is_connected():
            return None
        
        try:
            # Generate job ID if not provided
            if job_id is None:
                job_id = f"job_{queue_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.client.incr('job_counter')}"
            
            # Add job metadata
            job_data["job_id"] = job_id
            job_data["queue"] = queue_name
            job_data["status"] = "pending"
            job_data["created_at"] = datetime.now().isoformat()
            
            # Add to queue and set job details
            serialized = json.dumps(job_data)
            pipeline = self.client.pipeline()
            pipeline.lpush(f"queue:{queue_name}", job_id)
            pipeline.set(f"job:{job_id}", serialized)
            pipeline.execute()
            
            logger.info(f"Added job {job_id} to queue {queue_name}")
            return job_id
        except Exception as e:
            logger.error(f"Error adding job to queue {queue_name}: {str(e)}")
            return None
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job details.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job details or None if not found
        """
        if not self.is_connected():
            return None
        
        try:
            job_data = self.client.get(f"job:{job_id}")
            if job_data is None:
                return None
            
            return json.loads(job_data)
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {str(e)}")
            return None
    
    def update_job_status(self, job_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update job status.
        
        Args:
            job_id: Job ID
            status: New status (pending, processing, completed, failed)
            result: Optional job result
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            job_data = self.get_job(job_id)
            if job_data is None:
                return False
            
            job_data["status"] = status
            job_data["updated_at"] = datetime.now().isoformat()
            
            if status == "completed" or status == "failed":
                job_data["completed_at"] = datetime.now().isoformat()
            
            if result is not None:
                job_data["result"] = result
            
            serialized = json.dumps(job_data)
            self.client.set(f"job:{job_id}", serialized)
            
            # Also publish an update notification
            self.publish_message("job_updates", {
                "job_id": job_id,
                "status": status,
                "queue": job_data.get("queue", "unknown")
            })
            
            return True
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {str(e)}")
            return False
    
    def get_next_job(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the next job from a queue.
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            Job details or None if queue is empty
        """
        if not self.is_connected():
            return None
        
        try:
            # Get job ID from queue (blocking pop with 1 second timeout)
            result = self.client.brpop(f"queue:{queue_name}", 1)
            if result is None:
                return None
            
            # Extract job ID from result tuple (queue_name, job_id)
            _, job_id = result
            
            # Get job details
            job_data = self.get_job(job_id)
            if job_data is None:
                return None
            
            # Update job status to processing
            self.update_job_status(job_id, "processing")
            
            return job_data
        except Exception as e:
            logger.error(f"Error getting next job from queue {queue_name}: {str(e)}")
            return None
    
    def get_queue_length(self, queue_name: str) -> int:
        """
        Get the number of jobs in a queue.
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            Number of jobs in the queue
        """
        if not self.is_connected():
            return 0
        
        try:
            return self.client.llen(f"queue:{queue_name}")
        except Exception as e:
            logger.error(f"Error getting queue length for {queue_name}: {str(e)}")
            return 0
    
    def get_recent_jobs(self, queue_name: Optional[str] = None, status: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent jobs, optionally filtered by queue and status.
        
        Args:
            queue_name: Optional queue name filter
            status: Optional status filter
            limit: Maximum number of jobs to return
            
        Returns:
            List of job details
        """
        if not self.is_connected():
            return []
        
        try:
            # Get all job keys
            job_keys = self.client.keys("job:*")
            
            # Get job details for each key
            jobs = []
            for key in job_keys:
                job_data = json.loads(self.client.get(key))
                
                # Apply filters
                if queue_name and job_data.get("queue") != queue_name:
                    continue
                
                if status and job_data.get("status") != status:
                    continue
                
                jobs.append(job_data)
            
            # Sort by creation time (newest first) and limit
            jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return jobs[:limit]
        except Exception as e:
            logger.error(f"Error getting recent jobs: {str(e)}")
            return []

# Singleton instance
redis_client = RedisClient()
