# app/circuit.py
import time
from functools import wraps


class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=30):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = {}
        self.state = {}

    def call(self, backend_name: str, func, *args, **kwargs):
        now = time.time()
        if backend_name in self.state and self.state[backend_name] == "open":
            if now - self.failures.get(backend_name, 0) > self.reset_timeout:
                self.state[backend_name] = "half-open"
            else:
                raise Exception(f"Circuit breaker open for {backend_name}")

        try:
            result = func(*args, **kwargs)
            if self.state.get(backend_name) == "half-open":
                self.state[backend_name] = "closed"
            return result
        except Exception as e:
            self.failures[backend_name] = now
            if self.failures.get(backend_name, 0) >= self.failure_threshold:
                self.state[backend_name] = "open"
            raise e

    async def call_async(self, backend_name: str, coro_func, *args, **kwargs):
        # Addition beyond the lesson's own code block: `call()` above invokes
        # `func` synchronously, but every backend in app/backends.py is
        # async. This mirrors the same open/half-open/closed bookkeeping for
        # an awaitable, since the lesson never shows how the breaker is
        # actually wired into the (async) call path.
        now = time.time()
        if backend_name in self.state and self.state[backend_name] == "open":
            if now - self.failures.get(backend_name, 0) > self.reset_timeout:
                self.state[backend_name] = "half-open"
            else:
                raise Exception(f"Circuit breaker open for {backend_name}")

        try:
            result = await coro_func(*args, **kwargs)
            if self.state.get(backend_name) == "half-open":
                self.state[backend_name] = "closed"
            return result
        except Exception as e:
            self.failures[backend_name] = now
            if self.failures.get(backend_name, 0) >= self.failure_threshold:
                self.state[backend_name] = "open"
            raise e


# Single shared instance used by app/server.py around every backend call.
breaker = CircuitBreaker()
