"""Configuration loading from YAML files."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class APIConfig(BaseModel):
    """API-related configuration."""

    requests_per_hour: int = 5000
    delay_between_requests: float = 0.75
    timeout: int = 30
    max_retries: int = 3


class ScoringWeights(BaseModel):
    """Weights for scoring calculation."""

    followers: float = 0.15
    total_stars: float = 0.20
    contribution_count: float = 0.25
    contribution_diversity: float = 0.15
    language_score: float = 0.25


class ScoringConfig(BaseModel):
    """Scoring configuration."""

    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    max_followers: int = 10000
    max_stars: int = 5000
    max_contributions: int = 2000
    max_repos_contributed_to: int = 50


class LanguageWeights(BaseModel):
    """Weights for programming languages."""

    solidity: float = 2.0
    rust: float = 2.0
    typescript: float = 1.5
    swift: float = 1.5
    kotlin: float = 1.5
    go: float = 1.3
    python: float = 1.0
    javascript: float = 1.0
    java: float = 1.0
    c: float = 1.0
    cpp: float = 1.0
    default: float = 0.5

    def get_weight(self, language: str) -> float:
        """Get weight for a language, falling back to default."""
        lang_lower = language.lower()
        # Handle C++ variants
        if lang_lower in ("c++", "cpp"):
            return self.cpp
        # Only check known language fields to avoid returning methods
        known_langs = {
            "solidity", "rust", "typescript", "swift", "kotlin",
            "go", "python", "javascript", "java", "c", "cpp"
        }
        if lang_lower in known_langs:
            return getattr(self, lang_lower)
        return self.default


class Config(BaseModel):
    """Main application configuration."""

    api: APIConfig = Field(default_factory=APIConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    languages: LanguageWeights = Field(default_factory=LanguageWeights)

    @classmethod
    def load(cls, path: Path | str | None = None) -> "Config":
        """Load configuration from a YAML file.

        Args:
            path: Path to config file. If None, uses default config.

        Returns:
            Loaded Config object.
        """
        if path is None:
            return cls()

        path = Path(path)
        if not path.exists():
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        return cls.model_validate(data)

    def save(self, path: Path | str) -> None:
        """Save configuration to a YAML file."""
        path = Path(path)
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, sort_keys=False)


class Settings(BaseSettings):
    """Environment-based settings."""

    github_token: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_settings() -> Settings:
    """Load settings from environment."""
    return Settings()


def get_default_config_path() -> Path:
    """Get the default config file path."""
    return Path("config.yaml")


def get_checkpoint_path(output_path: Path) -> Path:
    """Get the checkpoint file path for resume capability."""
    return output_path.parent / f".{output_path.stem}_checkpoint.json"
