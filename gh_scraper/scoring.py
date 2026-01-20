"""Scoring engine with configurable weights."""

import math

from gh_scraper.config import Config
from gh_scraper.models import UserProfile


class ScoringEngine:
    """Calculates scores for GitHub profiles using configurable weights."""

    def __init__(self, config: Config | None = None):
        """Initialize the scoring engine.

        Args:
            config: Application configuration with scoring weights.
        """
        self.config = config or Config()

    def normalize_log(self, value: float, max_value: float) -> float:
        """Normalize a value using logarithmic scaling.

        Args:
            value: The value to normalize.
            max_value: The maximum expected value for full score.

        Returns:
            Normalized value between 0 and 1.
        """
        if value <= 0:
            return 0.0
        if max_value <= 0:
            return 0.0

        # Use log scaling to handle large ranges
        # log(1 + x) to handle x=0 case
        log_value = math.log(1 + value)
        log_max = math.log(1 + max_value)

        return min(1.0, log_value / log_max)

    def calculate_language_score(self, profile: UserProfile) -> float:
        """Calculate language score based on top languages.

        Args:
            profile: User profile with language stats.

        Returns:
            Language score between 0 and 1.
        """
        if not profile.language_stats.languages:
            return 0.0

        total_bytes = sum(profile.language_stats.languages.values())
        if total_bytes == 0:
            return 0.0

        weighted_sum = 0.0
        for lang, bytes_count in profile.language_stats.languages.items():
            weight = self.config.languages.get_weight(lang)
            proportion = bytes_count / total_bytes
            weighted_sum += weight * proportion

        # Normalize to 0-1 range (max possible is ~2.0 for all Solidity/Rust)
        return min(1.0, weighted_sum / 2.0)

    def calculate_activity_score(self, profile: UserProfile) -> float:
        """Calculate activity score from contribution stats.

        Args:
            profile: User profile with contribution stats.

        Returns:
            Activity score between 0 and 1.
        """
        stats = profile.contribution_stats

        # Combine multiple activity metrics
        contribution_norm = self.normalize_log(
            stats.total_contributions,
            self.config.scoring.max_contributions,
        )

        # Activity density (contributions per day over the year)
        density_norm = min(1.0, stats.activity_density / 5.0)  # 5+ contributions/day is max

        # Active days proportion
        active_days_norm = min(1.0, stats.active_days / 200.0)  # 200+ active days is max

        # Streak bonus
        streak_norm = min(1.0, stats.longest_streak / 30.0)  # 30+ day streak is max

        # Weighted combination
        return (
            contribution_norm * 0.4
            + density_norm * 0.25
            + active_days_norm * 0.25
            + streak_norm * 0.1
        )

    def calculate_total_score(self, profile: UserProfile) -> float:
        """Calculate total score using weighted formula.

        Args:
            profile: User profile with all data.

        Returns:
            Total score between 0 and 100.
        """
        weights = self.config.scoring.weights

        # Normalize individual metrics
        followers_norm = self.normalize_log(
            profile.followers,
            self.config.scoring.max_followers,
        )
        stars_norm = self.normalize_log(
            profile.total_stars,
            self.config.scoring.max_stars,
        )
        contribution_norm = self.normalize_log(
            profile.contribution_stats.total_contributions,
            self.config.scoring.max_contributions,
        )
        repos_contrib_norm = self.normalize_log(
            profile.repos_contributed_to,
            self.config.scoring.max_repos_contributed_to,
        )

        language_score = self.calculate_language_score(profile)
        activity_score = self.calculate_activity_score(profile)

        # Calculate weighted sum
        base_score = (
            followers_norm * weights.followers
            + stars_norm * weights.total_stars
            + contribution_norm * weights.contribution_count
            + repos_contrib_norm * weights.contribution_diversity
            + language_score * weights.language_score
        )

        # Convert to 0-100 scale
        total_score = base_score * 100

        # Apply bonuses for specific languages
        bonuses = 0.0
        if profile.language_stats.has_solidity:
            bonuses += 5.0
        if profile.language_stats.has_rust:
            bonuses += 5.0
        if profile.language_stats.has_go:
            bonuses += 5.0
        if profile.language_stats.has_typescript:
            bonuses += 2.0
        if profile.language_stats.has_mobile:
            bonuses += 2.0

        return min(100.0, total_score + bonuses)

    def calculate_scores(self, profile: UserProfile) -> None:
        """Calculate and set all scores on the profile.

        Args:
            profile: User profile to update with scores.
        """
        profile.language_score = self.calculate_language_score(profile)
        profile.activity_score = self.calculate_activity_score(profile)
        profile.total_score = self.calculate_total_score(profile)
