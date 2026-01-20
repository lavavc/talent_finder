"""Profile scraper orchestration."""

from gh_scraper.api.client import GitHubAPIError
from gh_scraper.api.graphql import GraphQLClient
from gh_scraper.api.rate_limiter import RateLimiter
from gh_scraper.api.rest import RestClient
from gh_scraper.config import Config
from gh_scraper.models import (
    ContributionStats,
    LanguageStats,
    UserProfile,
)
from gh_scraper.scoring import ScoringEngine


class ProfileScraper:
    """Orchestrates API calls to scrape complete user profiles."""

    def __init__(
        self,
        token: str | None = None,
        config: Config | None = None,
    ):
        """Initialize the profile scraper.

        Args:
            token: GitHub personal access token.
            config: Application configuration.
        """
        self.token = token
        self.config = config or Config()

        # Create shared rate limiter
        self.rate_limiter = RateLimiter(
            requests_per_hour=self.config.api.requests_per_hour,
            min_delay=self.config.api.delay_between_requests,
        )

        # Initialize API clients with shared rate limiter
        self.rest_client = RestClient(
            token=token,
            config=self.config.api,
            rate_limiter=self.rate_limiter,
        )
        self.graphql_client = GraphQLClient(
            token=token,
            config=self.config.api,
            rate_limiter=self.rate_limiter,
        )

        # Initialize scoring engine
        self.scoring_engine = ScoringEngine(config=self.config)

    def scrape_user(self, username: str) -> UserProfile:
        """Scrape complete profile data for a user.

        Args:
            username: GitHub username to scrape.

        Returns:
            UserProfile with all scraped and calculated data.
        """
        try:
            # 1. Get basic user profile
            user_data = self.rest_client.get_user(username)
            profile = UserProfile.from_api_response(user_data)

            # 2. Get user repositories
            repos = self.rest_client.get_user_repos(username)

            # Calculate total stars and forks
            profile.total_stars = sum(repo.stargazers_count for repo in repos)
            profile.total_forks = sum(repo.forks_count for repo in repos)

            # 3. Calculate language stats from repos
            profile.language_stats = LanguageStats.from_repos(repos)

            # 4. Get contribution data via GraphQL (requires token)
            if self.token:
                try:
                    calendar, contribution_counts = self.graphql_client.get_contributions(username)
                    profile.contribution_stats = ContributionStats.from_calendar(calendar)

                    # Calculate repos contributed to (unique repos across different activities)
                    profile.repos_contributed_to = max(
                        contribution_counts.get("repos_with_commits", 0),
                        contribution_counts.get("repos_with_prs", 0),
                        contribution_counts.get("repos_with_issues", 0),
                    )
                except GitHubAPIError:
                    # GraphQL might fail for some users, continue with REST data only
                    pass

            # 5. Calculate scores
            self.scoring_engine.calculate_scores(profile)

            return profile

        except GitHubAPIError as e:
            # Return profile with error information
            return UserProfile(
                username=username,
                error=str(e),
            )
        except Exception as e:
            return UserProfile(
                username=username,
                error=f"Unexpected error: {str(e)}",
            )

    def close(self) -> None:
        """Close all API clients."""
        self.rest_client.close()
        self.graphql_client.close()

    def __enter__(self) -> "ProfileScraper":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
