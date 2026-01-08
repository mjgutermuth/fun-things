# Critical Role Episode Tracker

Scrapes all Critical Role episodes from the wiki and creates a Google Sheets-compatible CSV for tracking what you've watched.

## Quick Start

### 1. Fetch the wiki page
```bash
curl "https://criticalrole.fandom.com/wiki/List_of_episodes" > cr_wiki.html
```

### 2. Run the scraper
```bash
python3 cr_complete_scraper.py cr_wiki.html
```

This creates `cr_episodes.csv` with 450+ episodes.

### 3. Import to Google Sheets
1. Create a new Google Sheet
2. File → Import → Upload
3. Select `cr_episodes.csv`
4. Import!

## What Gets Scraped

- **All Campaign Episodes** (C1: 115, C2: 141, C3: 120+, C4: ongoing)
- **Specials** (50+ one-shots and special events)
- **Miniseries** (Exandria Unlimited, Candela Obscura, etc.)
- **Talk Shows** (4-Sided Dive, Talks Machina)
- **Animated Series** (Legend of Vox Machina, Mighty Nein)

## CSV Structure

| Column | Description |
|--------|-------------|
| show_type | Main Campaign, Special, Miniseries, Talk Show, etc. |
| campaign | Campaign One, Campaign Two, Specials, etc. |
| arc | Story arc (e.g., "Arc 1: Kraghammer and Vasselheim") |
| episode_number | Episode number (1, 2, 3, etc.) |
| title | Episode title |
| airdate | Air date (YYYY-MM-DD format) |
| vod_url | YouTube/streaming link |
| wiki_url | Link to wiki page for more details |
| runtime | Episode length (H:MM:SS) |
| guests | Guest stars (if any) |
| dm_gm | DM/GM name (if not Matt Mercer) |
| watched | Checkbox column (☐ = unwatched, ☑ = watched) |
| notes | Your personal notes |

## Usage Tips

### Filter by campaign
Sort/filter the `campaign` column to focus on one campaign at a time.

### Track progress
Change ☐ to ☑ in the `watched` column as you watch episodes.

### Find episodes with guests
Filter the `guests` column to find special episodes.

### Chronological order
Sort by `airdate` to watch in release order across all shows.

## Updating

To get new episodes (run weekly):
```bash
curl "https://criticalrole.fandom.com/wiki/List_of_episodes" > cr_wiki.html
python3 cr_complete_scraper.py cr_wiki.html
```

Then compare the new CSV with your existing sheet and append new rows.