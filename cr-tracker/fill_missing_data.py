#!/usr/bin/env python3
"""
Fill missing VOD URLs and runtimes by scraping individual episode wiki pages
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


def fetch_page(url, timeout=30):
    """Fetch a page using Playwright or requests"""
    if USE_PLAYWRIGHT:
        return fetch_with_playwright(url, timeout)
    else:
        return fetch_with_requests(url, timeout)


def fetch_with_playwright(url, timeout=30):
    """Use Playwright with headless Chromium"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until='domcontentloaded', timeout=timeout * 1000)
            time.sleep(0.5)
            return page.content()
        finally:
            browser.close()


def fetch_with_requests(url, timeout=30):
    """Fallback to requests"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def extract_youtube_url(html):
    """Extract YouTube VOD URL from episode wiki page"""
    soup = BeautifulSoup(html, 'html.parser')

    # Method 1: Look for YouTube links in the page
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://youtu\.be/[\w-]+'
    ]

    # Check all links
    for link in soup.find_all('a', href=True):
        href = link['href']
        for pattern in youtube_patterns:
            match = re.search(pattern, href)
            if match:
                return match.group(0)

    # Method 2: Look in page text/infobox
    text = soup.get_text()
    for pattern in youtube_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)

    return None


def extract_runtime(html):
    """Extract runtime from episode wiki page"""
    soup = BeautifulSoup(html, 'html.parser')

    # Look for runtime in infobox
    # Common patterns: "Runtime", "Length", "Duration"
    infobox = soup.find('aside', class_='portable-infobox') or soup.find('table', class_='infobox')

    if infobox:
        text = infobox.get_text()
        # Look for runtime pattern
        runtime_match = re.search(r'(?:Runtime|Length|Duration)[:\s]*(\d+:\d{2}:\d{2}|\d+:\d{2})', text, re.IGNORECASE)
        if runtime_match:
            runtime = runtime_match.group(1)
            # Normalize to H:MM:SS
            if runtime.count(':') == 1:
                runtime = '0:' + runtime
            return runtime

    # Fallback: search entire page
    text = soup.get_text()
    # Look for runtime near "Runtime" label
    runtime_match = re.search(r'Runtime[:\s]*(\d+:\d{2}:\d{2})', text, re.IGNORECASE)
    if runtime_match:
        return runtime_match.group(1)

    return None


def find_episodes_missing_data(csv_file):
    """Find episodes missing VOD URLs or runtimes"""
    missing_vod = []
    missing_runtime = []

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for i, row in enumerate(rows):
        show_type = row.get('show_type', '')
        wiki_url = row.get('wiki_url', '').strip()
        vod_url = row.get('vod_url', '').strip()
        runtime = row.get('runtime', '').strip()
        airdate = row.get('airdate', '')
        notes = row.get('notes', '').lower()

        # Skip future episodes, beacon exclusives, or episodes without wiki URLs
        if not wiki_url or 'forthcoming' in notes or 'available soon' in notes:
            continue
        if 'beacon' in notes or vod_url == 'https://www.beacon.tv':
            continue

        # Only process Main Campaign episodes
        if show_type != 'Main Campaign':
            continue

        # Check if episode is in the past
        if airdate and airdate != 'Forthcoming':
            try:
                ep_date = datetime.strptime(airdate, '%Y-%m-%d')
                if ep_date >= datetime.now():
                    continue
            except ValueError:
                continue

        if not vod_url:
            missing_vod.append((i, row))

        if not runtime or runtime in ['0:00:00', 'Forthcoming']:
            missing_runtime.append((i, row))

    return missing_vod, missing_runtime, rows


def update_csv(rows, fieldnames, csv_file):
    """Write updated rows back to CSV"""
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    # Parse arguments
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    csv_file = args[0] if args else 'cr_episodes_series_airdates.csv'
    dry_run = '--dry-run' in sys.argv

    print("=" * 80)
    print("FILL MISSING DATA - VOD URLs & Runtimes")
    print("=" * 80)
    print(f"Using {'Playwright' if USE_PLAYWRIGHT else 'requests'} for fetching")
    if dry_run:
        print("DRY RUN MODE - no changes will be saved")
    print()

    # Load CSV and get fieldnames
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

    missing_vod, missing_runtime, rows = find_episodes_missing_data(csv_file)

    # Combine and deduplicate episodes to fetch
    episodes_to_fetch = {}
    for i, row in missing_vod:
        episodes_to_fetch[i] = {'row': row, 'needs_vod': True, 'needs_runtime': False}
    for i, row in missing_runtime:
        if i in episodes_to_fetch:
            episodes_to_fetch[i]['needs_runtime'] = True
        else:
            episodes_to_fetch[i] = {'row': row, 'needs_vod': False, 'needs_runtime': True}

    print(f"Found {len(missing_vod)} episodes missing VOD URLs")
    print(f"Found {len(missing_runtime)} episodes missing runtimes")
    print(f"Total unique episodes to process: {len(episodes_to_fetch)}")
    print()

    if not episodes_to_fetch:
        print("✓ No missing data to fill!")
        return 0

    # Process each episode
    updated_vod = 0
    updated_runtime = 0
    failed = 0

    for i, data in sorted(episodes_to_fetch.items()):
        row = data['row']
        wiki_url = row['wiki_url']
        title = row['title']

        print(f"Fetching: {title}")
        print(f"  URL: {wiki_url}")

        try:
            html = fetch_page(wiki_url)

            if data['needs_vod']:
                youtube_url = extract_youtube_url(html)
                if youtube_url:
                    print(f"  ✓ Found VOD: {youtube_url}")
                    if not dry_run:
                        rows[i]['vod_url'] = youtube_url
                    updated_vod += 1
                else:
                    print(f"  - No VOD URL found")

            if data['needs_runtime']:
                runtime = extract_runtime(html)
                if runtime:
                    print(f"  ✓ Found runtime: {runtime}")
                    if not dry_run:
                        rows[i]['runtime'] = runtime
                    updated_runtime += 1
                else:
                    print(f"  - No runtime found")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed += 1

        # Be nice to the server
        time.sleep(1)

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"VOD URLs found: {updated_vod}/{len(missing_vod)}")
    print(f"Runtimes found: {updated_runtime}/{len(missing_runtime)}")
    print(f"Failed fetches: {failed}")

    if not dry_run and (updated_vod > 0 or updated_runtime > 0):
        update_csv(rows, fieldnames, csv_file)
        print(f"\n✓ Updated {csv_file}")
    elif dry_run:
        print("\nDry run complete - no changes saved")

    return 0


if __name__ == '__main__':
    sys.exit(main())
