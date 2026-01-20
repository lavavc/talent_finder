"""REST API client for GitHub."""

from typing import Any

from gh_scraper.api.client import GitHubClient
from gh_scraper.api.rate_limiter import RateLimiter
from gh_scraper.config import APIConfig
from gh_scraper.models import Repository


class RestClient:
    """Client for GitHub REST API endpoints."""

    def __init__(
        self,
        token: str | None = None,
        config: APIConfig | None = None,
        rate_limiter: RateLimiter | None = None,
    ):
        """Initialize the REST client.

        Args:
            token: GitHub personal access token.
            config: API configuration.
            rate_limiter: Optional shared rate limiter.
        """
        self.client = GitHubClient(
            token=token,
            config=config,
            rate_limiter=rate_limiter,
        )

    def get_user(self, username: str) -> dict[str, Any]:
        """Get user profile data.

        Args:
            username: GitHub username.

        Returns:
            User profile data dictionary.
        """
        url = f"{self.client.REST_BASE_URL}/users/{username}"
        response = self.client.get(url)
        return response.json()

    def get_user_repos(
        self,
        username: str,
        per_page: int = 100,
        max_pages: int = 3,
    ) -> list[Repository]:
        """Get user's repositories with pagination.

        Args:
            username: GitHub username.
            per_page: Number of repos per page.
            max_pages: Maximum number of pages to fetch.

        Returns:
            List of Repository objects.
        """
        repos: list[Repository] = []
        page = 1

        while page <= max_pages:
            url = f"{self.client.REST_BASE_URL}/users/{username}/repos"
            params = {
                "per_page": per_page,
                "page": page,
                "sort": "updated",
                "type": "owner",
            }
            response = self.client.get(url, params=params)
            data = response.json()

            if not data:
                break

            for repo_data in data:
                repos.append(Repository.model_validate(repo_data))

            # Check if there are more pages
            if len(data) < per_page:
                break

            page += 1

        return repos

    def get_user_events(
        self,
        username: str,
        per_page: int = 100,
    ) -> list[dict[str, Any]]:
        """Get user's recent public events.

        Args:
            username: GitHub username.
            per_page: Number of events to fetch.

        Returns:
            List of event dictionaries.
        """
        url = f"{self.client.REST_BASE_URL}/users/{username}/events/public"
        params = {"per_page": per_page}
        response = self.client.get(url, params=params)
        return response.json()

    def get_repo_languages(
        self,
        owner: str,
        repo: str,
    ) -> dict[str, int]:
        """Get language breakdown for a repository.

        Args:
            owner: Repository owner.
            repo: Repository name.

        Returns:
            Dictionary mapping language names to bytes of code.
        """
        url = f"{self.client.REST_BASE_URL}/repos/{owner}/{repo}/languages"
        response = self.client.get(url)
        return response.json()

    def get_repo_contributors(
        self,
        owner: str,
        repo: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get top contributors for a repository (sorted by contributions).

        Args:
            owner: Repository owner.
            repo: Repository name.
            limit: Maximum number of contributors to return.

        Returns:
            List of contributor data dictionaries (most active first).
        """
        contributors: list[dict[str, Any]] = []
        page = 1
        per_page = min(100, limit)

        while len(contributors) < limit:
            url = f"{self.client.REST_BASE_URL}/repos/{owner}/{repo}/contributors"
            params = {"per_page": per_page, "page": page}
            response = self.client.get(url, params=params)
            data = response.json()

            if not data or not isinstance(data, list):
                break

            contributors.extend(data)

            if len(data) < per_page:
                break

            page += 1

        return contributors[:limit]

    def get_user_followers(
        self,
        username: str,
        per_page: int = 100,
        max_pages: int = 5,
    ) -> list[dict[str, Any]]:
        """Get followers of a user.

        Args:
            username: GitHub username.
            per_page: Number of followers per page.
            max_pages: Maximum pages to fetch.

        Returns:
            List of follower data dictionaries.
        """
        followers: list[dict[str, Any]] = []
        page = 1

        while page <= max_pages:
            url = f"{self.client.REST_BASE_URL}/users/{username}/followers"
            params = {"per_page": per_page, "page": page}
            response = self.client.get(url, params=params)
            data = response.json()

            if not data or not isinstance(data, list):
                break

            followers.extend(data)

            if len(data) < per_page:
                break

            page += 1

        return followers

    def get_user_repos_by_stars(
        self,
        username: str,
        limit: int = 10,
    ) -> list[Repository]:
        """Get user's top repositories sorted by stars.

        Args:
            username: GitHub username.
            limit: Maximum number of repos to return.

        Returns:
            List of Repository objects sorted by stars descending.
        """
        repos = self.get_user_repos(username, per_page=100, max_pages=3)
        # Sort by stars and return top N
        repos.sort(key=lambda r: r.stargazers_count, reverse=True)
        return repos[:limit]

    def close(self) -> None:
        """Close the client."""
        self.client.close()

    def __enter__(self) -> "RestClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
