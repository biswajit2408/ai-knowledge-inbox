import time


def elapsed_ms(start: float) -> float:
    """Milliseconds since `start` (a time.perf_counter() value), rounded for logs."""
    return round((time.perf_counter() - start) * 1000, 2)
