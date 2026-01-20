# GitHub Talent Finder

This tool is intended to help you find talented developers on GitHub that are relevant to you.

Twitter charges $5000/month for meaningful API access. LinkedIn is cheaper, but still unafforable for many in Emerging Markets. Plus, the signal there is difficult to find in all the noise. Github will answer 5000 requests/hour for anyone with a token, for free.

Our talent finder is a customisable CLI tool. Follow the instructions below to get set up, and then run it in your terminal, using whichever options are most relevant to you.

You'll get the most relevant results if your start with your own list of GitHub accounts you are already interested in.

### Option 1

Enrich the list of names you already have with activity, contribution, and language data. We find this useful to get a ranked view of our network, or to find people using the sort of language you would use when building things we at LAVA are interested in (the list is ranked by a global activity score, but we output a .csv file so that we can filter by various other columns we might be interested in researching).

If you have a large list to begin with, then we recommend you stick to this option otherwise you risk getting rate-limited. We're typically making 4 requests per user (depending on how many repos they have), so don't include more than 1,000 people on your list otherwise you'll hit the API limits.

For the example `gh_data.csv` provided, it takes about 25 minutes to run. We'd like to thank [Gayan Voice](https://github.com/gayanvoice/top-github-users) for providing the data we used to create this list. We filtered the data in that repo for African countries only, and only the top 20 users per country. Feel free to apply your own methods and filters.

### Option 2

Perhaps you only know 5 really cracked devs. Use this option to find their most popular repos by number of stars, and then look at all their collaborators. Build out a network of great developers by looking at who the people you most respect spend their precious time and energy actually collaborating with.

You'll need to specify how many repos of theirs to look at (it defaults to top 10 by star count) and how many collaborators per repo to consider (it default to the 30 most active) to avoid rate limits.

### Option 3

Also for those starting with small seed lists. Instead of crunching through popular repos and collaborators, create a network of users by looking at who else is following the people you are interested in. 

Depending on how many developers you begin with, you can set the "degree", i.e. do you want to collect followers, or followers of followers etc. Remember, there is a 5000 request/hour limit, so keep that in mind when tuning this parameter.

## Get Set Up

```bash
git clone git@github.com:lavavc/talent_finder.git
cd gh-scraper
```

This project uses Python, and I recommend using a virtual environment for your own sanity. Start the ven and install necessary dependencies with a command like:

```bash
python3 -m venv .venv && source .venv/bin/activate && python3 -m pip install -e .
```

This may depend on exactly where Python 3 is on your system and how your paths are set up.

You'll also need to setup a GitHub Access Token of your own. Go to your Settings, then to Developer Settings, and create a classic token. It should have `repo` and `read:user` scopes. Put this token in your `.env` file:

```bash
cp .env.example .env
# Edit .env and add your GitHub token
```

## Usage

3. Run the scraper:
   
```bash
gh-scraper scrape --input lava_data.csv
```

## CLI Commands

### Option 1: Scrape and enrich profiles

```bash
gh-scraper scrape --input users.csv --output enriched.csv
```

| Flag | Default | Description |
|------|---------|-------------|
| `-i, --input` | (required) | Input CSV with `gh_username` column |
| `-o, --output` | `processed_profiles.csv` | Output file (.csv or .xlsx) |
| `--resume` | off | Resume from checkpoint if interrupted |
| `--username-column` | `gh_username` | Column name for usernames |

### Option 2: Discover collaborators

Find developers who contribute to the same repos as your seed users.

```bash
gh-scraper discover collaborators --input seed.csv
```

| Flag | Default | Description |
|------|---------|-------------|
| `-i, --input` | (required) | Input CSV with seed usernames |
| `-o, --output` | `discovered_collaborators.csv` | Output file |
| `--top-repos` | 10 | Number of top repos (by stars) to check per user |
| `--max-contributors` | 30 | Max contributors per repo (most active first) |

### Option 3: Discover followers

Find developers who follow people in your seed list.

```bash
gh-scraper discover followers --input seed.csv
```

| Flag | Default | Description |
|------|---------|-------------|
| `-i, --input` | (required) | Input CSV with seed usernames |
| `-o, --output` | `discovered_followers.csv` | Output file |
| `--depth` | 1 | Network depth (1 = followers, 2 = followers of followers) |
| `--max-followers` | 500 | Max followers to fetch per user |

### Check a single profile

```bash
gh-scraper check torvalds
```

### Generate default config

```bash
gh-scraper init-config
```

## Output Columns

| Column | Description |
|--------|-------------|
| `username` | GitHub username |
| `total_score` | Overall score (0-100) |
| `followers` | Number of followers |
| `location` | User's location (for geographic filtering) |
| `activity_score` | Activity-based score |
| `activity_density` | Contributions per day (365 days) |
| `contribution_density` | Contributions per active day |
| `total_contributions` | Total contributions in past year |
| `total_stars` | Total stars across all repos |
| `top_languages` | Top 5 programming languages |
| `has_solidity` | Uses Solidity |
| `has_rust` | Uses Rust |
| `has_typescript` | Uses TypeScript |
| `has_mobile` | Uses mobile languages (Kotlin/Swift/Dart) |
| `source` | How user was found: `seed`, `collaborator`, or `follower` |
| `source_user` | Who they were discovered from |
| `error` | Error message if scraping failed |

## Configuration

Edit `config.yaml` to customize:

- **API settings**: Rate limits, delays, timeouts
- **Scoring weights**: Adjust importance of different metrics
- **Language weights**: Prioritize specific programming languages

## License

MIT
