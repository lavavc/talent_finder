"""Base HTTP client for GitHub API."""

import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from gh_scraper.api.rate_limiter import RateLimiter
from gh_scraper.config import APIConfig


class GitHubAPIError(Exception):
    """Exception raised for GitHub API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class GitHubClient:
    """Base HTTP client for GitHub API with authentication and rate limiting."""

    REST_BASE_URL = "https://api.github.com"
    GRAPHQL_URL = "https://api.github.com/graphql"

    def __init__(
        self,
        token: str | None = None,
        config: APIConfig | None = None,
        rate_limiter: RateLimiter | None = None,
    ):
        """Initialize the GitHub client.

        Args:
            token: GitHub personal access token.
            config: API configuration.
            rate_limiter: Optional shared rate limiter instance.
        """
        self.token = token
        self.config = config or APIConfig()

        if rate_limiter is not None:
            self.rate_limiter = rate_limiter
        else:
            self.rate_limiter = RateLimiter(
                requests_per_hour=self.config.requests_per_hour,
                min_delay=self.config.delay_between_requests,
            )

        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()

        # Set up retries
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        # Set headers
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "gh-scraper/0.1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        session.headers.update(headers)

        return session

    def _request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> requests.Response:
        """Make an HTTP request with rate limiting.

        Args:
            method: HTTP method.
            url: Request URL.
            **kwargs: Additional arguments to pass to requests.

        Returns:
            Response object.

        Raises:
            GitHubAPIError: If the request fails.
        """
        self.rate_limiter.wait()

        kwargs.setdefault("timeout", self.config.timeout)

        response = self.session.request(method, url, **kwargs)

        # Update rate limiter from response headers
        self.rate_limiter.update_from_headers(dict(response.headers))

        if response.status_code == 404:
            raise GitHubAPIError(f"Not found: {url}", status_code=404)
        elif response.status_code == 403:
            # Check if it's a rate limit error
            if "rate limit" in response.text.lower():
                # Wait for rate limit reset
                reset_time = self.rate_limiter.reset_time
                if reset_time:
                    wait_time = max(0, reset_time - time.time()) + 1
                    time.sleep(wait_time)
                    return self._request(method, url, **kwargs)
            raise GitHubAPIError(f"Forbidden: {response.text}", status_code=403)
        elif response.status_code >= 400:
            raise GitHubAPIError(
                f"API error ({response.status_code}): {response.text}",
                status_code=response.status_code,
            )

        return response

    def get(self, url: str, **kwargs) -> requests.Response:
        """Make a GET request."""
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """Make a POST request."""
        return self._request("POST", url, **kwargs)

    def close(self) -> None:
        """Close the session."""
        self.session.close()

    def __enter__(self) -> "GitHubClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
