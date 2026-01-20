"""CSV/XLSX output writer using pandas."""

import json
from pathlib import Path

import pandas as pd

from gh_scraper.config import get_checkpoint_path
from gh_scraper.models import ScrapedUser, UserProfile


class OutputWriter:
    """Writes scraped data to CSV or XLSX files."""

    def __init__(self, output_path: Path | str):
        """Initialize the output writer.

        Args:
            output_path: Path to the output file (.csv or .xlsx).
        """
        self.output_path = Path(output_path)
        self.checkpoint_path = get_checkpoint_path(self.output_path)
        self._results: list[ScrapedUser] = []
        self._processed_usernames: set[str] = set()

    def add_result(self, profile: UserProfile) -> None:
        """Add a scraped profile to the results.

        Args:
            profile: User profile to add.
        """
        scraped = ScrapedUser.from_profile(profile)
        self._results.append(scraped)
        self._processed_usernames.add(profile.username)

    def save_checkpoint(self) -> None:
        """Save current progress to checkpoint file."""
        checkpoint_data = {
            "processed": list(self._processed_usernames),
            "results": [r.model_dump() for r in self._results],
        }
        with open(self.checkpoint_path, "w") as f:
            json.dump(checkpoint_data, f)

    def load_checkpoint(self) -> set[str]:
        """Load checkpoint and return set of already processed usernames.

        Returns:
            Set of usernames that have already been processed.
        """
        if not self.checkpoint_path.exists():
            return set()

        try:
            with open(self.checkpoint_path) as f:
                checkpoint_data = json.load(f)

            self._processed_usernames = set(checkpoint_data.get("processed", []))
            self._results = [
                ScrapedUser.model_validate(r) for r in checkpoint_data.get("results", [])
            ]
            return self._processed_usernames
        except (json.JSONDecodeError, KeyError):
            return set()

    def clear_checkpoint(self) -> None:
        """Remove checkpoint file after successful completion."""
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()

    def write(self) -> None:
        """Write results to the output file."""
        if not self._results:
            return

        # Convert to DataFrame
        data = [r.model_dump() for r in self._results]
        df = pd.DataFrame(data)

        # Sort by total_score descending
        df = df.sort_values("total_score", ascending=False)

        # Write based on file extension
        suffix = self.output_path.suffix.lower()
        if suffix == ".xlsx":
            df.to_excel(self.output_path, index=False, sheet_name="GitHub Profiles")
        else:
            df.to_csv(self.output_path, index=False)

        # Clear checkpoint on success
        self.clear_checkpoint()

    @property
    def result_count(self) -> int:
        """Get number of results."""
        return len(self._results)

    @property
    def processed_usernames(self) -> set[str]:
        """Get set of processed usernames."""
        return self._processed_usernames


class InputReader:
    """Reads input CSV files with GitHub usernames."""

    def __init__(self, input_path: Path | str):
        """Initialize the input reader.

        Args:
            input_path: Path to the input CSV file.
        """
        self.input_path = Path(input_path)

    def read_usernames(self, username_column: str = "gh_username") -> list[str]:
        """Read GitHub usernames from input file.

        Args:
            username_column: Name of the column containing usernames.

        Returns:
            List of GitHub usernames.

        Raises:
            ValueError: If the username column is not found.
        """
        df = pd.read_csv(self.input_path)

        # Try to find the username column
        possible_columns = [
            username_column,
            "gh_username",
            "github_username",
            "username",
            "login",
            "user",
            "github",
        ]

        found_column = None
        for col in possible_columns:
            if col in df.columns:
                found_column = col
                break
            # Case-insensitive search
            for df_col in df.columns:
                if df_col.lower() == col.lower():
                    found_column = df_col
                    break
            if found_column:
                break

        if not found_column:
            available = ", ".join(df.columns.tolist())
            raise ValueError(
                f"Could not find username column. Tried: {', '.join(possible_columns)}. "
                f"Available columns: {available}"
            )

        # Extract usernames, filter out empty/null values
        usernames = df[found_column].dropna().astype(str).str.strip().tolist()
        usernames = [u for u in usernames if u and u.lower() != "nan"]

        return usernames
