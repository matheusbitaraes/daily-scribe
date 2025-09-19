"""
Simple in-memory cache utility with TTL (Time To Live) support.

This module provides a lightweight caching solution for storing temporary data
with automatic expiration based on time-to-live configuration.
"""

import time
from typing import Dict, Any, Optional


class SimpleCache:
    """
    A simple in-memory cache with TTL (Time To Live) support.
    
    This cache stores key-value pairs with timestamps and automatically
    removes expired entries when accessed or during cleanup operations.
    
    Attributes:
        cache: Dictionary storing cached data with timestamps
        ttl_seconds: Time to live for cache entries in seconds
    """
    
    def __init__(self, ttl_seconds: int = 1800):
        """
        Initialize the cache with specified TTL.
        
        Args:
            ttl_seconds: Time to live for cache entries in seconds (default: 30 minutes)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        
        Args:
            key: The cache key to retrieve
            
        Returns:
            The cached value if found and not expired, None otherwise
        """
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl_seconds:
                return entry['data']
            else:
                # Remove expired entry
                del self.cache[key]
        return None
    
    def set(self, key: str, data: Any) -> None:
        """
        Store a value in the cache.
        
        Args:
            key: The cache key
            data: The data to cache
        """
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        self.cache.clear()
    
    def size(self) -> int:
        """
        Get the current number of entries in the cache.
        
        Returns:
            Number of cached entries
        """
        return len(self.cache)
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from the cache.
        
        Returns:
            Number of expired entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry['timestamp'] >= self.ttl_seconds
        ]
        for key in expired_keys:
            del self.cache[key]
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        current_time = time.time()
        expired_count = 0
        oldest_entry = None
        newest_entry = None
        
        for entry in self.cache.values():
            timestamp = entry['timestamp']
            if current_time - timestamp >= self.ttl_seconds:
                expired_count += 1
            
            if oldest_entry is None or timestamp < oldest_entry:
                oldest_entry = timestamp
            if newest_entry is None or timestamp > newest_entry:
                newest_entry = timestamp
        
        return {
            'total_entries': len(self.cache),
            'expired_entries': expired_count,
            'valid_entries': len(self.cache) - expired_count,
            'ttl_seconds': self.ttl_seconds,
            'oldest_entry_age': current_time - oldest_entry if oldest_entry else 0,
            'newest_entry_age': current_time - newest_entry if newest_entry else 0
        }