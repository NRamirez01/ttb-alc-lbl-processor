import time


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        self.elapsed_ms = 0
        return self

    def __exit__(self, exc_type, exc, tb):
        self.elapsed_ms = int((time.perf_counter() - self.start) * 1000)