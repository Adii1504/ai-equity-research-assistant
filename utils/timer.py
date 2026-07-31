"""
utils/timer.py
--------------
Context manager for measuring latency of any block.
This is how we get the benchmark numbers that go on the resume.

Usage:
    with Timer() as t:
        result = fetch_something()
    print(f"Took {t.elapsed_ms:.1f}ms")
"""

import time
from utils.logger import get_logger

logger = get_logger(__name__)


class Timer:
    """
    Context manager that measures wall-clock time in milliseconds.

    Example:
        with Timer() as t:
            do_work()
        print(t.elapsed_ms)   # e.g. 312.4
    """

    def __init__(self, label: str = ""):
        self.label      = label
        self.elapsed_ms = 0.0
        self._start     = 0.0

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000
        if self.label:
            logger.debug("%s completed in %.1f ms", self.label, self.elapsed_ms)
