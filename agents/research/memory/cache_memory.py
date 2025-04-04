"""
Cache memory component for the Research Agent.
Provides enhanced caching capabilities with TTL and persistence.
"""

import logging
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class CacheMemory:
    """
    Enhanced cache memory with TTL and persistence.
    """
    
    def __init__(self, cache_dir: str, default_ttl: int = 86400):
        """
        Initialize the cache memory.
        
        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds (86400 = 1 day)
        """
        self.logger = logging.getLogger("dopcast.research.cache_memory")
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self.cache = {}
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load existing cache
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk."""
        cache_file = os.path.join(self.cache_dir, "research_cache.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                
                # Convert string timestamps back to datetime objects
                for key, entry in cache_data.items():
                    if "timestamp" in entry and isinstance(entry["timestamp"], str):
                        entry["timestamp"] = datetime.fromisoformat(entry["timestamp"])
                
                self.cache = cache_data
                self.logger.info(f"Loaded {len(self.cache)} cache entries from disk")
            except Exception as e:
                self.logger.error(f"Error loading cache: {e}")
                self.cache = {}
    
    def _save_cache(self):
        """Save cache to disk."""
        cache_file = os.path.join(self.cache_dir, "research_cache.json")
        
        try:
            # Convert datetime objects to ISO format strings for JSON serialization
            serializable_cache = {}
            for key, entry in self.cache.items():
                serializable_entry = entry.copy()
                if "timestamp" in serializable_entry and isinstance(serializable_entry["timestamp"], datetime):
                    serializable_entry["timestamp"] = serializable_entry["timestamp"].isoformat()
                serializable_cache[key] = serializable_entry
            
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(serializable_cache, f, indent=2)
            
            self.logger.info(f"Saved {len(self.cache)} cache entries to disk")
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key not in self.cache:
            return None
        
        cache_entry = self.cache[key]
        cache_age = (datetime.now() - cache_entry["timestamp"]).total_seconds()
        
        # Check if cache entry has expired
        ttl = cache_entry.get("ttl", self.default_ttl)
        if cache_age >= ttl:
            self.logger.info(f"Cache entry for {key} has expired")
            return None
        
        self.logger.info(f"Cache hit for {key}")
        return cache_entry["data"]
    
    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (optional)
        """
        self.cache[key] = {
            "timestamp": datetime.now(),
            "ttl": ttl if ttl is not None else self.default_ttl,
            "data": value
        }
        
        self.logger.info(f"Cache set for {key}")
        self._save_cache()
    
    def invalidate(self, key: str) -> None:
        """
        Invalidate a cache entry.
        
        Args:
            key: Cache key to invalidate
        """
        if key in self.cache:
            del self.cache[key]
            self.logger.info(f"Cache invalidated for {key}")
            self._save_cache()
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache = {}
        self.logger.info("Cache cleared")
        self._save_cache()
    
    def cleanup(self) -> None:
        """Remove expired cache entries."""
        keys_to_remove = []
        
        for key, entry in self.cache.items():
            cache_age = (datetime.now() - entry["timestamp"]).total_seconds()
            ttl = entry.get("ttl", self.default_ttl)
            
            if cache_age >= ttl:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
        
        if keys_to_remove:
            self.logger.info(f"Removed {len(keys_to_remove)} expired cache entries")
            self._save_cache()
