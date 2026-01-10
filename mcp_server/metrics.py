"""Metrics collection for monitoring and observability.

This module provides metrics collection capabilities for tracking
operation performance, cache statistics, and other system metrics.
"""

import time
from collections import defaultdict
from threading import Lock
from typing import Any, Dict, List

from .interfaces import IMetricsCollector


class MetricsCollector(IMetricsCollector):
    """Simple in-memory metrics collector.

    Collects and aggregates metrics for monitoring:
    - Operation duration and success/failure rates
    - Counter metrics (incremental values)
    - Gauge metrics (current values)

    Example:
        collector = MetricsCollector()

        # Record operation
        start = time.time()
        try:
            perform_operation()
            duration = (time.time() - start) * 1000
            collector.record_operation("load_pptx", duration, True)
        except Exception:
            duration = (time.time() - start) * 1000
            collector.record_operation("load_pptx", duration, False)

        # Increment counter
        collector.increment_counter("slides_processed", 10)

        # Record gauge
        collector.record_gauge("cache_size", 45)
    """

    def __init__(self):
        """Initialize metrics collector."""
        self._lock = Lock()

        # Operation metrics: {operation_name: {durations: [...], successes: int, failures: int}}
        self._operations: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"durations": [], "successes": 0, "failures": 0}
        )

        # Counter metrics: {metric_name: value}
        self._counters: Dict[str, int] = defaultdict(int)

        # Gauge metrics: {metric_name: value}
        self._gauges: Dict[str, float] = {}

        # Timestamp of last reset
        self._reset_time = time.time()

    def record_operation(self, operation: str, duration_ms: float, success: bool, **kwargs) -> None:
        """Record an operation metric.

        Args:
            operation: Operation name
            duration_ms: Operation duration in milliseconds
            success: Whether operation succeeded
            **kwargs: Additional attributes (for future extensions)
        """
        with self._lock:
            metrics = self._operations[operation]
            metrics["durations"].append(duration_ms)

            if success:
                metrics["successes"] += 1
            else:
                metrics["failures"] += 1

    def increment_counter(self, metric: str, value: int = 1, **kwargs) -> None:
        """Increment a counter metric.

        Args:
            metric: Metric name
            value: Increment value (default: 1)
            **kwargs: Additional attributes (for future extensions)
        """
        with self._lock:
            self._counters[metric] += value

    def record_gauge(self, metric: str, value: float, **kwargs) -> None:
        """Record a gauge metric.

        Args:
            metric: Metric name
            value: Gauge value
            **kwargs: Additional attributes (for future extensions)
        """
        with self._lock:
            self._gauges[metric] = value

    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics.

        Returns:
            Dictionary with all metrics including aggregations
        """
        with self._lock:
            # Calculate operation aggregations
            operations_summary = {}
            for operation, metrics in self._operations.items():
                durations = metrics["durations"]
                total_calls = metrics["successes"] + metrics["failures"]

                if durations:
                    avg_duration = sum(durations) / len(durations)
                    min_duration = min(durations)
                    max_duration = max(durations)
                    p95_duration = self._calculate_percentile(durations, 95)
                    p99_duration = self._calculate_percentile(durations, 99)
                else:
                    avg_duration = min_duration = max_duration = 0.0
                    p95_duration = p99_duration = 0.0

                success_rate = metrics["successes"] / total_calls if total_calls > 0 else 0.0

                operations_summary[operation] = {
                    "total_calls": total_calls,
                    "successes": metrics["successes"],
                    "failures": metrics["failures"],
                    "success_rate": success_rate,
                    "avg_duration_ms": avg_duration,
                    "min_duration_ms": min_duration,
                    "max_duration_ms": max_duration,
                    "p95_duration_ms": p95_duration,
                    "p99_duration_ms": p99_duration,
                }

            return {
                "operations": operations_summary,
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "collection_period_seconds": time.time() - self._reset_time,
            }

    def get_operation_metrics(self, operation: str) -> Dict[str, Any]:
        """Get metrics for a specific operation.

        Args:
            operation: Operation name

        Returns:
            Metrics for the operation
        """
        metrics = self.get_metrics()
        return metrics["operations"].get(operation, {})

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._operations.clear()
            self._counters.clear()
            self._gauges.clear()
            self._reset_time = time.time()

    @staticmethod
    def _calculate_percentile(values: List[float], percentile: int) -> float:
        """Calculate percentile of values.

        Args:
            values: List of values
            percentile: Percentile to calculate (0-100)

        Returns:
            Percentile value
        """
        if not values:
            return 0.0

        sorted_values = sorted(values)
        n = len(sorted_values)
        position = (percentile / 100.0) * (n - 1)
        index = int(position)
        index = max(0, min(index, n - 1))
        return sorted_values[index]


class NoOpMetricsCollector(IMetricsCollector):
    """No-op metrics collector that does nothing.

    Useful for disabling metrics collection without changing code.
    """

    def record_operation(self, operation: str, duration_ms: float, success: bool, **kwargs) -> None:
        """Record an operation metric (no-op)."""
        pass

    def increment_counter(self, metric: str, value: int = 1, **kwargs) -> None:
        """Increment a counter metric (no-op)."""
        pass

    def record_gauge(self, metric: str, value: float, **kwargs) -> None:
        """Record a gauge metric (no-op)."""
        pass

    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics (empty)."""
        return {
            "operations": {},
            "counters": {},
            "gauges": {},
            "collection_period_seconds": 0.0,
        }
