"""Rate limiter for GitHub API requests."""

import time
from threading import Lock


class RateLimiter:
    """Token bucket rate limiter for API requests.

    Implements a simple token bucket algorithm to respect GitHub's rate limits.
    """

    def __init__(self, requests_per_hour: int = 5000, min_delay: float = 0.75):
        """Initialize the rate limiter.

        Args:
            requests_per_hour: Maximum requests allowed per hour.
            min_delay: Minimum delay between requests in seconds.
        """
        self.requests_per_hour = requests_per_hour
        self.min_delay = min_delay
        self._last_request_time: float = 0.0
        self._lock = Lock()

        # Track remaining requests from API headers
        self._remaining: int | None = None
        self._reset_time: float | None = None

    def wait(self) -> None:
        """Wait if necessary to respect rate limits."""
        with self._lock:
            now = time.time()

            # Check if we're approaching rate limit based on API feedback
            if self._remaining is not None and self._remaining < 100:
                if self._reset_time and self._reset_time > now:
                    wait_time = self._reset_time - now + 1
                    time.sleep(wait_time)
                    return

            # Enforce minimum delay between requests
            elapsed = now - self._last_request_time
            if elapsed < self.min_delay:
                time.sleep(self.min_delay - elapsed)

            self._last_request_time = time.time()

    def update_from_headers(self, headers: dict[str, str]) -> None:
        """Update rate limit info from GitHub API response headers.

        Args:
            headers: Response headers from GitHub API.
        """
        with self._lock:
            if "x-ratelimit-remaining" in headers:
                self._remaining = int(headers["x-ratelimit-remaining"])
            if "x-ratelimit-reset" in headers:
                self._reset_time = float(headers["x-ratelimit-reset"])

    @property
    def remaining(self) -> int | None:
        """Get remaining requests, if known."""
        return self._remaining

    @property
    def reset_time(self) -> float | None:
        """Get rate limit reset time, if known."""
        return self._reset_time
