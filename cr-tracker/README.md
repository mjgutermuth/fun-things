# Critical Role Episode Tracker

A web-based tracker for all Critical Role content with automatic weekly updates.

## Files

- **index.html** - Main tracker web app (open in browser to use)
- **cr_episodes_series_airdates.csv** - Episode database (1000+ episodes)
- **beacon_scraper.py** - Scrapes CritRole.com for new Beacon-exclusive content
- **cr_complete_scraper.py** - Scrapes CR wiki for all episodes

## Automated Updates

### GitHub Actions (Enabled)
A GitHub Actions workflow runs **every Monday at 21:00 UTC** (2 PM Pacific / 5 PM
Eastern during DST; 1 PM / 4 PM in winter) to:
1. Scrape CritRole.com programming schedules for new Beacon content
2. Add any new episodes to the CSV
3. Automatically commit and push changes

**Workflow file:** `.github/workflows/scrape-episodes.yml`

**Manual trigger:** Go to Actions tab in GitHub and run "Scrape Critical Role Episodes" workflow

## Usage

### Using the Tracker
1. Open `index.html` in a web browser
2. Filter by show type and series
3. Check episodes as you watch them
4. Your progress is saved in browser localStorage on that device

### Syncing Across Devices
Enter your email in the bar at the top and click "Sign in to Sync," then
click the magic link sent to your inbox. Once signed in, your watch
history is tied to your account (via Supabase Auth) instead of the
browser — log in with the same email on any device and your progress
follows you. Signing in is optional; skip it and the tracker still works
fully offline, saved locally on that device only.

Schema/RLS setup for the `cr_sync` table lives in `supabase/schema.sql`.

### Manual Scraping

**Beacon-exclusive content:**
```bash
cd cr-tracker
python3 beacon_scraper.py
```

This will:
- Scrape all programming schedules from May 2024 to today
- Find Cooldown episodes, Fireside Chats, etc.
- Merge new episodes into the main CSV

**Full wiki scrape:**
```bash
cd cr-tracker
# First, save the CR wiki episodes page as HTML
python3 cr_complete_scraper.py episodes.html
```

## CSV Format

The main CSV includes:
- **episode_id** - Unique ID: `{show_type}|{campaign}|{episode_number}|{title}`
- **show_type** - Main Campaign, Miniseries, Webseries, Special, etc.
- **campaign** - Campaign name or series name
- **arc** - Sub-series or story arc (for Exandria Unlimited, etc.)
- **episode_number** - Episode number
- **title** - Episode title
- **airdate** - Air date (YYYY-MM-DD)
- **vod_url** - YouTube or Beacon.tv URL
- **wiki_url** - Critical Role wiki URL
- **runtime** - Episode length (H:MM:SS)
- **watched** - True/False (synced with localStorage)
- **notes** - Special notes
- **has_cooldown** - Whether episode has a Cooldown
- **cooldown_date** - Date of Cooldown episode

## Current Content

Everything from the founding Critical Role cast, from its Geek & Sundry days
through today's Beacon era:

- **Main Campaigns** - Vox Machina (C1), The Mighty Nein (C2), Bells Hells (C3), Campaign Four
- **Animated Series on Prime Video** - The Legend of Vox Machina, The Mighty Nein
- **Miniseries** - Exandria Unlimited, Candela Obscura, Age of Umbra, etc.
- **Talkback Shows** - Talks Machina, 4-Sided Dive, Critical Role Cooldown, Tale Gate
- **Webseries** - from the Geek & Sundry era (Handbooker Helper, Game Master Tips, EverythingIsContent, etc.) through today's shows (Get Your Sheet Together, Narrative Telephone, Weird Kids, etc.)
- **Specials & One-Shots** - Live Shows, One-Shots, Crit Recap Animated
- **Beacon Exclusives** - Fireside Chat, Backstage Pass, Critical Role Cooldown

Not currently tracked: Beacon-exclusive shows from outside the founding cast
(Viva La Dirt League, Midst, Tales from the Stinky Dragon), but open to
adding if there's interest.