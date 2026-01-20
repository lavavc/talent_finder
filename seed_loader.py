"""
Load seed users from CSV file.
"""

import csv
from pathlib import Path
from typing import List, Tuple

import config
from models import UserProfile
from storage import Storage


def load_seed_users(csv_path: str = None) -> List[Tuple[str, str]]:
    """
    Load seed users from CSV file.

    Returns:
        List of (username, location) tuples
    """
    csv_path = Path(csv_path or config.SEED_FILE)

    if not csv_path.exists():
        raise FileNotFoundError(f"Seed file not found: {csv_path}")

    users = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            username = row.get("Username", "").strip()
            location = row.get("Location", "").strip()

            if username:
                users.append((username, location))

    print(f"Loaded {len(users)} seed users from {csv_path}")
    return users


def initialize_storage_with_seeds(
    storage: Storage,
    csv_path: str = None
) -> int:
    """
    Initialize storage with seed users.

    Returns:
        Number of new users added
    """
    seed_users = load_seed_users(csv_path)
    added = 0

    for username, location in seed_users:
        if not storage.has_user(username):
            # Create minimal profile, will be fully populated later
            user = UserProfile(
                username=username,
                location=location if location else None,
                source="seed",
                is_fully_scraped=False,
            )
            storage.add_user(user)
            added += 1

    storage.save()
    print(f"Added {added} new seed users to storage")
    return added


if __name__ == "__main__":
    # Test loading
    users = load_seed_users()
    print(f"\nFirst 5 users:")
    for username, location in users[:5]:
        print(f"  {username} ({location or 'no location'})")
