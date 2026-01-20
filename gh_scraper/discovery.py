"""Discovery module for finding collaborators and followers."""

from typing import Callable

from gh_scraper.api.client import GitHubAPIError
from gh_scraper.api.graphql import GraphQLClient
from gh_scraper.api.rate_limiter import RateLimiter
from gh_scraper.api.rest import RestClient
from gh_scraper.config import Config
from gh_scraper.models import UserProfile
from gh_scraper.scoring import ScoringEngine


class NetworkDiscovery:
    """Discovers new users through collaborators and followers."""

    def __init__(
        self,
        token: str | None = None,
        config: Config | None = None,
    ):
        """Initialize the discovery engine.

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

        # Initialize API clients
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

        self.scoring_engine = ScoringEngine(config=self.config)

    def discover_collaborators(
        self,
        seed_usernames: list[str],
        top_repos: int = 10,
        max_contributors: int = 30,
        progress_callback: Callable[[str, str], None] | None = None,
    ) -> dict[str, list[str]]:
        """Discover collaborators from seed users' top repositories.

        Args:
            seed_usernames: List of seed GitHub usernames.
            top_repos: Number of top repos (by stars) to check per user.
            max_contributors: Maximum contributors to fetch per repo (most active first).
            progress_callback: Optional callback(username, status) for progress updates.

        Returns:
            Dict mapping discovered username -> list of source usernames they collaborated with.
        """
        discovered: dict[str, list[str]] = {}
        seed_set = set(u.lower() for u in seed_usernames)

        for username in seed_usernames:
            if progress_callback:
                progress_callback(username, "Finding top repos...")

            try:
                # Get top repos by stars
                repos = self.rest_client.get_user_repos_by_stars(username, limit=top_repos)

                for repo in repos:
                    if progress_callback:
                        progress_callback(username, f"Checking {repo.name}...")

                    try:
                        # Get top contributors for this repo
                        contributors = self.rest_client.get_repo_contributors(
                            owner=username,
                            repo=repo.name,
                            limit=max_contributors,
                        )

                        for contrib in contributors:
                            contrib_username = contrib.get("login", "")
                            if not contrib_username:
                                continue

                            # Skip if it's a seed user or bot
                            if contrib_username.lower() in seed_set:
                                continue
                            if "[bot]" in contrib_username:
                                continue

                            # Track the discovery
                            if contrib_username not in discovered:
                                discovered[contrib_username] = []
                            if username not in discovered[contrib_username]:
                                discovered[contrib_username].append(username)

                    except GitHubAPIError:
                        # Skip repos we can't access
                        continue

            except GitHubAPIError as e:
                if progress_callback:
                    progress_callback(username, f"Error: {e}")
                continue

        return discovered

    def discover_followers(
        self,
        seed_usernames: list[str],
        depth: int = 1,
        max_followers_per_user: int = 500,
        progress_callback: Callable[[str, str], None] | None = None,
    ) -> dict[str, list[str]]:
        """Discover followers from seed users.

        Args:
            seed_usernames: List of seed GitHub usernames.
            depth: Network depth (1 = direct followers, 2 = followers of followers, etc.)
            max_followers_per_user: Max followers to fetch per user.
            progress_callback: Optional callback(username, status) for progress updates.

        Returns:
            Dict mapping discovered username -> list of source usernames they follow.
        """
        discovered: dict[str, list[str]] = {}
        seed_set = set(u.lower() for u in seed_usernames)
        current_level = list(seed_usernames)
        seen_users: set[str] = set(seed_set)

        for current_depth in range(depth):
            next_level: list[str] = []

            for username in current_level:
                if progress_callback:
                    progress_callback(username, f"Depth {current_depth + 1}: Getting followers...")

                try:
                    # Calculate max pages based on max_followers_per_user
                    max_pages = (max_followers_per_user // 100) + 1

                    followers = self.rest_client.get_user_followers(
                        username=username,
                        per_page=100,
                        max_pages=max_pages,
                    )

                    for follower in followers[:max_followers_per_user]:
                        follower_username = follower.get("login", "")
                        if not follower_username:
                            continue

                        follower_lower = follower_username.lower()

                        # Skip bots
                        if "[bot]" in follower_username:
                            continue

                        # Track the discovery (even if seed, we track the relationship)
                        if follower_lower not in seed_set:
                            if follower_username not in discovered:
                                discovered[follower_username] = []
                            if username not in discovered[follower_username]:
                                discovered[follower_username].append(username)

                        # Add to next level if not seen and we need more depth
                        if follower_lower not in seen_users and current_depth < depth - 1:
                            next_level.append(follower_username)
                            seen_users.add(follower_lower)

                except GitHubAPIError as e:
                    if progress_callback:
                        progress_callback(username, f"Error: {e}")
                    continue

            current_level = next_level

        return discovered

    def scrape_user(self, username: str) -> UserProfile:
        """Scrape complete profile data for a user.

        Args:
            username: GitHub username to scrape.

        Returns:
            UserProfile with all scraped and calculated data.
        """
        from gh_scraper.models import ContributionStats, LanguageStats

        try:
            # Get basic user profile
            user_data = self.rest_client.get_user(username)
            profile = UserProfile.from_api_response(user_data)

            # Get user repositories
            repos = self.rest_client.get_user_repos(username)

            # Calculate totals
            profile.total_stars = sum(repo.stargazers_count for repo in repos)
            profile.total_forks = sum(repo.forks_count for repo in repos)

            # Calculate language stats
            profile.language_stats = LanguageStats.from_repos(repos)

            # Get contribution data via GraphQL
            if self.token:
                try:
                    calendar, contribution_counts = self.graphql_client.get_contributions(username)
                    profile.contribution_stats = ContributionStats.from_calendar(calendar)
                    profile.repos_contributed_to = max(
                        contribution_counts.get("repos_with_commits", 0),
                        contribution_counts.get("repos_with_prs", 0),
                        contribution_counts.get("repos_with_issues", 0),
                    )
                except GitHubAPIError:
                    pass

            # Calculate scores
            self.scoring_engine.calculate_scores(profile)

            return profile

        except GitHubAPIError as e:
            return UserProfile(username=username, error=str(e))
        except Exception as e:
            return UserProfile(username=username, error=f"Unexpected error: {str(e)}")

    def close(self) -> None:
        """Close all API clients."""
        self.rest_client.close()
        self.graphql_client.close()

    def __enter__(self) -> "NetworkDiscovery":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
