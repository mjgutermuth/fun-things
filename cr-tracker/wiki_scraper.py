#!/usr/bin/env python3
"""
Scrape Critical Role wiki for new main campaign episodes
and merge them into the main CSV
"""

import csv
import re
import sys
import time
from datetime import datetime
from bs4 import BeautifulSoup

# Try Playwright first, fall back to requests
USE_PLAYWRIGHT = True
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    USE_PLAYWRIGHT = False
    import requests


def fetch_episode_list():
    """Fetch the episode list page from the CR wiki"""
    url = "https://criticalrole.fandom.com/wiki/List_of_episodes"
    print(f"Fetching {url}...")

    if USE_PLAYWRIGHT:
        return fetch_with_playwright(url)
    else:
        return fetch_with_requests(url)


def fetch_with_playwright(url):
    """Use Playwright with headless Chromium to fetch the page (bypasses Cloudflare)"""
    print("Using Playwright to bypass Cloudflare...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        try:
            # Use domcontentloaded instead of networkidle (Fandom has many async requests)
            page.goto(url, wait_until='domcontentloaded', timeout=60000)

            # Wait for wikitable to appear (indicates page content loaded)
            print("Waiting for page content...")
            page.wait_for_selector('.wikitable', timeout=45000)

            # Short additional wait for any remaining content
            time.sleep(1)

            html = page.content()
            print(f"Successfully fetched {len(html)} characters")
            return html
        finally:
            browser.close()


def fetch_with_requests(url):
    """Fallback to requests (may fail with Cloudflare)"""
    print("Playwright not available, using requests (may fail with Cloudflare)...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def clean_text(text):
    """Remove wiki formatting artifacts"""
    if not text:
        return ''
    text = re.sub(r'\[edit\]', '', text)
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\[\]', '', text)
    return text.strip()


def parse_date(date_str):
    """Parse various date formats into YYYY-MM-DD"""
    if not date_str:
        return ''

    date_str = clean_text(date_str)

    # Try common formats
    formats = [
        '%B %d, %Y',    # January 16, 2026
        '%b %d, %Y',    # Jan 16, 2026
        '%Y-%m-%d',     # 2026-01-16
        '%d %B %Y',     # 16 January 2026
        '%d %b %Y',     # 16 Jan 2026
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue

    return date_str  # Return as-is if parsing fails


def parse_runtime(runtime_str):
    """Parse runtime into HH:MM:SS format"""
    if not runtime_str:
        return ''

    runtime_str = clean_text(runtime_str)

    # Match patterns like "4:15:13" or "4h 15m 13s" or "4:15"
    match = re.search(r'(\d+):(\d+):(\d+)', runtime_str)
    if match:
        return f"{int(match.group(1))}:{match.group(2)}:{match.group(3)}"

    match = re.search(r'(\d+):(\d+)', runtime_str)
    if match:
        return f"{match.group(1)}:{match.group(2)}:00"

    return runtime_str


def parse_campaign_episodes(html_content):
    """Parse main campaign episodes from the wiki HTML using arc-based tables"""
    soup = BeautifulSoup(html_content, 'html.parser')
    episodes = []

    # Get all tables
    tables = soup.find_all('table', class_='wikitable')

    for table in tables:
        # Find the preceding h3 header (arc header)
        prev_h3 = table.find_previous('h3')
        if not prev_h3:
            continue

        arc_name = clean_text(prev_h3.get_text())

        # Find the preceding h2 header (campaign header) to determine which campaign
        prev_h2 = table.find_previous('h2')
        if not prev_h2:
            continue

        campaign_header = clean_text(prev_h2.get_text())

        # Determine campaign name from h2 header
        campaign_name = None
        if 'Campaign One' in campaign_header or 'Vox Machina' in campaign_header:
            campaign_name = 'Campaign One: Vox Machina'
        elif 'Campaign Two' in campaign_header or 'Mighty Nein' in campaign_header:
            campaign_name = 'Campaign Two: The Mighty Nein'
        elif 'Campaign Three' in campaign_header or 'Bells Hells' in campaign_header:
            campaign_name = 'Campaign Three: Bells Hells'
        elif 'Campaign Four' in campaign_header:
            campaign_name = 'Campaign Four'

        if not campaign_name:
            continue

        # Make sure this arc belongs to a main campaign (not animated, specials, etc)
        # by checking that the arc header contains "Arc" or "Campaign Four Arc"
        if 'Arc' not in arc_name and 'Campaign Four' not in arc_name:
            continue

        # Get table headers
        header_row = table.find('tr')
        if not header_row:
            continue

        headers = [clean_text(th.get_text()).lower() for th in header_row.find_all('th')]
        header_map = {h: i for i, h in enumerate(headers)}

        # Parse rows
        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            if len(cells) < 3:
                continue

            episode = {
                'show_type': 'Main Campaign',
                'campaign': campaign_name,
                'arc': arc_name,
                'episode_number': '',
                'title': '',
                'airdate': '',
                'vod_url': '',
                'wiki_url': '',
                'runtime': '',
            }

            # Episode number
            for num_header in ['no.', 'no', '#', 'episode']:
                if num_header in header_map and header_map[num_header] < len(cells):
                    ep_num = clean_text(cells[header_map[num_header]].get_text())
                    match = re.search(r'(\d+)', ep_num)
                    if match:
                        episode['episode_number'] = match.group(1)
                    break

            # Title and wiki URL
            for title_header in ['title', 'episode title', 'name']:
                if title_header in header_map and header_map[title_header] < len(cells):
                    title_cell = cells[header_map[title_header]]
                    title_link = title_cell.find('a')
                    if title_link:
                        episode['title'] = clean_text(title_link.get_text())
                        href = title_link.get('href', '')
                        if href.startswith('/wiki/'):
                            episode['wiki_url'] = 'https://criticalrole.fandom.com' + href
                    else:
                        episode['title'] = clean_text(title_cell.get_text())
                    break

            # Airdate
            for date_header in ['original airdate', 'airdate', 'air date', 'date']:
                if date_header in header_map and header_map[date_header] < len(cells):
                    episode['airdate'] = parse_date(cells[header_map[date_header]].get_text())
                    break

            # Runtime
            for runtime_header in ['runtime', 'length', 'duration']:
                if runtime_header in header_map and header_map[runtime_header] < len(cells):
                    episode['runtime'] = parse_runtime(cells[header_map[runtime_header]].get_text())
                    break

            # VOD URL - look for YouTube link
            for link_header in ['link', 'vod', 'video']:
                if link_header in header_map and header_map[link_header] < len(cells):
                    link_cell = cells[header_map[link_header]]
                    vod_link = link_cell.find('a', href=re.compile(r'youtube|youtu\.be'))
                    if vod_link:
                        episode['vod_url'] = vod_link['href']
                    break

            # Only add if we have a title and episode number
            if episode['title'] and episode['episode_number']:
                episodes.append(episode)

    return episodes


def merge_into_main_csv(new_episodes, main_csv='cr_episodes_series_airdates.csv'):
    """Merge new episodes into the main CSV"""
    if not new_episodes:
        print("\nNo new episodes to merge")
        return 0

    # Read existing CSV
    try:
        with open(main_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing_rows = list(reader)
            fieldnames = reader.fieldnames
    except FileNotFoundError:
        print(f"Error: {main_csv} not found")
        return 0

    # Build lookup of existing main campaign episodes by (campaign, episode_number)
    existing_episodes = {}
    for i, row in enumerate(existing_rows):
        if row.get('show_type') == 'Main Campaign':
            key = (row.get('campaign', ''), row.get('episode_number', ''))
            existing_episodes[key] = i

    def is_placeholder_title(title):
        """Check if title is a placeholder like 'Campaign 4 Episode 13'"""
        return bool(re.match(r'^Campaign \d+ Episode \d+$', title))

    # Find new episodes and update placeholders
    added = []
    updated = []
    for ep in new_episodes:
        key = (ep['campaign'], ep['episode_number'])
        if key not in existing_episodes:
            # Generate episode_id
            episode_id = f"Main Campaign|{ep['campaign']}|{ep['episode_number']}|{ep['title']}"

            new_row = {
                'episode_id': episode_id,
                'show_type': 'Main Campaign',
                'campaign': ep['campaign'],
                'arc': ep.get('arc', ''),
                'episode_number': ep['episode_number'],
                'title': ep['title'],
                'airdate': ep['airdate'],
                'vod_url': ep['vod_url'],
                'wiki_url': ep['wiki_url'],
                'runtime': ep['runtime'],
                'watched': 'False',
                'notes': '',
                'has_cooldown': 'False',
                'cooldown_date': '',
                'is_canon': 'TRUE',
                'prerequisite_episode': '',
                'prerequisite_notes': '',
            }

            existing_rows.append(new_row)
            existing_episodes[key] = len(existing_rows) - 1
            added.append(ep)
            print(f"  + {ep['campaign']} E{ep['episode_number']}: {ep['title']}")
        else:
            # Check if existing episode has a placeholder title that should be updated
            idx = existing_episodes[key]
            existing_row = existing_rows[idx]
            existing_title = existing_row.get('title', '')
            new_title = ep['title']

            if is_placeholder_title(existing_title) and not is_placeholder_title(new_title):
                # Update the title and other fields from wiki
                existing_row['title'] = new_title
                existing_row['episode_id'] = f"Main Campaign|{ep['campaign']}|{ep['episode_number']}|{new_title}"
                if ep.get('wiki_url') and not existing_row.get('wiki_url'):
                    existing_row['wiki_url'] = ep['wiki_url']
                if ep.get('arc') and not existing_row.get('arc'):
                    existing_row['arc'] = ep['arc']
                if ep.get('runtime') and not existing_row.get('runtime'):
                    existing_row['runtime'] = ep['runtime']
                # Remove placeholder note if present
                if 'wiki pending' in existing_row.get('notes', '').lower():
                    existing_row['notes'] = ''
                updated.append(ep)
                print(f"  ~ {ep['campaign']} E{ep['episode_number']}: {existing_title} -> {new_title}")

    if not added and not updated:
        print("\nNo new main campaign episodes to add or update")
        return 0

    if updated:
        print(f"\n✓ Updated {len(updated)} episode(s) with real titles")

    # Sort by airdate
    existing_rows.sort(key=lambda x: x.get('airdate', '') or '9999-99-99')

    # Write back
    with open(main_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_rows)

    if added:
        print(f"\n✓ Added {len(added)} new main campaign episode(s)")
    return len(added) + len(updated)


def main():
    print("=" * 80)
    print("CRITICAL ROLE WIKI EPISODE SCRAPER")
    print("=" * 80)

    # Fetch and parse
    html = fetch_episode_list()
    episodes = parse_campaign_episodes(html)

    print(f"\nFound {len(episodes)} main campaign episodes on wiki")

    # Show latest episodes per campaign
    by_campaign = {}
    for ep in episodes:
        campaign = ep['campaign']
        if campaign not in by_campaign:
            by_campaign[campaign] = []
        by_campaign[campaign].append(ep)

    print("\nLatest episodes by campaign:")
    for campaign, eps in sorted(by_campaign.items()):
        if eps:
            latest = max(eps, key=lambda x: int(x['episode_number']))
            print(f"  {campaign}: E{latest['episode_number']} - {latest['title']}")

    # Merge into main CSV
    print("\n" + "=" * 80)
    print("MERGING INTO MAIN CSV")
    print("=" * 80)

    new_count = merge_into_main_csv(episodes)

    if new_count > 0:
        print(f"\n✓ Successfully updated the tracker with {new_count} change(s)!")
    else:
        print("\n✓ No changes needed - CSV is up to date!")

    return new_count


if __name__ == '__main__':
    main()
