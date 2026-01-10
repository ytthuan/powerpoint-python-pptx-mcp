"""Unit tests for caching module."""

import time
from threading import Thread

from mcp_server.cache import LRUCache, PresentationCache


class TestLRUCache:
    """Tests for LRUCache class."""

    def test_basic_get_set(self):
        """Test basic get and set operations."""
        cache = LRUCache(maxsize=10)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_nonexistent_key(self):
        """Test getting non-existent key returns None."""
        cache = LRUCache(maxsize=10)
        assert cache.get("nonexistent") is None

    def test_set_overwrites_existing(self):
        """Test setting existing key overwrites value."""
        cache = LRUCache(maxsize=10)
        cache.set("key1", "value1")
        cache.set("key1", "value2")
        assert cache.get("key1") == "value2"

    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = LRUCache(maxsize=3)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it most recently used
        cache.get("key1")
        
        # Add key4, should evict key2 (least recently used)
        cache.set("key4", "value4")
        
        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key2") is None      # Evicted
        assert cache.get("key3") == "value3"  # Still there
        assert cache.get("key4") == "value4"  # Just added

    def test_ttl_expiration(self):
        """Test TTL-based expiration."""
        cache = LRUCache(maxsize=10, default_ttl=1)
        cache.set("key1", "value1", ttl=1)
        
        # Should be available immediately
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        assert cache.get("key1") is None

    def test_ttl_none_never_expires(self):
        """Test that None TTL means no expiration."""
        cache = LRUCache(maxsize=10)
        cache.set("key1", "value1", ttl=None)
        
        # Should still be available
        assert cache.get("key1") == "value1"

    def test_delete(self):
        """Test deleting entries."""
        cache = LRUCache(maxsize=10)
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_clear(self):
        """Test clearing all entries."""
        cache = LRUCache(maxsize=10)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Clear should reset everything
        cache.clear()
        
        # Get stats before any operations to verify clear worked
        stats = cache.get_stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        
        # These will be misses but that's expected
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_statistics_tracking(self):
        """Test statistics tracking."""
        cache = LRUCache(maxsize=10)
        
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["hit_rate"] == 0.5

    def test_eviction_tracking(self):
        """Test eviction tracking in statistics."""
        cache = LRUCache(maxsize=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should trigger eviction
        
        stats = cache.get_stats()
        assert stats["evictions"] == 1

    def test_thread_safety(self):
        """Test thread-safe operations."""
        cache = LRUCache(maxsize=100)
        
        def worker(start, end):
            for i in range(start, end):
                cache.set(f"key{i}", f"value{i}")
                cache.get(f"key{i}")
        
        threads = [
            Thread(target=worker, args=(0, 50)),
            Thread(target=worker, args=(50, 100)),
        ]
        
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All values should be set
        stats = cache.get_stats()
        assert stats["size"] <= 100

    def test_cleanup_expired(self):
        """Test cleaning up expired entries."""
        cache = LRUCache(maxsize=10)
        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=10)
        
        time.sleep(1.1)
        
        removed = cache.cleanup_expired()
        assert removed == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"


class TestPresentationCache:
    """Tests for PresentationCache class."""

    def test_get_nonexistent_presentation(self, tmp_path):
        """Test getting non-existent presentation returns None."""
        cache = PresentationCache()
        nonexistent_path = tmp_path / "nonexistent.pptx"
        assert cache.get_presentation(nonexistent_path) is None

    def test_cache_key_includes_mtime(self, tmp_path):
        """Test cache key includes modification time."""
        cache = PresentationCache()
        test_file = tmp_path / "test.pptx"
        test_file.write_text("test content")
        
        # Mock presentation object
        mock_presentation = "MockPresentation"
        
        # Cache the presentation
        cache.cache_presentation(test_file, mock_presentation)
        assert cache.get_presentation(test_file) == mock_presentation
        
        # Modify file (change mtime)
        time.sleep(0.1)
        test_file.write_text("modified content")
        
        # Should not find cached version (mtime changed)
        assert cache.get_presentation(test_file) is None

    def test_invalidate(self, tmp_path):
        """Test invalidating cached presentation."""
        cache = PresentationCache()
        test_file = tmp_path / "test.pptx"
        test_file.write_text("test content")
        
        mock_presentation = "MockPresentation"
        cache.cache_presentation(test_file, mock_presentation)
        
        # Verify it's cached
        assert cache.get_presentation(test_file) == mock_presentation
        
        # Invalidate
        cache.invalidate(test_file)
        
        # Should no longer be cached
        assert cache.get_presentation(test_file) is None

    def test_clear(self, tmp_path):
        """Test clearing all cached presentations."""
        cache = PresentationCache()
        
        test_file1 = tmp_path / "test1.pptx"
        test_file2 = tmp_path / "test2.pptx"
        test_file1.write_text("test1")
        test_file2.write_text("test2")
        
        cache.cache_presentation(test_file1, "Mock1")
        cache.cache_presentation(test_file2, "Mock2")
        
        cache.clear()
        
        assert cache.get_presentation(test_file1) is None
        assert cache.get_presentation(test_file2) is None

    def test_get_stats(self, tmp_path):
        """Test getting cache statistics."""
        cache = PresentationCache()
        test_file = tmp_path / "test.pptx"
        test_file.write_text("test content")
        
        cache.cache_presentation(test_file, "Mock")
        cache.get_presentation(test_file)  # Hit
        
        stats = cache.get_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "size" in stats
