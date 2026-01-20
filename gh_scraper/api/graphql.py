"""GraphQL API client for GitHub contributions."""

from typing import Any

from gh_scraper.api.client import GitHubAPIError, GitHubClient
from gh_scraper.api.rate_limiter import RateLimiter
from gh_scraper.config import APIConfig
from gh_scraper.models import ContributionCalendar, ContributionDay, ContributionWeek


CONTRIBUTION_QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalRepositoriesWithContributedCommits
      totalRepositoriesWithContributedIssues
      totalRepositoriesWithContributedPullRequests
      totalRepositoriesWithContributedPullRequestReviews
    }
  }
}
"""


class GraphQLClient:
    """Client for GitHub GraphQL API."""

    def __init__(
        self,
        token: str | None = None,
        config: APIConfig | None = None,
        rate_limiter: RateLimiter | None = None,
    ):
        """Initialize the GraphQL client.

        Args:
            token: GitHub personal access token (required for GraphQL).
            config: API configuration.
            rate_limiter: Optional shared rate limiter.
        """
        self.client = GitHubClient(
            token=token,
            config=config,
            rate_limiter=rate_limiter,
        )

    def execute(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GraphQL query.

        Args:
            query: GraphQL query string.
            variables: Query variables.

        Returns:
            Query response data.

        Raises:
            GitHubAPIError: If the query fails.
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = self.client.post(
            self.client.GRAPHQL_URL,
            json=payload,
        )
        data = response.json()

        if "errors" in data:
            error_msg = "; ".join(e.get("message", str(e)) for e in data["errors"])
            raise GitHubAPIError(f"GraphQL error: {error_msg}")

        return data.get("data", {})

    def get_contributions(self, username: str) -> tuple[ContributionCalendar, dict[str, int]]:
        """Get user's contribution data.

        Args:
            username: GitHub username.

        Returns:
            Tuple of (ContributionCalendar, contribution_counts dict).

        Raises:
            GitHubAPIError: If the user is not found or query fails.
        """
        data = self.execute(CONTRIBUTION_QUERY, {"username": username})

        user_data = data.get("user")
        if not user_data:
            raise GitHubAPIError(f"User not found: {username}", status_code=404)

        collection = user_data.get("contributionsCollection", {})
        calendar_data = collection.get("contributionCalendar", {})

        # Parse contribution calendar
        weeks = []
        for week_data in calendar_data.get("weeks", []):
            days = [
                ContributionDay(
                    date=day["date"],
                    contributionCount=day["contributionCount"],
                )
                for day in week_data.get("contributionDays", [])
            ]
            weeks.append(ContributionWeek(contributionDays=days))

        calendar = ContributionCalendar(
            totalContributions=calendar_data.get("totalContributions", 0),
            weeks=weeks,
        )

        # Extract additional contribution counts
        contribution_counts = {
            "commits": collection.get("totalCommitContributions", 0),
            "issues": collection.get("totalIssueContributions", 0),
            "pull_requests": collection.get("totalPullRequestContributions", 0),
            "reviews": collection.get("totalPullRequestReviewContributions", 0),
            "repos_with_commits": collection.get("totalRepositoriesWithContributedCommits", 0),
            "repos_with_issues": collection.get("totalRepositoriesWithContributedIssues", 0),
            "repos_with_prs": collection.get("totalRepositoriesWithContributedPullRequests", 0),
            "repos_with_reviews": collection.get(
                "totalRepositoriesWithContributedPullRequestReviews", 0
            ),
        }

        return calendar, contribution_counts

    def close(self) -> None:
        """Close the client."""
        self.client.close()

    def __enter__(self) -> "GraphQLClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
