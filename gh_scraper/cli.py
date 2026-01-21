"""Click CLI for GitHub profile scraper."""

import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from gh_scraper.config import Config, load_settings
from gh_scraper.output import InputReader, OutputWriter
from gh_scraper.scraper import ProfileScraper

console = Console()


def get_progress() -> Progress:
    """Create a rich progress bar."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    )


@click.group()
@click.version_option(version="0.1.0")
def main():
    """GitHub Profile Scraper - Enrich user data with scores and language analysis."""
    pass


@main.command()
@click.option(
    "--input", "-i",
    "input_file",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Input CSV file with GitHub usernames",
)
@click.option(
    "--output", "-o",
    "output_file",
    default="processed_profiles.csv",
    type=click.Path(path_type=Path),
    help="Output file path (.csv or .xlsx)",
)
@click.option(
    "--config", "-c",
    "config_file",
    type=click.Path(exists=True, path_type=Path),
    help="Custom configuration YAML file",
)
@click.option(
    "--resume/--no-resume",
    default=False,
    help="Resume from previous checkpoint",
)
@click.option(
    "--username-column",
    default="gh_username",
    help="Name of the column containing GitHub usernames",
)
@click.option(
    "--token",
    envvar="GITHUB_TOKEN",
    help="GitHub personal access token (or set GITHUB_TOKEN env var)",
)
@click.option(
    "--update-ranking",
    "ranking_file",
    type=click.Path(path_type=Path),
    help="Update a markdown ranking file with results (e.g., borderless_ranked.md)",
)
@click.option(
    "--ranking-title",
    default="Borderless Talent Ranking",
    help="Title for the ranking markdown file",
)
def scrape(
    input_file: Path,
    output_file: Path,
    config_file: Path | None,
    resume: bool,
    username_column: str,
    token: str | None,
    ranking_file: Path | None,
    ranking_title: str,
):
    """Scrape GitHub profiles from a CSV and output enriched data."""
    # Load environment variables
    load_dotenv()

    # Get token from environment if not provided
    if not token:
        settings = load_settings()
        token = settings.github_token

    if not token:
        console.print(
            "[yellow]Warning: No GitHub token provided. "
            "Rate limits will be stricter and contribution data unavailable.[/yellow]"
        )
        console.print(
            "Set GITHUB_TOKEN environment variable or use --token option."
        )

    # Load configuration
    config = Config.load(config_file)

    # Read input usernames
    console.print(f"[bold]Reading input file:[/bold] {input_file}")
    try:
        reader = InputReader(input_file)
        usernames = reader.read_usernames(username_column)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    console.print(f"[green]Found {len(usernames)} usernames to process[/green]")

    # Initialize output writer
    writer = OutputWriter(output_file)

    # Handle resume
    processed = set()
    if resume:
        processed = writer.load_checkpoint()
        if processed:
            console.print(f"[yellow]Resuming: {len(processed)} users already processed[/yellow]")

    # Filter out already processed usernames
    remaining_usernames = [u for u in usernames if u not in processed]

    if not remaining_usernames:
        console.print("[green]All users already processed![/green]")
        writer.write()
        console.print(f"[bold green]Output saved to:[/bold green] {output_file}")
        return

    # Initialize scraper
    with ProfileScraper(token=token, config=config) as scraper:
        # Process users with progress bar
        with get_progress() as progress:
            task = progress.add_task("Scraping profiles...", total=len(remaining_usernames))

            errors = 0
            for username in remaining_usernames:
                progress.update(task, description=f"Scraping {username}...")

                profile = scraper.scrape_user(username)
                writer.add_result(profile)

                if profile.error:
                    errors += 1

                # Save checkpoint periodically
                if writer.result_count % 10 == 0:
                    writer.save_checkpoint()

                progress.advance(task)

    # Write final output
    writer.write()

    # Print summary
    console.print()
    console.print("[bold green]Scraping complete![/bold green]")
    console.print(f"  Total users: {writer.result_count}")
    console.print(f"  Errors: {errors}")
    console.print(f"  Output: {output_file}")

    # Show top 5 results
    if writer.result_count > 0:
        console.print()
        show_top_results(output_file, n=5)

    # Update ranking markdown if requested
    if ranking_file:
        console.print()
        generate_ranking_markdown(output_file, ranking_file, ranking_title)


def show_top_results(output_file: Path, n: int = 5):
    """Display top N results in a table."""
    import pandas as pd

    suffix = output_file.suffix.lower()
    if suffix == ".xlsx":
        df = pd.read_excel(output_file)
    else:
        df = pd.read_csv(output_file)

    df = df.head(n)

    table = Table(title=f"Top {n} Profiles by Score")
    table.add_column("Username", style="cyan")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Followers", justify="right")
    table.add_column("Stars", justify="right")
    table.add_column("Contributions", justify="right")
    table.add_column("Top Languages", style="yellow")

    for _, row in df.iterrows():
        table.add_row(
            str(row["username"]),
            f"{row['total_score']:.1f}",
            str(row["followers"]),
            str(row["total_stars"]),
            str(row["total_contributions"]),
            str(row["top_languages"])[:30],
        )

    console.print(table)


def generate_ranking_markdown(csv_path: Path, output_path: Path, title: str = "Talent Ranking"):
    """Generate a markdown ranking file from a processed CSV.

    Args:
        csv_path: Path to the input CSV file.
        output_path: Path to the output markdown file.
        title: Title for the markdown document.
    """
    import pandas as pd

    df = pd.read_csv(csv_path)

    # Filter out rows with 0 total_score and sort by total_score
    df = df[df["total_score"] > 0].sort_values("total_score", ascending=False)

    lines = [
        f"# {title}",
        "",
        "GitHub developer rankings based on activity, contributions, and technical skills.",
        "",
        "| Rank | GitHub Username | Total Score | Followers | Contributions | Stars | Top Languages |",
        "|------|-----------------|-------------|-----------|---------------|-------|---------------|",
    ]

    for i, (_, row) in enumerate(df.iterrows(), 1):
        username = row["username"]
        gh_link = f"[@{username}](https://github.com/{username})"
        score = f"{row['total_score']:.2f}"
        followers = int(row["followers"])
        contributions = int(row["total_contributions"])
        stars = int(row["total_stars"])
        langs = str(row["top_languages"]) if pd.notna(row["top_languages"]) else ""
        langs = langs.strip('"').strip("'")

        lines.append(
            f"| {i} | {gh_link} | {score} | {followers:,} | {contributions:,} | {stars:,} | {langs} |"
        )

    output_path.write_text("\n".join(lines) + "\n")
    console.print(f"[green]Ranking updated:[/green] {output_path}")


@main.command()
@click.option(
    "--output", "-o",
    "output_file",
    default="config.yaml",
    type=click.Path(path_type=Path),
    help="Output path for config file",
)
def init_config(output_file: Path):
    """Generate a default configuration file."""
    config = Config()
    config.save(output_file)
    console.print(f"[green]Configuration file created:[/green] {output_file}")


@main.command()
@click.argument("username")
@click.option(
    "--token",
    envvar="GITHUB_TOKEN",
    help="GitHub personal access token",
)
@click.option(
    "--config", "-c",
    "config_file",
    type=click.Path(exists=True, path_type=Path),
    help="Custom configuration YAML file",
)
def check(username: str, token: str | None, config_file: Path | None):
    """Check a single GitHub profile (for testing)."""
    load_dotenv()

    if not token:
        settings = load_settings()
        token = settings.github_token

    config = Config.load(config_file)

    console.print(f"[bold]Checking profile:[/bold] {username}")

    with ProfileScraper(token=token, config=config) as scraper:
        profile = scraper.scrape_user(username)

    if profile.error:
        console.print(f"[red]Error:[/red] {profile.error}")
        return

    # Display results
    table = Table(title=f"Profile: {username}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Name", profile.name or "-")
    table.add_row("Location", profile.location or "-")
    table.add_row("Followers", str(profile.followers))
    table.add_row("Public Repos", str(profile.public_repos))
    table.add_row("Total Stars", str(profile.total_stars))
    table.add_row("Total Contributions", str(profile.contribution_stats.total_contributions))
    table.add_row("Activity Density", f"{profile.contribution_stats.activity_density:.2f}")
    table.add_row("Top Languages", ", ".join(profile.language_stats.top_languages))
    table.add_row("Has Solidity", str(profile.language_stats.has_solidity))
    table.add_row("Has Rust", str(profile.language_stats.has_rust))
    table.add_row("Has Go", str(profile.language_stats.has_go))
    table.add_row("Has TypeScript", str(profile.language_stats.has_typescript))
    table.add_row("Has Mobile", str(profile.language_stats.has_mobile))
    table.add_row("Total Score", f"{profile.total_score:.2f}")

    console.print(table)


# Discovery command group
@main.group()
def discover():
    """Expand your seed list by discovering new users.

    Two discovery methods are available:

    \b
    COLLABORATORS: Find users who contribute to the same repositories.
      gh-scraper discover collaborators -i seed.csv

    \b
    FOLLOWERS: Find users who follow people in your seed list.
      gh-scraper discover followers -i seed.csv --depth 1
    """
    pass


@discover.command("collaborators")
@click.option(
    "--input", "-i",
    "input_file",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Input CSV file with seed GitHub usernames",
)
@click.option(
    "--output", "-o",
    "output_file",
    default="discovered_collaborators.csv",
    type=click.Path(path_type=Path),
    help="Output file path (.csv or .xlsx)",
)
@click.option(
    "--top-repos",
    default=10,
    show_default=True,
    help="Number of top repos (by stars) to check per user",
)
@click.option(
    "--max-contributors",
    default=30,
    show_default=True,
    help="Maximum contributors per repo (most active first)",
)
@click.option(
    "--config", "-c",
    "config_file",
    type=click.Path(exists=True, path_type=Path),
    help="Custom configuration YAML file",
)
@click.option(
    "--username-column",
    default="gh_username",
    help="Name of the column containing GitHub usernames",
)
@click.option(
    "--token",
    envvar="GITHUB_TOKEN",
    help="GitHub personal access token",
)
def discover_collaborators(
    input_file: Path,
    output_file: Path,
    top_repos: int,
    max_contributors: int,
    config_file: Path | None,
    username_column: str,
    token: str | None,
):
    """Discover collaborators from seed users' top repositories."""
    from gh_scraper.discovery import NetworkDiscovery
    from gh_scraper.models import ScrapedUser

    load_dotenv()

    if not token:
        settings = load_settings()
        token = settings.github_token

    if not token:
        console.print("[red]Error: GitHub token required for discovery.[/red]")
        console.print("Set GITHUB_TOKEN environment variable or use --token option.")
        sys.exit(1)

    config = Config.load(config_file)

    # Read seed usernames
    console.print(f"[bold]Reading seed file:[/bold] {input_file}")
    try:
        reader = InputReader(input_file)
        seed_usernames = reader.read_usernames(username_column)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    console.print(f"[green]Found {len(seed_usernames)} seed users[/green]")

    # Phase 1: Discover collaborators
    console.print()
    console.print("[bold]Phase 1: Discovering collaborators...[/bold]")

    with NetworkDiscovery(token=token, config=config) as discovery:
        with get_progress() as progress:
            task = progress.add_task("Finding collaborators...", total=len(seed_usernames))

            def update_progress(username: str, status: str):
                progress.update(task, description=f"{username}: {status}")

            discovered = discovery.discover_collaborators(
                seed_usernames=seed_usernames,
                top_repos=top_repos,
                max_contributors=max_contributors,
                progress_callback=update_progress,
            )

            for _ in seed_usernames:
                progress.advance(task)

        console.print(f"[green]Discovered {len(discovered)} unique collaborators[/green]")

        # Phase 2: Scrape discovered users
        console.print()
        console.print("[bold]Phase 2: Scraping discovered profiles...[/bold]")

        writer = OutputWriter(output_file)
        errors = 0

        with get_progress() as progress:
            task = progress.add_task("Scraping profiles...", total=len(discovered))

            for username, source_users in discovered.items():
                progress.update(task, description=f"Scraping {username}...")

                profile = discovery.scrape_user(username)
                scraped = ScrapedUser.from_profile(
                    profile,
                    source="collaborator",
                    source_user=", ".join(source_users[:3]),  # Limit to first 3 sources
                )
                writer._results.append(scraped)
                writer._processed_usernames.add(username)

                if profile.error:
                    errors += 1

                if writer.result_count % 10 == 0:
                    writer.save_checkpoint()

                progress.advance(task)

    writer.write()

    console.print()
    console.print("[bold green]Discovery complete![/bold green]")
    console.print(f"  Discovered users: {writer.result_count}")
    console.print(f"  Errors: {errors}")
    console.print(f"  Output: {output_file}")

    if writer.result_count > 0:
        console.print()
        show_top_results(output_file, n=5)


