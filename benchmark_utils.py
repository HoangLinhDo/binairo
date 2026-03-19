"""
Benchmark utilities for measuring solver performance.
Provides decorators and context managers for timing and memory measurement.
"""

import time
import tracemalloc
import gc
from dataclasses import dataclass
from typing import Callable, Any, Optional, Tuple, Dict
from functools import wraps


@dataclass
class PerformanceStats:
    """Container for performance statistics."""
    time_seconds: float
    memory_current_mb: float
    memory_peak_mb: float
    success: bool = True
    result: Any = None
    error: Optional[str] = None

    def __str__(self) -> str:
        status = "Success" if self.success else f"Failed: {self.error}"
        return (
            f"Performance Stats:\n"
            f"  Status: {status}\n"
            f"  Time: {self.time_seconds:.4f}s\n"
            f"  Memory (current): {self.memory_current_mb:.2f} MB\n"
            f"  Memory (peak): {self.memory_peak_mb:.2f} MB"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'time_seconds': self.time_seconds,
            'memory_current_mb': self.memory_current_mb,
            'memory_peak_mb': self.memory_peak_mb,
            'success': self.success,
            'error': self.error
        }


class PerformanceMonitor:
    """
    Context manager for measuring performance.

    Usage:
        with PerformanceMonitor() as pm:
            result = some_function()
        print(pm.stats)
    """

    def __init__(self, gc_before: bool = True):
        """
        Initialize the performance monitor.

        Args:
            gc_before: Whether to run garbage collection before measurement
        """
        self.gc_before = gc_before
        self.stats: Optional[PerformanceStats] = None
        self._start_time = 0
        self._result = None

    def __enter__(self) -> 'PerformanceMonitor':
        if self.gc_before:
            gc.collect()

        tracemalloc.start()
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        elapsed = end_time - self._start_time
        success = exc_type is None
        error = str(exc_val) if exc_val else None

        self.stats = PerformanceStats(
            time_seconds=elapsed,
            memory_current_mb=current / (1024 * 1024),
            memory_peak_mb=peak / (1024 * 1024),
            success=success,
            result=self._result,
            error=error
        )

        # Don't suppress exceptions
        return False

    def set_result(self, result: Any):
        """Store the result for later access."""
        self._result = result
        if self.stats:
            self.stats.result = result


def measure_performance(func: Callable, *args, **kwargs) -> Tuple[Any, PerformanceStats]:
    """
    Measure the performance of a function call.

    Args:
        func: Function to call
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        Tuple of (result, PerformanceStats)
    """
    gc.collect()
    tracemalloc.start()

    start_time = time.perf_counter()
    error = None
    result = None

    try:
        result = func(*args, **kwargs)
        success = True
    except Exception as e:
        success = False
        error = str(e)

    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    stats = PerformanceStats(
        time_seconds=end_time - start_time,
        memory_current_mb=current / (1024 * 1024),
        memory_peak_mb=peak / (1024 * 1024),
        success=success,
        result=result,
        error=error
    )

    return result, stats


def timed(func: Callable) -> Callable:
    """
    Decorator to time a function and print results.

    Usage:
        @timed
        def my_function():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end - start:.4f}s")
        return result
    return wrapper


def profiled(func: Callable) -> Callable:
    """
    Decorator to profile a function (time + memory).

    Usage:
        @profiled
        def my_function():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result, stats = measure_performance(func, *args, **kwargs)
        print(f"{func.__name__}:")
        print(f"  Time: {stats.time_seconds:.4f}s")
        print(f"  Memory (peak): {stats.memory_peak_mb:.2f} MB")
        return result
    return wrapper


class Timer:
    """
    Simple timer for measuring elapsed time.

    Usage:
        timer = Timer()
        timer.start()
        # ... do work ...
        elapsed = timer.stop()
    """

    def __init__(self):
        self._start_time: Optional[float] = None
        self._elapsed: float = 0

    def start(self):
        """Start the timer."""
        self._start_time = time.perf_counter()

    def stop(self) -> float:
        """Stop the timer and return elapsed time."""
        if self._start_time is None:
            return 0
        self._elapsed = time.perf_counter() - self._start_time
        self._start_time = None
        return self._elapsed

    @property
    def elapsed(self) -> float:
        """Get elapsed time (either stopped or running)."""
        if self._start_time is not None:
            return time.perf_counter() - self._start_time
        return self._elapsed

    def reset(self):
        """Reset the timer."""
        self._start_time = None
        self._elapsed = 0


def format_time(seconds: float) -> str:
    """Format time for display."""
    if seconds < 0.001:
        return f"{seconds * 1000000:.2f} μs"
    elif seconds < 1:
        return f"{seconds * 1000:.2f} ms"
    elif seconds < 60:
        return f"{seconds:.3f} s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"


def format_memory(mb: float) -> str:
    """Format memory for display."""
    if mb < 1:
        return f"{mb * 1024:.2f} KB"
    elif mb < 1024:
        return f"{mb:.2f} MB"
    else:
        return f"{mb / 1024:.2f} GB"


if __name__ == "__main__":
    # Test the utilities
    import random

    def test_function(n: int):
        """A function that takes some time and memory."""
        data = [random.random() for _ in range(n)]
        sorted_data = sorted(data)
        return sum(sorted_data)

    print("Testing measure_performance:")
    result, stats = measure_performance(test_function, 1000000)
    print(stats)
    print(f"Result: {result:.4f}")
    print()

    print("Testing PerformanceMonitor context manager:")
    with PerformanceMonitor() as pm:
        result = test_function(500000)
    print(pm.stats)
    print()

    print("Testing timed decorator:")
    @timed
    def quick_sort_test():
        return test_function(100000)

    quick_sort_test()
