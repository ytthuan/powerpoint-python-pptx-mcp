"""Performance benchmarks for MCP server components."""

import time

import pytest

from mcp_server.cache import LRUCache
from mcp_server.config import get_config, reset_config


@pytest.mark.benchmark
class TestCachePerformance:
    """Benchmark tests for cache performance."""

    def test_cache_write_performance(self, benchmark):
        """Benchmark cache write operations."""
        cache = LRUCache(maxsize=1000)

        def write_ops():
            for i in range(100):
                cache.set(f"key{i}", f"value{i}")

        benchmark(write_ops)

    def test_cache_read_performance(self, benchmark):
        """Benchmark cache read operations."""
        cache = LRUCache(maxsize=1000)
        for i in range(100):
            cache.set(f"key{i}", f"value{i}")

        def read_ops():
            for i in range(100):
                cache.get(f"key{i}")

        benchmark(read_ops)

    def test_cache_hit_rate(self):
        """Test cache hit rate under load."""
        cache = LRUCache(maxsize=100)

        # Populate cache
        for i in range(100):
            cache.set(f"key{i}", f"value{i}")

        # Access pattern: 80% hits, 20% misses
        for _ in range(1000):
            for i in range(80):
                cache.get(f"key{i}")  # Hit
            for i in range(100, 120):
                cache.get(f"key{i}")  # Miss

        stats = cache.get_stats()
        print(f"\nCache hit rate: {stats['hit_rate']:.2%}")
        assert stats["hit_rate"] > 0.75  # Should be around 80%


@pytest.mark.benchmark
class TestConfigPerformance:
    """Benchmark tests for configuration loading."""

    def test_config_load_performance(self, benchmark):
        """Benchmark configuration loading."""

        def load_config():
            reset_config()
            return get_config()

        benchmark(load_config)

    def test_config_access_performance(self, benchmark):
        """Benchmark configuration access."""
        reset_config()
        config = get_config()

        def access_config():
            _ = config.security.max_file_size
            _ = config.performance.enable_cache
            _ = config.logging.level

        benchmark(access_config)


def run_performance_report():
    """Generate a performance report."""
    print("\n" + "=" * 70)
    print("PERFORMANCE BENCHMARK REPORT")
    print("=" * 70)

    # Cache performance
    print("\n📊 Cache Performance:")
    cache = LRUCache(maxsize=1000)

    start = time.time()
    for i in range(1000):
        cache.set(f"key{i}", f"value{i}")
    write_time = time.time() - start
    print(f"   Write 1000 items: {write_time:.4f}s ({1000/write_time:.0f} ops/sec)")

    start = time.time()
    for i in range(1000):
        cache.get(f"key{i}")
    read_time = time.time() - start
    print(f"   Read 1000 items: {read_time:.4f}s ({1000/read_time:.0f} ops/sec)")

    stats = cache.get_stats()
    print(f"   Hit rate: {stats['hit_rate']:.2%}")

    # Config performance
    print("\n⚙️  Configuration Performance:")
    start = time.time()
    for _ in range(100):
        reset_config()
        get_config()
    config_time = time.time() - start
    print(f"   Load config 100 times: {config_time:.4f}s ({100/config_time:.0f} ops/sec)")

    print("\n" + "=" * 70)
    print("✅ Benchmark complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_performance_report()