@discover.command("followers")
@click.option(
    "--input", "-i",
    "input_file",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Input CSV file with seed GitHub usernames",
)
@click.option(
    "--output", "-o",
    "output_file",
    default="discovered_followers.csv",
    type=click.Path(path_type=Path),
    help="Output file path (.csv or .xlsx)",
)
@click.option(
    "--depth",
    default=1,
    show_default=True,
    help="Network depth (1 = direct followers, 2 = followers of followers, etc.)",
)
@click.option(
    "--max-followers",
    default=500,
    show_default=True,
    help="Maximum followers to fetch per user",
)
@click.option(
    "--config", "-c",
    "config_file",
    type=click.Path(exists=True, path_type=Path),
    help="Custom configuration YAML file",
)
@click.option(
    "--username-column",
    default="gh_username",
    help="Name of the column containing GitHub usernames",
)
@click.option(
    "--token",
    envvar="GITHUB_TOKEN",
    help="GitHub personal access token",
)
def discover_followers(
    input_file: Path,
    output_file: Path,
    depth: int,
    max_followers: int,
    config_file: Path | None,
    username_column: str,
    token: str | None,
):
    """Discover followers from seed users with configurable network depth."""
    from gh_scraper.discovery import NetworkDiscovery
    from gh_scraper.models import ScrapedUser

    load_dotenv()

    if not token:
        settings = load_settings()
        token = settings.github_token

    if not token:
        console.print("[red]Error: GitHub token required for discovery.[/red]")
        console.print("Set GITHUB_TOKEN environment variable or use --token option.")
        sys.exit(1)

    config = Config.load(config_file)

    # Read seed usernames
    console.print(f"[bold]Reading seed file:[/bold] {input_file}")
    try:
        reader = InputReader(input_file)
        seed_usernames = reader.read_usernames(username_column)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    console.print(f"[green]Found {len(seed_usernames)} seed users[/green]")
    console.print(f"[dim]Network depth: {depth}, Max followers per user: {max_followers}[/dim]")

    # Phase 1: Discover followers
    console.print()
    console.print("[bold]Phase 1: Discovering followers...[/bold]")

    with NetworkDiscovery(token=token, config=config) as discovery:
        with get_progress() as progress:
            task = progress.add_task("Finding followers...", total=len(seed_usernames))

            def update_progress(username: str, status: str):
                progress.update(task, description=f"{username}: {status}")

            discovered = discovery.discover_followers(
                seed_usernames=seed_usernames,
                depth=depth,
                max_followers_per_user=max_followers,
                progress_callback=update_progress,
            )

            for _ in seed_usernames:
                progress.advance(task)

        console.print(f"[green]Discovered {len(discovered)} unique followers[/green]")

        # Phase 2: Scrape discovered users
        console.print()
        console.print("[bold]Phase 2: Scraping discovered profiles...[/bold]")

        writer = OutputWriter(output_file)
        errors = 0

        with get_progress() as progress:
            task = progress.add_task("Scraping profiles...", total=len(discovered))

            for username, source_users in discovered.items():
                progress.update(task, description=f"Scraping {username}...")

                profile = discovery.scrape_user(username)
                scraped = ScrapedUser.from_profile(
                    profile,
                    source="follower",
                    source_user=", ".join(source_users[:3]),
                )
                writer._results.append(scraped)
                writer._processed_usernames.add(username)

                if profile.error:
                    errors += 1

                if writer.result_count % 10 == 0:
                    writer.save_checkpoint()

                progress.advance(task)

    writer.write()

    console.print()
    console.print("[bold green]Discovery complete![/bold green]")
    console.print(f"  Discovered users: {writer.result_count}")
    console.print(f"  Errors: {errors}")
    console.print(f"  Output: {output_file}")

    if writer.result_count > 0:
        console.print()
        show_top_results(output_file, n=5)


if __name__ == "__main__":
    main()
