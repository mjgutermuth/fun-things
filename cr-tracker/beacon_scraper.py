#!/usr/bin/env python3
"""
Scrape CritRole.com weekly programming schedules to extract Beacon-exclusive content
"""

import sys
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time
import csv

# Try Playwright first, fall back to requests
USE_PLAYWRIGHT = True
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    USE_PLAYWRIGHT = False
    import requests


def fetch_url_with_retry(url, max_retries=3, timeout=30):
    """
    Fetch a URL with retry logic. Uses Playwright if available, otherwise requests.
    Returns (html_content, success_bool)
    """
    for attempt in range(max_retries):
        try:
            if USE_PLAYWRIGHT:
                html = fetch_with_playwright(url, timeout)
            else:
                html = fetch_with_requests(url, timeout)
            return html, True
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                print(f"    Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                return None, False
    return None, False


def fetch_with_playwright(url, timeout=30):
    """Use Playwright with headless Chromium to fetch the page"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        try:
            response = page.goto(url, wait_until='domcontentloaded', timeout=timeout * 1000)
            if response and response.status == 404:
                raise Exception("404 Not Found")
            # Wait a moment for dynamic content
            time.sleep(0.5)
            return page.content()
        finally:
            browser.close()


def fetch_with_requests(url, timeout=30):
    """Fallback to requests (may fail with Cloudflare)"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    if response.status_code == 404:
        raise Exception("404 Not Found")
    response.raise_for_status()
    return response.text

def generate_schedule_urls(start_date, end_date):
    """
    Generate all weekly programming schedule URLs between two dates.
    Schedules are posted on Mondays.
    Returns both critrole.com and beacon.tv URLs.
    """
    urls = []
    current = start_date

    # Find the first Monday
    while current.weekday() != 0:  # 0 = Monday
        current += timedelta(days=1)

    while current <= end_date:
        # Format: programming-schedule-week-of-may-13th-2024
        month = current.strftime('%B').lower()
        day = current.day
        year = current.year

        # Add ordinal suffix (1st, 2nd, 3rd, 4th, etc.)
        if 10 <= day <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

        # Generate both critrole.com and beacon.tv URLs
        critrole_url = f"https://critrole.com/programming-schedule-week-of-{month}-{day}{suffix}-{year}/"
        beacon_url = f"https://beacon.tv/content/programming-schedule-week-of-{month}-{day}{suffix}-{year}"

        urls.append((current, critrole_url, 'critrole'))
        urls.append((current, beacon_url, 'beacon'))

        current += timedelta(days=7)  # Next Monday

    return urls

def extract_beacon_content(html, week_date):
    """
    Extract Beacon-exclusive content from a programming schedule page
    """
    soup = BeautifulSoup(html, 'html.parser')
    content = []
    
    # Look for the main content area
    text = soup.get_text()
    
    # Pattern 1: Critical Role Cooldown (simplified)
    # Matches: "Critical Cooldown: Campaign 3, Episode 96" or similar
    cooldown_pattern = r'Critical\s+(?:Role\s+)?Cooldown.*?Campaign\s+(\d+).*?Episode\s+(\d+)'
    cooldown_matches = list(re.finditer(cooldown_pattern, text, re.IGNORECASE))
    
    for match in cooldown_matches:
        campaign = match.group(1)
        episode = match.group(2)
        
        content.append({
            'week_date': week_date.strftime('%Y-%m-%d'),
            'show_type': 'Beacon Exclusive',
            'series': 'Critical Role Cooldown',
            'campaign': f'Campaign {campaign}',
            'episode_number': episode,
            'title': f'C{campaign}E{episode} Cooldown',
            'release_date': week_date.strftime('%Y-%m-%d'),
            'notes': 'Post-show reactions'
        })
    
    # Pattern 2: Fireside Chat (simplified)
    # Matches: "Fireside Chat LIVE Oops All Crew | Jan 2026" or "Fireside Chat with [guest]"
    fireside_pattern = r'Fireside\s+Chat(?:\s+LIVE)?(?:\s+Oops\s+All\s+Crew\s*\|\s*(\w+\s+\d+)|\s+with\s+([\w\s&,]+?))?(?=\s|$)'
    fireside_matches = list(re.finditer(fireside_pattern, text, re.IGNORECASE))

    for match in fireside_matches:
        # Check if this is an "Oops All Crew" special
        if match.group(1):
            month_year = match.group(1)
            title = f'Fireside Chat LIVE Oops All Crew | {month_year}'
        elif match.group(2):
            guest = match.group(2).strip()
            title = f'Fireside Chat with {guest}'
        else:
            title = 'Fireside Chat'

        content.append({
            'week_date': week_date.strftime('%Y-%m-%d'),
            'show_type': 'Beacon Exclusive',
            'series': 'Fireside Chat',
            'campaign': '',
            'episode_number': '',
            'title': title,
            'release_date': week_date.strftime('%Y-%m-%d'),
            'notes': 'Monthly AMA/Q&A'
        })
    
    # Pattern 3: Weird Kids (simplified)
    weird_pattern = r'Weird\s+Kids.*?Episode\s+(\d+)'
    weird_matches = re.finditer(weird_pattern, text, re.IGNORECASE)
    
    for match in weird_matches:
        episode = match.group(1)
        
        content.append({
            'week_date': week_date.strftime('%Y-%m-%d'),
            'show_type': 'Beacon Exclusive',
            'series': 'Weird Kids',
            'campaign': '',
            'episode_number': episode,
            'title': f'Weird Kids Episode {episode}',
            'release_date': week_date.strftime('%Y-%m-%d'),
            'notes': 'Ashley Johnson & Taliesin Jaffe podcast'
        })
    
    # Pattern 4: Backstage Pass
    backstage_pattern = r'(Backstage Pass|backstage tour).*?(LIVE|Airs).*?only on Beacon'
    backstage_matches = re.finditer(backstage_pattern, text, re.DOTALL | re.IGNORECASE)

    for match in backstage_matches:
        context_start = max(0, match.start() - 200)
        context_end = min(len(text), match.end() + 50)
        context = text[context_start:context_end]

        # Try to find the event name
        event_match = re.search(r'(Sydney|Melbourne|Chicago|Indianapolis|New York|Radio City|Daggerheart Critmas)', context, re.IGNORECASE)
        event = event_match.group(1) if event_match else 'Live Show'

        content.append({
            'week_date': week_date.strftime('%Y-%m-%d'),
            'show_type': 'Beacon Exclusive',
            'series': 'Backstage Pass',
            'campaign': '',
            'episode_number': '',
            'title': f'Backstage Pass - {event}',
            'release_date': '',
            'notes': 'Behind-the-scenes live stream'
        })

    # Pattern 5: The Long Rest
    # Matches: "The Long Rest | Story Title" or "The Long Rest" followed by story details
    long_rest_pattern = r'The\s+Long\s+Rest\s*\|?\s*([^\n\r]+?)(?=\s*(?:releases|airs|available|only on Beacon|\d+\s+minutes?|$))'
    long_rest_matches = re.finditer(long_rest_pattern, text, re.IGNORECASE)

    for match in long_rest_matches:
        story_title = match.group(1).strip()
        # Clean up any trailing punctuation or extra text
        story_title = re.sub(r'\s*\|?\s*$', '', story_title)

        if story_title and len(story_title) > 3:  # Make sure we got a real title
            full_title = f'The Long Rest | {story_title}' if story_title else 'The Long Rest'

            content.append({
                'week_date': week_date.strftime('%Y-%m-%d'),
                'show_type': 'Beacon Exclusive',
                'series': 'The Long Rest',
                'campaign': '',
                'episode_number': '',  # No episode numbers for this series
                'title': full_title,
                'release_date': week_date.strftime('%Y-%m-%d'),
                'notes': 'Bedtime stories read by CR cast'
            })

    # Pattern 6: Inside The Mighty Nein
    # Matches: "Inside The Mighty Nein | Episodes 6-8" or "Inside The Mighty Nein: Episodes 1-5"
    mighty_nein_pattern = r'Inside\s+The\s+Mighty\s+Nein.*?Episodes?\s+([\d\-]+)'
    mighty_nein_matches = re.finditer(mighty_nein_pattern, text, re.IGNORECASE)

    for match in mighty_nein_matches:
        episode_range = match.group(1)

        content.append({
            'week_date': week_date.strftime('%Y-%m-%d'),
            'show_type': 'Beacon Exclusive',
            'series': 'Inside The Mighty Nein',
            'campaign': '',
            'episode_number': episode_range,
            'title': f'Inside The Mighty Nein: Episodes {episode_range}',
            'release_date': week_date.strftime('%Y-%m-%d'),
            'notes': 'Talk show series'
        })

    # Pattern 7: Get Your Sheet Together
    gyst_pattern = r'Get\s+Your\s+Sheet\s+Together.*?Episode\s+(\d+)'
    gyst_matches = re.finditer(gyst_pattern, text, re.IGNORECASE)

    for match in gyst_matches:
        episode = match.group(1)

        content.append({
            'week_date': week_date.strftime('%Y-%m-%d'),
            'show_type': 'Beacon Exclusive',
            'series': 'Get Your Sheet Together',
            'campaign': '',
            'episode_number': episode,
            'title': f'Get Your Sheet Together Episode {episode}',
            'release_date': week_date.strftime('%Y-%m-%d'),
            'notes': 'Beacon exclusive series'
        })

    # Pattern 8: Previously On...
    # Matches: "Previously On… | The Soldier's Table" or "Meet The Characters of Campaign 4 | Ep 1-4 Recap"
    # Arc names typically end with "Table" so we capture up to that
    previously_on_patterns = [
        # "Previously On... | Arc Name" - capture arc name ending in Table
        r'Previously\s+On[…\.]+\s*\|\s*(.+?Table)(?:We|[A-Z])',
        r'(Meet\s+The\s+Characters\s+of\s+Campaign\s+\d+)\s*\|\s*Ep(?:isode)?s?\s+([\d\-]+)\s+Recap'
    ]

    for pattern in previously_on_patterns:
        previously_on_matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in previously_on_matches:
            if match.lastindex == 2:
                # "Meet The Characters" format
                title_part = match.group(1).strip()
                episode_range = match.group(2)
                full_title = f'{title_part} | Ep {episode_range} Recap'
            else:
                # "Previously On... | Arc Name" format
                arc_name = match.group(1).strip()
                full_title = f'Previously On... | {arc_name}'
                episode_range = ''

            content.append({
                'week_date': week_date.strftime('%Y-%m-%d'),
                'show_type': 'Beacon Exclusive',
                'series': 'Previously On...',
                'campaign': 'Campaign 4',
                'episode_number': episode_range,
                'title': full_title,
                'release_date': week_date.strftime('%Y-%m-%d'),
                'notes': 'Campaign 4 recap show'
            })

    # Pattern 9: Tale Gate (Campaign 4 talkback show)
    # Matches: "Tale Gate | The Soldier's Table" followed by description text
    # Arc names typically end with "Table" so we capture up to that, stopping at the next word
    tale_gate_pattern = r'Tale\s+Gate\s*\|\s*(.+?Table)(?:The\s+gate|[A-Z])'
    tale_gate_matches = re.finditer(tale_gate_pattern, text, re.IGNORECASE)

    for match in tale_gate_matches:
        arc_name = match.group(1).strip()
        full_title = f'Tale Gate | {arc_name}'

        content.append({
            'week_date': week_date.strftime('%Y-%m-%d'),
            'show_type': 'Beacon Exclusive',
            'series': 'Tale Gate',
            'campaign': 'Campaign 4',
            'episode_number': '',
            'title': full_title,
            'release_date': week_date.strftime('%Y-%m-%d'),
            'notes': 'Campaign 4 live talkback show'
        })

    # Pattern 10: Main Campaign 4 Episodes (for when wiki isn't updated yet)
    # Matches: "Critical Role | Campaign 4 | Episode 12" or similar
    c4_episode_pattern = r'Critical\s+Role\s*\|\s*Campaign\s+4\s*\|\s*Episode\s+(\d+)'
    c4_matches = re.finditer(c4_episode_pattern, text, re.IGNORECASE)

    for match in c4_matches:
        episode_num = match.group(1)

        # Try to extract episode title from surrounding text
        # Look for title patterns like "Title: ..." or just text after the episode number
        context_start = match.end()
        context_end = min(len(text), match.end() + 500)
        context = text[context_start:context_end]

        # Try to find a title - look for quoted text or descriptive text
        title = ''
        title_match = re.search(r'"([^"]+)"', context)
        if title_match:
            title = title_match.group(1)

        content.append({
            'week_date': week_date.strftime('%Y-%m-%d'),
            'show_type': 'Main Campaign',
            'series': 'Campaign Four',
            'campaign': 'Campaign Four',
            'episode_number': episode_num,
            'title': title if title else f'Campaign 4 Episode {episode_num}',
            'release_date': week_date.strftime('%Y-%m-%d'),
            'notes': 'Added from Beacon schedule (wiki pending)'
        })

    return content

def scrape_beacon_exclusives(start_date_str, end_date_str=None):
    """
    Scrape all Beacon-exclusive content from programming schedules
    """
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else datetime.now()

    print(f"Generating schedule URLs from {start_date.date()} to {end_date.date()}...")
    print(f"Using {'Playwright' if USE_PLAYWRIGHT else 'requests'} for fetching\n")
    urls = generate_schedule_urls(start_date, end_date)
    print(f"Found {len(urls)} weekly schedules to check (both critrole.com and beacon.tv)\n")

    all_content = []

    for week_date, url, source in urls:
        # Try both URL formats - with and without ordinal suffix
        url_without_suffix = url.replace('st-', '-').replace('nd-', '-').replace('rd-', '-').replace('th-', '-')

        success = False

        for attempt_url in [url, url_without_suffix]:
            if success:
                break

            print(f"Fetching {week_date.strftime('%Y-%m-%d')} [{source}]: {attempt_url}")

            html, fetch_success = fetch_url_with_retry(attempt_url, max_retries=2, timeout=15)

            if fetch_success and html:
                content = extract_beacon_content(html, week_date)
                if content:
                    print(f"  ✓ Found {len(content)} Beacon-exclusive items")
                    all_content.extend(content)
                else:
                    print(f"  - No Beacon content found")
                success = True
            else:
                print(f"  ✗ Failed to fetch (trying alternate URL format...)")

        # Be nice to the server
        time.sleep(1)

    return all_content

def save_to_csv(content, filename='beacon_exclusives.csv'):
    """
    Save extracted content to CSV
    """
    if not content:
        print("\nNo content to save!")
        return

    fieldnames = ['week_date', 'show_type', 'series', 'campaign', 'episode_number', 'title', 'release_date', 'notes']

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(content)

    print(f"\n✓ Saved {len(content)} items to {filename}")

    # Print summary
    series_counts = {}
    for item in content:
        series = item['series']
        series_counts[series] = series_counts.get(series, 0) + 1

    print("\nSummary by series:")
    for series, count in sorted(series_counts.items()):
        print(f"  {series}: {count}")

def merge_into_main_csv(scraped_content, main_csv='cr_episodes_series_airdates.csv'):
    """
    Merge scraped Beacon content into the main episodes CSV
    Returns number of new episodes added
    """
    if not scraped_content:
        print("\nNo new content to merge")
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

    # Build set of existing episode IDs
    existing_ids = {row['episode_id'] for row in existing_rows if row['episode_id']}

    # Build additional lookup sets for smarter duplicate detection
    # For Cooldowns: check if we already have a cooldown for that episode number
    existing_cooldowns = set()
    existing_fireside_chats = set()
    existing_weird_kids = set()
    existing_tale_gates = set()  # Track by arc name
    existing_previously_on = set()  # Track by arc name
    existing_c4_episodes = set()  # Track Campaign 4 episodes by number
    existing_backstage_pass = set()  # Track by event name

    for row in existing_rows:
        title = row.get('title', '').lower()
        ep_num = row.get('episode_number', '')
        campaign = row.get('campaign', '')
        show_type = row.get('show_type', '')

        # Track Cooldowns by episode number (handles C3x95 vs 95 mismatch)
        if 'cooldown' in campaign.lower() or 'cooldown' in title:
            # Extract episode number from various formats
            match = re.search(r'(?:C\d+[xE])?(\d+)', ep_num)
            if match:
                existing_cooldowns.add(match.group(1))

        # Track Fireside Chats by guest name (normalized)
        if 'fireside' in campaign.lower() or 'fireside' in title:
            # Extract guest name
            guest_match = re.search(r'with\s+(\w+)', title, re.IGNORECASE)
            if guest_match:
                existing_fireside_chats.add(guest_match.group(1).lower())

        # Track Weird Kids by episode number
        if 'weird kids' in campaign.lower() or 'weird kids' in title:
            if ep_num:
                existing_weird_kids.add(ep_num)

        # Track Tale Gate by arc name
        if 'tale gate' in campaign.lower() or 'tale gate' in title:
            arc_match = re.search(r'tale gate\s*\|\s*(.+)', title, re.IGNORECASE)
            if arc_match:
                existing_tale_gates.add(arc_match.group(1).strip().lower())

        # Track Previously On... by arc name
        if 'previously on' in campaign.lower() or 'previously on' in title:
            arc_match = re.search(r'previously on[…\.]+\s*\|\s*(.+)', title, re.IGNORECASE)
            if arc_match:
                existing_previously_on.add(arc_match.group(1).strip().lower())

        # Track Campaign 4 main episodes by episode number
        if show_type == 'Main Campaign' and ('campaign four' in campaign.lower() or 'campaign 4' in campaign.lower()):
            if ep_num:
                existing_c4_episodes.add(ep_num)

        # Track Backstage Pass by event name
        if 'backstage pass' in campaign.lower() or 'backstage pass' in title:
            event_match = re.search(r'backstage pass\s*-\s*(.+)', title, re.IGNORECASE)
            if event_match:
                existing_backstage_pass.add(event_match.group(1).strip().lower())

    # Convert scraped content to main CSV format and check for duplicates
    new_rows = []
    skipped = []

    for item in scraped_content:
        # Map series to proper format
        series_name = item['series']

        # Map each series to its correct show_type
        show_type_mapping = {
            'Critical Role Cooldown': 'Talk Show',
            'Fireside Chat': 'Fireside Chat',
            'Weird Kids': 'Webseries',
            'Backstage Pass': 'Backstage Pass',
            'The Long Rest': 'Webseries',
            'Inside The Mighty Nein': 'Talk Show',
            'Get Your Sheet Together': 'Webseries',
            'Previously On...': 'Talk Show',
            'Tale Gate': 'Talk Show',
            'Campaign Four': 'Main Campaign'
        }

        # Handle Campaign 4 main episodes differently
        if series_name == 'Campaign Four':
            show_type = 'Main Campaign'
            campaign = 'Campaign Four'
        else:
            show_type = show_type_mapping.get(series_name, 'Webseries')
            campaign = series_name

        # Generate episode_id
        episode_id = f"{show_type}|{campaign}|{item['episode_number']}|{item['title']}"

        # Skip if already exists (exact match)
        if episode_id in existing_ids:
            skipped.append(item['title'])
            continue

        # Smart duplicate detection for specific series
        ep_num = item['episode_number']

        # Check Cooldowns - skip if we already have a cooldown for this episode
        if series_name == 'Critical Role Cooldown' and ep_num:
            if ep_num in existing_cooldowns:
                skipped.append(f"{item['title']} (cooldown already exists for ep {ep_num})")
                continue

        # Check Fireside Chats - skip if we already have one with this guest
        if series_name == 'Fireside Chat':
            guest_match = re.search(r'with\s+(\w+)', item['title'], re.IGNORECASE)
            if guest_match:
                guest_name = guest_match.group(1).lower()
                if guest_name in existing_fireside_chats:
                    skipped.append(f"{item['title']} (fireside chat with {guest_name} already exists)")
                    continue

        # Check Weird Kids - skip if we already have this episode
        if series_name == 'Weird Kids' and ep_num:
            if ep_num in existing_weird_kids:
                skipped.append(f"{item['title']} (weird kids ep {ep_num} already exists)")
                continue

        # Check Tale Gate - skip if we already have this arc
        if series_name == 'Tale Gate':
            arc_match = re.search(r'tale gate\s*\|\s*(.+)', item['title'], re.IGNORECASE)
            if arc_match:
                arc_name = arc_match.group(1).strip().lower()
                if arc_name in existing_tale_gates:
                    skipped.append(f"{item['title']} (tale gate for {arc_name} already exists)")
                    continue

        # Check Previously On... - skip if we already have this arc
        if series_name == 'Previously On...':
            arc_match = re.search(r'previously on[…\.]+\s*\|\s*(.+)', item['title'], re.IGNORECASE)
            if arc_match:
                arc_name = arc_match.group(1).strip().lower()
                if arc_name in existing_previously_on:
                    skipped.append(f"{item['title']} (previously on for {arc_name} already exists)")
                    continue

        # Check Campaign 4 main episodes - skip if wiki already has it
        if series_name == 'Campaign Four' and ep_num:
            if ep_num in existing_c4_episodes:
                skipped.append(f"{item['title']} (C4 episode {ep_num} already exists from wiki)")
                continue

        # Check Backstage Pass - skip if we already have this event
        if series_name == 'Backstage Pass':
            event_match = re.search(r'backstage pass\s*-\s*(.+)', item['title'], re.IGNORECASE)
            if event_match:
                event_name = event_match.group(1).strip().lower()
                if event_name in existing_backstage_pass:
                    skipped.append(f"{item['title']} (backstage pass for {event_name} already exists)")
                    continue

        # Create new row
        new_row = {
            'episode_id': episode_id,
            'show_type': show_type,
            'campaign': campaign,
            'arc': '',
            'episode_number': item['episode_number'],
            'title': item['title'],
            'airdate': item['release_date'],
            'vod_url': 'https://www.beacon.tv',
            'wiki_url': '',
            'runtime': '',
            'watched': 'False',
            'notes': item['notes'],
            'has_cooldown': 'False',
            'cooldown_date': ''
        }

        new_rows.append(new_row)
        existing_ids.add(episode_id)

        # Update tracking sets to prevent duplicates within the same scrape
        if series_name == 'Critical Role Cooldown' and ep_num:
            existing_cooldowns.add(ep_num)
        if series_name == 'Fireside Chat':
            guest_match = re.search(r'with\s+(\w+)', item['title'], re.IGNORECASE)
            if guest_match:
                existing_fireside_chats.add(guest_match.group(1).lower())
        if series_name == 'Weird Kids' and ep_num:
            existing_weird_kids.add(ep_num)
        if series_name == 'Tale Gate':
            arc_match = re.search(r'tale gate\s*\|\s*(.+)', item['title'], re.IGNORECASE)
            if arc_match:
                existing_tale_gates.add(arc_match.group(1).strip().lower())
        if series_name == 'Previously On...':
            arc_match = re.search(r'previously on[…\.]+\s*\|\s*(.+)', item['title'], re.IGNORECASE)
            if arc_match:
                existing_previously_on.add(arc_match.group(1).strip().lower())
        if series_name == 'Campaign Four' and ep_num:
            existing_c4_episodes.add(ep_num)
        if series_name == 'Backstage Pass':
            event_match = re.search(r'backstage pass\s*-\s*(.+)', item['title'], re.IGNORECASE)
            if event_match:
                existing_backstage_pass.add(event_match.group(1).strip().lower())

    if skipped:
        print(f"\nSkipped {len(skipped)} existing episodes:")
        for title in skipped[:5]:
            print(f"  - {title}")
        if len(skipped) > 5:
            print(f"  ... and {len(skipped) - 5} more")

    if not new_rows:
        print("\nNo new episodes to add")
        return 0

    # Add new rows and sort by airdate
    all_rows = existing_rows + new_rows
    all_rows.sort(key=lambda x: x['airdate'] if x['airdate'] else '9999-99-99')

    # Write back to CSV
    with open(main_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n✓ Added {len(new_rows)} new episodes to {main_csv}")
    for row in new_rows:
        print(f"  + {row['campaign']} #{row['episode_number']}: {row['title']}")

    return len(new_rows)

if __name__ == '__main__':
    # Default to only check the last 4 weeks (current + 3 prior)
    # This makes the scraper much faster for regular updates
    today = datetime.now()
    four_weeks_ago = today - timedelta(days=28)
    start_date = four_weeks_ago.strftime('%Y-%m-%d')

    # Default to today
    end_date = None

    if len(sys.argv) > 1:
        start_date = sys.argv[1]
    if len(sys.argv) > 2:
        end_date = sys.argv[2]

    print("=" * 80)
    print("BEACON EXCLUSIVE CONTENT SCRAPER")
    print("=" * 80)
    print(f"Scraping CritRole.com programming schedules")
    print(f"Start date: {start_date}")
    print(f"End date: {end_date or 'today'}")
    print("=" * 80 + "\n")

    content = scrape_beacon_exclusives(start_date, end_date)

    # Save raw scrape results
    save_to_csv(content)

    # Merge new episodes into main CSV
    print("\n" + "=" * 80)
    print("MERGING INTO MAIN CSV")
    print("=" * 80)
    new_count = merge_into_main_csv(content)

    if new_count > 0:
        print(f"\n✓ Successfully added {new_count} new episode(s) to the tracker!")
    else:
        print("\n✓ No new episodes found - CSV is up to date!")
