"""Caching implementation for MCP server.

This module provides caching capabilities with LRU eviction, TTL support,
and cache statistics tracking.
"""

import hashlib
import time
from collections import OrderedDict
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

from pptx import Presentation

from .config import get_config
from .interfaces import ICache


class LRUCache(ICache):
    """Thread-safe LRU (Least Recently Used) cache with TTL support.
    
    This cache implementation:
    - Evicts least recently used items when full
    - Supports optional time-to-live (TTL) for entries
    - Is thread-safe for concurrent access
    - Tracks hit/miss statistics
    
    Example:
        cache = LRUCache(maxsize=100)
        cache.set("key", value, ttl=3600)  # Cache for 1 hour
        value = cache.get("key")
    """
    
    def __init__(self, maxsize: Optional[int] = None, default_ttl: Optional[int] = None):
        """Initialize LRU cache.
        
        Args:
            maxsize: Maximum number of items. If None, uses config value.
            default_ttl: Default TTL in seconds. If None, uses config value.
        """
        config = get_config()
        self._maxsize = maxsize or config.performance.cache_size
        self._default_ttl = default_ttl or config.performance.cache_ttl
        
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = Lock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired.
        
        Args:
            entry: Cache entry with 'expires_at' field
            
        Returns:
            True if expired, False otherwise
        """
        expires_at = entry.get("expires_at")
        if expires_at is None:
            return False
        return time.time() > expires_at
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if self._is_expired(entry):
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live in seconds. If None, uses default.
        """
        with self._lock:
            # Calculate expiration
            if ttl is None:
                ttl = self._default_ttl
            
            expires_at = None if ttl is None else time.time() + ttl
            
            # Add/update entry
            if key in self._cache:
                # Update existing entry
                self._cache[key] = {
                    "value": value,
                    "expires_at": expires_at,
                    "created_at": time.time()
                }
                self._cache.move_to_end(key)
            else:
                # Add new entry
                self._cache[key] = {
                    "value": value,
                    "expires_at": expires_at,
                    "created_at": time.time()
                }
                
                # Evict if over capacity
                if len(self._cache) > self._maxsize:
                    self._cache.popitem(last=False)  # Remove oldest
                    self._evictions += 1
    
    def delete(self, key: str) -> None:
        """Delete value from cache.
        
        Args:
            key: Cache key
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                "size": len(self._cache),
                "maxsize": self._maxsize,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": hit_rate,
                "total_requests": total_requests
            }
    
    def cleanup_expired(self) -> int:
        """Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if self._is_expired(entry)
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)


class PresentationCache:
    """Specialized cache for PPTX Presentation objects.
    
    This cache uses file modification time and path as cache key,
    automatically invalidating entries when the file changes.
    
    Example:
        cache = PresentationCache()
        presentation = cache.get_presentation(path)
        if presentation is None:
            presentation = Presentation(path)
            cache.cache_presentation(path, presentation)
    """
    
    def __init__(self, cache: Optional[ICache] = None):
        """Initialize presentation cache.
        
        Args:
            cache: Optional cache implementation. If None, creates LRUCache.
        """
        self._cache = cache or LRUCache()
    
    def _get_cache_key(self, pptx_path: Path) -> str:
        """Generate cache key for PPTX file.
        
        Includes file path and modification time to auto-invalidate on changes.
        
        Args:
            pptx_path: Path to PPTX file
            
        Returns:
            Cache key string
        """
        if not pptx_path.exists():
            raise FileNotFoundError(f"PPTX file not found: {pptx_path}")
        
        mtime = pptx_path.stat().st_mtime
        key_str = f"{pptx_path}:{mtime}"
        
        # Use hash for shorter key (avoid MD5 to satisfy security tooling)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get_presentation(self, pptx_path: Path) -> Optional[Presentation]:
        """Get cached presentation.
        
        Args:
            pptx_path: Path to PPTX file
            
        Returns:
            Cached Presentation or None if not cached
        """
        try:
            cache_key = self._get_cache_key(pptx_path)
            return self._cache.get(cache_key)
        except FileNotFoundError:
            return None
    
    def cache_presentation(
        self,
        pptx_path: Path,
        presentation: Presentation,
        ttl: Optional[int] = None
    ) -> None:
        """Cache a presentation.
        
        Args:
            pptx_path: Path to PPTX file
            presentation: Presentation object to cache
            ttl: Optional time-to-live in seconds
        """
        try:
            cache_key = self._get_cache_key(pptx_path)
            self._cache.set(cache_key, presentation, ttl=ttl)
        except FileNotFoundError:
            # Can't cache if file doesn't exist
            pass
    
    def invalidate(self, pptx_path: Path) -> None:
        """Invalidate cached presentation for a file.
        
        Args:
            pptx_path: Path to PPTX file
        """
        try:
            cache_key = self._get_cache_key(pptx_path)
            self._cache.delete(cache_key)
        except FileNotFoundError:
            # If the file doesn't exist, there's nothing to invalidate
            pass
    
    def clear(self) -> None:
        """Clear all cached presentations."""
        self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return self._cache.get_stats()
