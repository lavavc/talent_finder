"""Pydantic models for GitHub data structures."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Repository(BaseModel):
    """GitHub repository data."""

    name: str
    full_name: str
    description: str | None = None
    language: str | None = None
    stargazers_count: int = 0
    forks_count: int = 0
    watchers_count: int = 0
    size: int = 0
    fork: bool = False
    archived: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    pushed_at: datetime | None = None
    topics: list[str] = Field(default_factory=list)


class ContributionDay(BaseModel):
    """Single day contribution data from GraphQL."""

    date: str
    contribution_count: int = Field(alias="contributionCount")

    class Config:
        populate_by_name = True


class ContributionWeek(BaseModel):
    """Weekly contribution data from GraphQL."""

    contribution_days: list[ContributionDay] = Field(alias="contributionDays")

    class Config:
        populate_by_name = True


class ContributionCalendar(BaseModel):
    """Full contribution calendar from GraphQL."""

    total_contributions: int = Field(alias="totalContributions")
    weeks: list[ContributionWeek] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class ContributionStats(BaseModel):
    """Aggregated contribution statistics."""

    total_contributions: int = 0
    active_days: int = 0
    longest_streak: int = 0
    current_streak: int = 0
    activity_density: float = 0.0  # contributions / 365
    contribution_density: float = 0.0  # contributions / active_days

    @classmethod
    def from_calendar(cls, calendar: ContributionCalendar) -> "ContributionStats":
        """Calculate stats from a contribution calendar."""
        total = calendar.total_contributions
        active_days = 0
        current_streak = 0
        longest_streak = 0
        temp_streak = 0

        all_days: list[ContributionDay] = []
        for week in calendar.weeks:
            all_days.extend(week.contribution_days)

        for day in all_days:
            if day.contribution_count > 0:
                active_days += 1
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0

        # Calculate current streak from the end
        for day in reversed(all_days):
            if day.contribution_count > 0:
                current_streak += 1
            else:
                break

        days_in_year = len(all_days) if all_days else 365
        activity_density = total / days_in_year if days_in_year > 0 else 0.0
        contribution_density = total / active_days if active_days > 0 else 0.0

        return cls(
            total_contributions=total,
            active_days=active_days,
            longest_streak=longest_streak,
            current_streak=current_streak,
            activity_density=round(activity_density, 4),
            contribution_density=round(contribution_density, 4),
        )


class LanguageStats(BaseModel):
    """Aggregated language statistics across repos."""

    languages: dict[str, int] = Field(default_factory=dict)  # language -> bytes
    top_languages: list[str] = Field(default_factory=list)
    has_solidity: bool = False
    has_rust: bool = False
    has_typescript: bool = False
    has_mobile: bool = False  # kotlin/swift/dart/react-native

    @classmethod
    def from_repos(cls, repos: list[Repository]) -> "LanguageStats":
        """Aggregate language data from repositories."""
        languages: dict[str, int] = {}
        for repo in repos:
            if repo.language:
                lang = repo.language.lower()
                languages[lang] = languages.get(lang, 0) + repo.size

        sorted_langs = sorted(languages.keys(), key=lambda x: languages[x], reverse=True)
        top_languages = sorted_langs[:5]

        mobile_langs = {"kotlin", "swift", "dart"}
        has_mobile = any(lang in languages for lang in mobile_langs)
        # Also check for react-native in topics
        for repo in repos:
            if "react-native" in [t.lower() for t in repo.topics]:
                has_mobile = True
                break

        return cls(
            languages=languages,
            top_languages=top_languages,
            has_solidity="solidity" in languages,
            has_rust="rust" in languages,
            has_typescript="typescript" in languages,
            has_mobile=has_mobile,
        )


class UserProfile(BaseModel):
    """Complete GitHub user profile with all scraped data."""

    username: str
    name: str | None = None
    email: str | None = None
    bio: str | None = None
    company: str | None = None
    location: str | None = None
    blog: str | None = None
    twitter_username: str | None = None
    public_repos: int = 0
    public_gists: int = 0
    followers: int = 0
    following: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Aggregated data
    total_stars: int = 0
    total_forks: int = 0
    repos_contributed_to: int = 0
    contribution_stats: ContributionStats = Field(default_factory=ContributionStats)
    language_stats: LanguageStats = Field(default_factory=LanguageStats)

    # Scoring
    total_score: float = 0.0
    activity_score: float = 0.0
    language_score: float = 0.0

    # Error tracking
    error: str | None = None

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "UserProfile":
        """Create UserProfile from GitHub REST API response."""
        return cls(
            username=data.get("login", ""),
            name=data.get("name"),
            email=data.get("email"),
            bio=data.get("bio"),
            company=data.get("company"),
            location=data.get("location"),
            blog=data.get("blog"),
            twitter_username=data.get("twitter_username"),
            public_repos=data.get("public_repos", 0),
            public_gists=data.get("public_gists", 0),
            followers=data.get("followers", 0),
            following=data.get("following", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


class ScrapedUser(BaseModel):
    """Output model for CSV/Excel export."""

    username: str
    total_score: float = 0.0
    followers: int = 0
    location: str | None = None
    activity_score: float = 0.0
    activity_density: float = 0.0
    contribution_density: float = 0.0
    total_contributions: int = 0
    total_stars: int = 0
    top_languages: str = ""  # comma-separated
    has_solidity: bool = False
    has_rust: bool = False
    has_typescript: bool = False
    has_mobile: bool = False
    source: str = "seed"  # seed, collaborator, follower
    source_user: str | None = None  # who they were discovered from
    error: str | None = None

    @classmethod
    def from_profile(
        cls,
        profile: UserProfile,
        source: str = "seed",
        source_user: str | None = None,
    ) -> "ScrapedUser":
        """Convert UserProfile to ScrapedUser for export."""
        return cls(
            username=profile.username,
            total_score=round(profile.total_score, 2),
            followers=profile.followers,
            location=profile.location,
            activity_score=round(profile.activity_score, 2),
            activity_density=profile.contribution_stats.activity_density,
            contribution_density=profile.contribution_stats.contribution_density,
            total_contributions=profile.contribution_stats.total_contributions,
            total_stars=profile.total_stars,
            top_languages=", ".join(profile.language_stats.top_languages),
            has_solidity=profile.language_stats.has_solidity,
            has_rust=profile.language_stats.has_rust,
            has_typescript=profile.language_stats.has_typescript,
            has_mobile=profile.language_stats.has_mobile,
            source=source,
            source_user=source_user,
            error=profile.error,
        )
