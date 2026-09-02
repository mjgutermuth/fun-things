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
from collections import Counter
from itertools import permutations

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
    text_nl = soup.get_text(separator='\n')

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
    # Uses newline-separated text so the guest name captures to end-of-line, not just first word.
    fireside_pattern = r'Fireside\s+Chat(?:\s+LIVE)?(?:\s+Oops\s+All\s+Crew\s*\|\s*(\w+\s+\d+)|\s+with\s+(.+?))?(?=[\n\r]|$)'
    fireside_matches = list(re.finditer(fireside_pattern, text_nl, re.IGNORECASE))

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

    # Pattern 7: Inside The Legend of Vox Machina
    # Matches: "Inside The Legend of Vox Machina: Episodes 1-6"
    lovm_inside_pattern = r'Inside\s+The\s+Legend\s+of\s+Vox\s+Machina.*?Episodes?\s+([\d\-]+)'
    lovm_matched_spans = []

    for match in re.finditer(lovm_inside_pattern, text, re.IGNORECASE):
        episode_range = match.group(1)
        lovm_matched_spans.append(match.span())

        content.append({
            'week_date': week_date.strftime('%Y-%m-%d'),
            'show_type': 'Beacon Exclusive',
            'series': 'Inside The Legend of Vox Machina',
            'campaign': '',
            'episode_number': episode_range,
            'title': f'Inside The Legend of Vox Machina: Episodes {episode_range}',
            'release_date': week_date.strftime('%Y-%m-%d'),
            'notes': 'Talkback show for LoVM Season 4'
        })

    # Pattern 7b: Inside The Legend of Vox Machina season finale
    # The finale installment isn't labeled with an "Episodes N-M" range like the
    # earlier ones - the schedule copy just says "...our finale episode of
    # Inside The Legend of Vox Machina...", so Pattern 7 silently drops it.
    lovm_finale_pattern = r'Inside\s+The\s+Legend\s+of\s+Vox\s+Machina.{0,200}?finale'
    for match in re.finditer(lovm_finale_pattern, text, re.IGNORECASE):
        if any(start <= match.start() < end for start, end in lovm_matched_spans):
            continue  # already captured by the numbered-range pattern above

        content.append({
            'week_date': week_date.strftime('%Y-%m-%d'),
            'show_type': 'Beacon Exclusive',
            'series': 'Inside The Legend of Vox Machina',
            'campaign': '',
            'episode_number': '',
            'title': 'Inside The Legend of Vox Machina: Season Finale',
            'release_date': week_date.strftime('%Y-%m-%d'),
            'notes': 'Talkback show for LoVM Season 4'
        })

    # Pattern 8: Get Your Sheet Together
    # critrole.com's schedule text only ever exposes a bare sequential number
    # here ("...Episode N"), never the real episode subtitle - and that number
    # doesn't reliably match the tracker's own GYST numbering (seen: page said
    # "Episode 17" for what the tracker tracks as #10). beacon.tv's own
    # schedule page for the same week carries the real subtitle (e.g. "Using
    # Fear in Daggerheart!") with no "Episode N" text at all, so it's caught
    # separately by the generic fallback pass (Pattern 13) instead - that's
    # the reliable source of truth for GYST releases. Since this pattern's
    # match lives on a different page than the fallback's widget scan,
    # _widget_already_claimed can't dedupe the two against each other, so
    # this pattern must not emit its own row - it exists only so
    # _widget_already_claimed can still recognize (and skip) a GYST widget
    # that happens to say "Episode N" on the same page.
    gyst_pattern = r'Get\s+Your\s+Sheet\s+Together.*?Episode\s+(\d+)'

    # Pattern 9: Previously On...
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
                title_part = clean_scraped_text(match.group(1))
                episode_range = match.group(2)
                full_title = f'{title_part} | Ep {episode_range} Recap'
            else:
                # "Previously On... | Arc Name" format
                arc_name = clean_scraped_text(match.group(1))
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
        arc_name = clean_scraped_text(match.group(1))
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

        # Campaign 4 airs on Thursdays (3 days after Monday schedule date)
        thursday_date = week_date + timedelta(days=3)

        content.append({
            'week_date': week_date.strftime('%Y-%m-%d'),
            'show_type': 'Main Campaign',
            'series': 'Campaign Four',
            'campaign': 'Campaign Four',
            'episode_number': episode_num,
            'title': title if title else f'Campaign 4 Episode {episode_num}',
            'release_date': thursday_date.strftime('%Y-%m-%d'),
            'notes': 'Added from Beacon schedule (wiki pending)'
        })

    # Pattern 11: One-Shots
    # Use newline-separated text so the event title is on its own line, isolated from
    # description prose that also mentions "One-Shot". The old inline regex broke on
    # titles containing punctuation like "!" (e.g. "Hubris! A Darrington Brigade One-Shot")
    # and would fall through to match promo copy in the description instead.
    # Match whole lines: starts with a capital letter, ends with "One-Shot" / "One Shot"
    one_shot_pattern = r'^([A-Z][^\n]*?One[- ]Shot)\s*$'

    # Pattern 12: Live Shows
    # Matches lines like "Bells Hells & the Maelstrom Kingdom | Atlanta Live Show 2026"
    # These are one-off live event specials that don't end in "One-Shot"
    live_show_pattern = r'^([A-Z][^\n]*?Live Show \d{4})\s*$'

    # Words that indicate an actual schedule slot vs. promotional/archive text
    schedule_indicators = re.compile(
        r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|'
        r'airs|premieres|debuts|new episode|this week|only on beacon|'
        r'live on beacon|exclusively on beacon|available [a-z]+ on beacon)\b',
        re.IGNORECASE
    )

    # Dedup by the last two words before "One-Shot" (the series name), so that
    # "Hubris! A Darrington Brigade One-Shot" and "NEW Darrington Brigade One-Shot"
    # (which appears in description prose) are treated as the same event.
    seen_one_shot_series = set()
    for match in re.finditer(one_shot_pattern, text_nl, re.MULTILINE):
        title = match.group(1).strip()
        if len(title) < 15:
            continue

        # Extract series key: the last two words before "One-Shot"
        series_match = re.search(r'(.+?)\s+One[- ]Shot$', title, re.IGNORECASE)
        if not series_match:
            continue
        words_before = series_match.group(1).strip().split()
        series_key = ' '.join(words_before[-2:]).lower()

        if series_key in seen_one_shot_series:
            continue

        # Require scheduling context nearby — use a wider window since the newline
        # separator adds chars and the date line may be several elements away
        context_start = max(0, match.start() - 400)
        context_end = min(len(text_nl), match.end() + 400)
        context = text_nl[context_start:context_end]
        if not schedule_indicators.search(context):
            continue

        seen_one_shot_series.add(series_key)

        content.append({
            'week_date': week_date.strftime('%Y-%m-%d'),
            'show_type': 'Beacon Exclusive',
            'series': 'One-Shot',
            'campaign': '',
            'episode_number': '',
            'title': title,
            'release_date': week_date.strftime('%Y-%m-%d'),
            'notes': 'One-shot adventure'
        })

    seen_live_shows = set()
    for match in re.finditer(live_show_pattern, text_nl, re.MULTILINE):
        title = clean_live_show_title(match.group(1).strip())

        if title.lower() in seen_live_shows:
            continue

        context_start = max(0, match.start() - 400)
        context_end = min(len(text_nl), match.end() + 400)
        context = text_nl[context_start:context_end]
        if not schedule_indicators.search(context):
            continue

        seen_live_shows.add(title.lower())

        content.append({
            'week_date': week_date.strftime('%Y-%m-%d'),
            'show_type': 'Special',
            'series': 'Live Show',
            'campaign': '',
            'episode_number': '',
            'title': title,
            'release_date': week_date.strftime('%Y-%m-%d'),
            'notes': 'CR live show'
        })

    # Pattern 13: Generic fallback for anything not caught by the patterns above.
    # Patterns 1-12 only recognize a fixed set of known series; anything else on
    # the schedule page (a brand-new miniseries, a webseries with no dedicated
    # pattern, etc.) was previously silently dropped. Default to including it
    # instead - see EXCLUDED_TITLE_KEYWORDS for the explicit, narrow opt-out list.
    def _widget_already_claimed(widget_text, widget_text_nl):
        """Would any of patterns 1-12 above already match this widget's own
        text? If so, they already produced a (correctly tuned) row for it
        elsewhere in this function, and the fallback must not add a second one."""
        checks = [
            (cooldown_pattern, widget_text, re.IGNORECASE),
            (fireside_pattern, widget_text_nl, re.IGNORECASE),
            (weird_pattern, widget_text, re.IGNORECASE),
            (backstage_pattern, widget_text, re.DOTALL | re.IGNORECASE),
            (long_rest_pattern, widget_text, re.IGNORECASE),
            (mighty_nein_pattern, widget_text, re.IGNORECASE),
            (lovm_inside_pattern, widget_text, re.IGNORECASE),
            (lovm_finale_pattern, widget_text, re.IGNORECASE),
            (gyst_pattern, widget_text, re.IGNORECASE),
            (previously_on_patterns[0], widget_text, re.IGNORECASE),
            (previously_on_patterns[1], widget_text, re.IGNORECASE),
            (tale_gate_pattern, widget_text, re.IGNORECASE),
            (c4_episode_pattern, widget_text, re.IGNORECASE),
            (one_shot_pattern, widget_text_nl, re.MULTILINE),
            (live_show_pattern, widget_text_nl, re.MULTILINE),
        ]
        return any(re.search(pattern, t, flags) for pattern, t, flags in checks)

    for widget in soup.find_all('div', class_='elementor-widget-container'):
        h3 = widget.find('h3')
        ul = widget.find('ul')
        if not h3 or not ul:
            continue  # not a schedule item (e.g. the page's intro blurb widget)

        widget_text = widget.get_text()
        widget_text_nl = widget.get_text(separator='\n')

        if _widget_already_claimed(widget_text, widget_text_nl):
            continue  # a tuned pattern above already extracted this

        raw_title = h3.get_text(separator=' ', strip=True)
        if not raw_title or is_excluded_from_generic_fallback(raw_title):
            continue

        # Fix punctuation (curly quotes/dashes/ellipsis) and drop empty
        # pipe-segments (get_text() sometimes glues two text nodes that each
        # already contained a "|", e.g. a badge/icon element between them
        # producing no text of its own - see clean_live_show_title) before
        # this raw text is split apart or stored anywhere below.
        segments = [s.strip() for s in clean_scraped_text(raw_title).split('|')]
        segments = [s for s in segments if s]
        series_prefix_override, segments = split_generic_series_prefix(segments)
        cleaned_title = ' | '.join(segments) if segments else raw_title

        first_li = ul.find('li')
        first_li_text = first_li.get_text(' ', strip=True) if first_li else ''

        is_cooldown, series_key, episode_number = parse_generic_title(cleaned_title)
        campaign_key = series_key
        if series_prefix_override:
            series_key = series_prefix_override
            campaign_key = ''
        release_date = parse_release_date_from_li(first_li_text, week_date)

        note = ('Added from Beacon schedule (auto-detected, please verify)'
                if episode_number else
                'Added from Beacon schedule (auto-detected, non-standard title - '
                'please verify this belongs in the tracker)')

        content.append({
            'week_date': week_date.strftime('%Y-%m-%d'),
            'show_type': 'Beacon Exclusive',
            'series': 'Critical Role Cooldown' if is_cooldown else series_key,
            'campaign': campaign_key,
            'episode_number': episode_number,
            'title': cleaned_title,
            'release_date': release_date,
            'notes': note,
            'is_generic_fallback': True,
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

    fieldnames = ['week_date', 'show_type', 'series', 'campaign', 'episode_number', 'title', 'release_date', 'notes', 'is_generic_fallback']

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

def validate_title(title, series_name):
    """
    Validate that a title is complete and well-formed.
    Returns (is_valid, reason) tuple.
    """
    if not title or len(title) < 5:
        return False, "Title too short"

    # Check for truncated titles (ending mid-word or with incomplete phrases)
    truncated_patterns = [
        r'\bwith\s+\w{1,3}$',  # "with our", "with the" - incomplete
        r'\bthe\s*$',  # ends with "the"
        r'\band\s*$',  # ends with "and"
        r'\bof\s*$',  # ends with "of"
    ]
    for pattern in truncated_patterns:
        if re.search(pattern, title, re.IGNORECASE):
            return False, f"Title appears truncated: '{title}'"

    # Check for generic/placeholder titles that shouldn't be added
    if series_name == 'Backstage Pass' and title == 'Backstage Pass - Live Show':
        return False, "Generic backstage pass entry without specific event"

    return True, None


def validate_episode_number(ep_num, series_name, existing_episodes):
    """
    Validate that an episode number is reasonable.
    Returns (is_valid, reason) tuple.
    """
    if not ep_num:
        return True, None  # Empty episode numbers are OK for some series

    try:
        num = int(ep_num)
    except ValueError:
        return True, None  # Non-numeric episode numbers are OK (e.g., "1-4")

    # For Weird Kids, check for unreasonable jumps
    if series_name == 'Weird Kids' and existing_episodes:
        max_existing = max(int(e) for e in existing_episodes if e.isdigit())
        if num > max_existing + 5:  # Allow some gap but not huge jumps
            return False, f"Episode {num} is too far ahead of max existing ({max_existing})"

    return True, None


def normalize_text(text):
    """
    Normalize scraped text for duplicate-detection comparisons.
    Source pages inconsistently use non-breaking spaces, curly quotes/dashes,
    and inconsistent capitalization between scrapes of the same content, which
    defeats plain exact-string dedup. This folds all of that away so identical
    content compares equal regardless of which scrape produced it.
    """
    if not text:
        return ''
    t = text.replace('\xa0', ' ')
    t = t.replace('‘', "'").replace('’', "'")
    t = t.replace('–', '-').replace('—', '-')
    t = re.sub(r'\s+', ' ', t)
    return t.strip().lower()


def clean_scraped_text(text):
    """
    Clean scraped text for display/storage (as opposed to normalize_text(),
    which lowercases and collapses punctuation for comparison only). Source
    pages inconsistently use curly quotes/dashes/ellipsis and non-breaking
    spaces even between scrapes of the same show, which is what made e.g.
    "Previously On..." show up in the tracker as both the ASCII spelling and
    "Previously On…" depending on which schedule page/pattern caught it.
    Preserves original casing and wording - only normalizes punctuation.
    """
    if not text:
        return ''
    t = text.replace('\xa0', ' ')
    t = t.replace('‘', "'").replace('’', "'")
    t = t.replace('“', '"').replace('”', '"')
    t = t.replace('–', '-').replace('—', '-')
    t = t.replace('…', '...')
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


def extract_arc_name(title):
    """
    Extract the arc/episode name from titles with pipe separators.
    Works for "Previously On... | Arc Name" and "Tale Gate | Arc Name" formats.
    """
    if '|' in title:
        return normalize_text(title.split('|', 1)[1])
    return normalize_text(title)


def clean_live_show_title(title):
    """
    Drop empty pipe-segments from a scraped Live Show title before storing it.

    The source schedule page sometimes renders a badge/icon element between
    two text segments that produces no text, leaving a stray "| |" in the
    line captured by get_text(). Collapsing those empty segments (but keeping
    real ones, and their original casing) turns e.g.
    "Darktow | | Echoes of Exandria | Edinburgh Live Show 2026" into
    "Darktow | Echoes of Exandria | Edinburgh Live Show 2026".
    """
    segments = [s.strip() for s in title.split('|')]
    segments = [s for s in segments if s]
    return ' | '.join(segments)


def normalize_live_show_title(title):
    """
    Normalize a Live Show title for duplicate detection.

    critrole.com re-promotes the same live show release across multiple weekly
    schedule pages, and the blurb is sometimes reworded slightly between
    postings (e.g. a "| Critical Role |" segment gets added or dropped). That
    defeats plain exact-string dedup, producing a second row for what's really
    the same release. Dropping empty/filler pipe-segments (just "critical
    role") folds those cosmetic rewrites away, while still keeping distinct
    same-event pieces (e.g. a Backstage Pass teaser vs. its later "Road To..."
    follow-up, or the main show vs. its Cooldown) as separate segments so they
    aren't incorrectly collapsed together.
    """
    segments = [normalize_text(s) for s in title.split('|')]
    segments = [s for s in segments if s and s != 'critical role']
    return '|'.join(segments)


# Live Show rows whose stored `title` was manually rewritten from the raw
# scraped pipe-delimited form into a cleaner, reworded sentence (segments
# collapsed/reordered, "Critical Role Cooldown" shortened to "Cooldown:",
# etc). normalize_live_show_title() compares segment-for-segment, so once a
# title is reworded like this it no longer matches what a fresh scrape of
# the same event produces - the segments and their order are gone. Rather
# than fuzzy-match on word overlap (tried and rejected: a show and its own
# Cooldown score 0.90 similarity by word-overlap, since "Cooldown:" is a
# single differing word among many shared ones - a generic similarity
# threshold cannot safely tell them apart), each already-cleaned-up event is
# listed explicitly here as a set of required keywords, checked against the
# RAW incoming scraped title (case-insensitive substring match on every
# keyword). This is intentionally an allowlist of known past events, not a
# general heuristic - safe by construction, but needs a new entry whenever
# another Live Show row's title gets manually cleaned up like this.
_MANUALLY_REWORDED_LIVE_SHOWS = [
    ('atlanta', 'maelstrom', 'cooldown'),   # Cooldown: The Maelstrom Kingdom – Atlanta Live Show 2026
    ('atlanta', 'maelstrom', 'bells hells'),  # Bells Hells & the Maelstrom Kingdom – Atlanta Live Show 2026 (now One-Shot)
    ('berlin', 'funball', 'cooldown'),       # Cooldown: [PROJEKT] Funball – Berlin Live Show 2026
    ('berlin', 'funball'),                   # [PROJEKT] Funball – Berlin Live Show 2026 (now One-Shot)
    ('edinburgh', 'darktow', 'cooldown'),    # Cooldown: Darktow – Edinburgh Live Show 2026
    ('edinburgh', 'darktow', 'echoes'),      # Echoes of Exandria: Darktow – Edinburgh Live Show 2026 (now One-Shot)
    ('edinburgh', 'darktow', 'vip'),         # Darktow Backstage Pass – VIP Access: Edinburgh Live Show 2026
    ('edinburgh', 'darktow', 'road'),        # Darktow Backstage Pass – Road to Edinburgh Live Show 2026
]


def is_manually_reworded_live_show_duplicate(scraped_title):
    """Check a raw scraped Live Show title against the allowlist above."""
    t = scraped_title.lower()
    return any(all(kw in t for kw in keywords) for keywords in _MANUALLY_REWORDED_LIVE_SHOWS)


# Same problem as _MANUALLY_REWORDED_LIVE_SHOWS above, but for rows the generic
# fallback pass (Pattern 13 in extract_beacon_content) added and that were then
# hand-cleaned into a nicer title/campaign/arc split. Keyed on (required
# keywords in the RAW scraped title, episode_number) since the fallback's own
# dedup can't rely on a cleaned-up title matching the raw scrape anymore.
# Add a new entry here whenever a generic-fallback row's title gets rewritten.
_MANUALLY_REWORDED_GENERIC_ROWS = [
    (('age of umbra', 'sallowlands'), '1'),  # -> "Sallowlands: Scattered Pilgrims"
    (('age of umbra', 'sallowlands'), '2'),  # -> "Sallowlands: The Onyx Spire"
    (('age of umbra', 'sallowlands'), '3'),  # -> "Sallowlands: Horizon of Promise"
    (('age of umbra', 'sallowlands'), '4'),  # -> "Sallowlands: Call of the Wild Hearts"
    (('age of umbra', 'sallowlands'), '5'),  # -> "Sallowlands: Delaying Deliverance"
    (('age of umbra', 'sallowlands'), '6'),  # -> "Sallowlands: The Ancient Wound"
    (('get your sheet together', 'step into the spotlight'), ''),  # -> GYST #10 "Step into the Spotlight"
    (('funball', 'echoes of exandria', 'berlin'), ''),  # -> "Echoes of Exandria: [PROJEKT] Funball (Berlin Live Show 2026)"
    (('discussing up to c4e31',), ''),  # -> Tale Gate "Discussing Up To C4E31" (also caught a second, differently-worded widget for the same episode - keyword alone covers both)
]


def is_manually_reworded_generic_duplicate(scraped_title, episode_number):
    t = scraped_title.lower()
    return any(ep == episode_number and all(kw in t for kw in keywords)
               for keywords, ep in _MANUALLY_REWORDED_GENERIC_ROWS)


# Series that show up on the schedule page wrapped in a "<Series Name> |
# <Subtitle>" site-navigation-style prefix, where the tracker's own
# convention (see the manually-curated rows, e.g. "How to Play Daggerheart!",
# "Level Up in Daggerheart!") is to store the series name in the `series`
# column and just the bare subtitle as the `title` - not the full breadcrumb
# string. Pattern 8's comment above documents that GYST releases are
# expected to land via this fallback pass with the real subtitle intact,
# but the prefix segment was never being split off before storage. Keyed by
# normalize_text() of the prefix segment -> canonical series name.
_GENERIC_FALLBACK_KNOWN_SERIES_PREFIXES = {
    'get your sheet together': 'Get Your Sheet Together',
    'gyst': 'Get Your Sheet Together',
}


def split_generic_series_prefix(segments):
    """
    If the first pipe-segment of a Pattern 13 fallback title is a known
    series-navigation prefix (see _GENERIC_FALLBACK_KNOWN_SERIES_PREFIXES),
    split it off. Returns (series_override, remaining_segments) - series_override
    is None when no known prefix matched, in which case the segments are
    returned unchanged and the caller should fall back to its usual
    series-detection logic.
    """
    if len(segments) > 1:
        key = normalize_text(segments[0])
        if key in _GENERIC_FALLBACK_KNOWN_SERIES_PREFIXES:
            return _GENERIC_FALLBACK_KNOWN_SERIES_PREFIXES[key], segments[1:]
    return None, segments


def parse_generic_title(raw_title):
    """
    Split a schedule widget's <h3> title into (is_cooldown, series_key, episode_number)
    for the generic fallback pass (see extract_beacon_content).

    Handles the same pipe-segment convention as the site's other titles:
      "Age of Umbra: Sallowlands | Episode 4"
        -> (False, "Age of Umbra: Sallowlands", "4")
      "Critical Role Cooldown | Age of Umbra: Sallowlands | Episode 4"
        -> (True, "Age of Umbra: Sallowlands", "4")
      "Age of Umbra: Sallowlands | Level Up!"
        -> (False, "Age of Umbra: Sallowlands | Level Up!", "")  # last segment isn't "Episode N"
      "UNEND Season 3"
        -> (False, "UNEND Season 3", "")
    """
    segments = [s.strip() for s in raw_title.split('|') if s.strip()]
    is_cooldown = bool(segments) and normalize_text(segments[0]) == 'critical role cooldown'
    if is_cooldown:
        segments = segments[1:]

    episode_number = ''
    if segments:
        ep_match = re.fullmatch(r'Episode\s+(\d+)', segments[-1], re.IGNORECASE)
        if ep_match:
            episode_number = ep_match.group(1)
            segments = segments[:-1]

    series_key = ' | '.join(segments) if segments else raw_title
    return is_cooldown, series_key, episode_number


_WEEKDAY_OFFSETS = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                     'friday': 4, 'saturday': 5, 'sunday': 6}


def parse_release_date_from_li(li_text, week_date):
    """
    Derive the actual release date from a widget's first <li> line (e.g.
    "Airs Thursday, July 30th at 7pm Pacific on Twitch and YouTube"), rather
    than stamping every item with the schedule page's own Monday date. Falls
    back to week_date if no weekday name is found.
    """
    match = re.search(r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
                       li_text, re.IGNORECASE)
    if not match:
        return week_date.strftime('%Y-%m-%d')
    offset = _WEEKDAY_OFFSETS[match.group(1).lower()]
    return (week_date + timedelta(days=offset)).strftime('%Y-%m-%d')


# Content that shows up on critrole.com schedule pages but is deliberately out
# of scope for this tracker: third-party/adjacent shows (not Critical Role's
# own cast/content) and pure teaser posts with no real content yet. This is
# the ONLY place the generic fallback pass silently drops something - anything
# else, including bonus/tutorial segments of an existing or brand-new series
# (e.g. "GYST | Multiclassing in Daggerheart!"), defaults to being added.
# Matched as a case-insensitive substring against the widget's raw title.
EXCLUDED_TITLE_KEYWORDS = [
    'viva la dirt league',
    'tales from the stinky dragon',
    'unend season',
    'critical role abridged',
    'something is coming',
]


def is_excluded_from_generic_fallback(title):
    # normalize_text() doesn't touch pipe separators, but source titles often
    # pipe-delimit words that should read as a single phrase for this check
    # (e.g. "UNEND | Season 3 Roundtable" needs to match 'unend season').
    t = re.sub(r'\s+', ' ', normalize_text(title).replace('|', ' ')).strip()
    return any(kw in t for kw in EXCLUDED_TITLE_KEYWORDS)


def extract_fireside_guests(title):
    """
    Extract a normalized, order-independent guest key from a Fireside Chat title.
    Guards against duplicate rows caused by cosmetic differences between scrapes:
    guest order ("A & B" vs "B & A"), separator ("&" vs "and"), trailing punctuation
    ("!"), dangling fragments ("... from"), trailing "| Month Year" suffixes, and
    curly vs straight apostrophes. Returns a sorted tuple of guest names, or None.
    """
    match = re.search(r'with\s+(.+)', title, re.IGNORECASE)
    if not match:
        return None
    guests = normalize_text(match.group(1))
    guests = re.sub(r'\|\s*\w+\s+\d{4}\s*$', '', guests)  # trailing "| Month Year"
    guests = re.sub(r'[!.]+\s*$', '', guests)
    guests = re.sub(r'\bfrom\s*$', '', guests, flags=re.IGNORECASE)
    guests = guests.strip()
    parts = re.split(r'\s*(?:&|,|\band\b)\s*', guests, flags=re.IGNORECASE)
    parts = tuple(sorted(p.strip().lower() for p in parts if p.strip()))
    return parts or None


def _fireside_names_match(name_a, name_b):
    """A guest may be scraped as just a first name before the full name is
    announced (e.g. "Whitney" vs "Whitney Moore" for the same chat)."""
    if name_a == name_b:
        return True
    return name_a.startswith(name_b + ' ') or name_b.startswith(name_a + ' ')


def fireside_guests_match(guests_a, guests_b):
    """Check whether two guest tuples (from extract_fireside_guests) refer to
    the same lineup, tolerating first-name-only vs full-name mismatches."""
    if len(guests_a) != len(guests_b):
        return False
    return any(
        all(_fireside_names_match(a, b) for a, b in zip(guests_a, perm))
        for perm in permutations(guests_b)
    )


def merge_into_main_csv(scraped_content, main_csv='cr_episodes_series_airdates.csv'):
    """
    Merge scraped Beacon content into the main episodes CSV.
    Returns (new_rows, skipped) - the rows actually added, and a list of
    human-readable reasons for everything that was skipped as a duplicate -
    so a caller (e.g. the weekly changelog) can report exactly what happened
    without re-deriving it.
    """
    if not scraped_content:
        print("\nNo new content to merge")
        return [], []

    # Read existing CSV
    try:
        with open(main_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing_rows = list(reader)
            fieldnames = reader.fieldnames
    except FileNotFoundError:
        print(f"Error: {main_csv} not found")
        return [], []

    # Build set of existing episode IDs (exact and normalized, so cosmetic scrape
    # drift like non-breaking spaces or curly quotes doesn't create a duplicate row)
    existing_ids = {row['episode_id'] for row in existing_rows if row['episode_id']}
    existing_ids_normalized = {normalize_text(row['episode_id']) for row in existing_rows if row['episode_id']}

    # Established campaign names (and their usual show_type), keyed by
    # normalize_text() so a generic-fallback row can fold into one of these
    # by exact name match instead of minting a new one-off category out of
    # unrecognized raw scraped text (see the fold-or-blank logic below).
    existing_campaign_display = {}
    existing_campaign_show_types = {}
    for row in existing_rows:
        campaign = row.get('campaign', '')
        if not campaign:
            continue
        key = normalize_text(campaign)
        existing_campaign_display.setdefault(key, campaign)
        existing_campaign_show_types.setdefault(key, Counter())
        existing_campaign_show_types[key][row.get('show_type', '')] += 1

    # Build additional lookup sets for smarter duplicate detection
    # For Cooldowns: check if we already have a cooldown for that episode number
    existing_cooldowns = set()
    existing_fireside_chats = set()
    existing_weird_kids = set()
    existing_tale_gates = set()  # Track by arc name
    existing_previously_on = set()  # Track by arc name
    existing_c4_episodes = set()  # Track Campaign 4 episodes by number
    existing_live_shows = set()  # Track by normalized (filler-stripped) title
    existing_backstage_pass = set()  # Track by event name
    existing_one_shots = set()  # Track by normalized title
    # Track normalized titles to catch duplicates with different episode numbers
    existing_normalized_titles = set()

    for row in existing_rows:
        title = row.get('title', '').lower()
        ep_num = row.get('episode_number', '')
        campaign = row.get('campaign', '')
        show_type = row.get('show_type', '')

        # Track Cooldowns by (campaign_prefix, episode_number) to differentiate C4 vs Candela etc.
        if 'cooldown' in campaign.lower() or 'cooldown' in title:
            # Extract episode number from various formats
            match = re.search(r'(?:C\d+[xE])?(\d+)', ep_num)
            if match:
                # Determine campaign prefix from title or campaign field
                campaign_prefix = ''
                if 'campaign four' in campaign.lower() or '(c4)' in title.lower() or 'c4e' in ep_num.lower():
                    campaign_prefix = 'c4'
                elif 'candela' in campaign.lower() or '(candela)' in title.lower():
                    campaign_prefix = 'candela'
                elif 'campaign three' in campaign.lower() or '(c3)' in title.lower() or 'c3' in ep_num.lower():
                    campaign_prefix = 'c3'
                else:
                    # Generic-fallback cooldowns (any series without a dedicated
                    # pattern) would otherwise all collide in a shared '' bucket -
                    # bucket by the parent series' own name instead, so e.g. two
                    # unrelated minis both airing "Episode 3" don't collide.
                    campaign_prefix = normalize_text(row.get('arc') or extract_arc_name(row.get('title', '')))
                existing_cooldowns.add((campaign_prefix, match.group(1)))

        # Track Fireside Chats by normalized, order-independent guest set
        if 'fireside' in campaign.lower() or 'fireside' in title:
            guests = extract_fireside_guests(row.get('title', ''))
            if guests:
                existing_fireside_chats.add(guests)

        # Track Weird Kids by episode number
        if 'weird kids' in campaign.lower() or 'weird kids' in title:
            if ep_num:
                existing_weird_kids.add(ep_num)

        # Track Tale Gate by arc name (use simple pipe split for robustness)
        if 'tale gate' in campaign.lower() or 'tale gate' in title:
            arc_name = extract_arc_name(title)
            if arc_name and arc_name != normalize_text(title):  # Only add if we extracted something
                existing_tale_gates.add(arc_name)
            # Also track normalized title to catch duplicates with different episode numbers
            existing_normalized_titles.add(('tale gate', normalize_text(title)))

        # Track Previously On... by arc name (use simple pipe split for robustness)
        if 'previously on' in campaign.lower() or 'previously on' in title:
            arc_name = extract_arc_name(title)
            if arc_name and arc_name != normalize_text(title):  # Only add if we extracted something
                existing_previously_on.add(arc_name)
            # Also track normalized title to catch duplicates with different episode numbers
            existing_normalized_titles.add(('previously on', normalize_text(title)))

        # Track Campaign 4 main episodes by episode number
        if show_type == 'Main Campaign' and ('campaign four' in campaign.lower() or 'campaign 4' in campaign.lower()):
            if ep_num:
                existing_c4_episodes.add(ep_num)

        # Track Backstage Pass by event name
        if 'backstage pass' in campaign.lower() or 'backstage pass' in title:
            event_match = re.search(r'backstage pass\s*-\s*(.+)', title, re.IGNORECASE)
            if event_match:
                existing_backstage_pass.add(normalize_text(event_match.group(1)))

        # Track One-Shots by normalized title
        if 'one-shot' in campaign.lower() or 'one-shot' in title or 'one shot' in title:
            existing_one_shots.add(normalize_text(title))

        # Track Live Shows by filler-stripped title (catches re-promoted events
        # whose blurb was reworded slightly between weekly schedule postings).
        # Scraped Live Show items always land as show_type='Special', but a row
        # can get manually recategorized afterward (the live show itself into
        # One-Shot, or its Cooldown into Talk Show/Critical Role Cooldown) -
        # keep tracking those too so a rescrape doesn't re-add them as a
        # fresh 'Special' duplicate under the old wording.
        if show_type == 'Special' or show_type == 'One-Shot' or (
            show_type == 'Talk Show' and campaign == 'Critical Role Cooldown' and 'live show' in title
        ):
            existing_live_shows.add(normalize_live_show_title(row.get('title', '')))

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
            'Inside The Legend of Vox Machina': 'Talk Show',
            'Get Your Sheet Together': 'Webseries',
            'Previously On...': 'Talk Show',
            'Tale Gate': 'Talk Show',
            'Campaign Four': 'Main Campaign',
            'One-Shot': 'One-Shot',
            'Live Show': 'Special'
        }

        # Handle series that need a campaign name different from the series name
        if series_name == 'Campaign Four':
            show_type = 'Main Campaign'
            campaign = 'Campaign Four'
        elif series_name == 'Live Show':
            show_type = 'Special'
            campaign = 'Specials'
        elif series_name in show_type_mapping:
            show_type = show_type_mapping[series_name]
            campaign = series_name
        elif item.get('is_generic_fallback'):
            # series_name is raw, unrecognized scraped text - often a
            # pipe-joined "<Segment> | <Segment> | ..." string (e.g. a site
            # nav breadcrumb or a subtitle glued onto a known show name).
            # Rather than minting a brand-new one-off category out of it
            # (every such string would become its own permanent, never-to-
            # recur "campaign"), try folding the first segment into an
            # ALREADY-ESTABLISHED campaign by exact name match, and
            # otherwise leave campaign blank so it surfaces for manual
            # triage (e.g. via edit_titles.py) instead of silently becoming
            # noise in the series/campaign list.
            segments = [s.strip() for s in item['title'].split('|') if s.strip()]
            fold_key = normalize_text(segments[0]) if len(segments) > 1 else ''
            if fold_key in existing_campaign_display:
                campaign = existing_campaign_display[fold_key]
                show_type = existing_campaign_show_types[fold_key].most_common(1)[0][0]
                item = dict(item)
                item['title'] = ' | '.join(segments[1:])
                series_name = campaign
            else:
                show_type = 'Webseries'
                campaign = ''
        else:
            show_type = show_type_mapping.get(series_name, 'Webseries')
            campaign = series_name

        # Generate episode_id
        episode_id = f"{show_type}|{campaign}|{item['episode_number']}|{item['title']}"

        # Skip if already exists (exact match, or same after normalizing cosmetic
        # scrape drift like non-breaking spaces, curly quotes, or capitalization)
        if episode_id in existing_ids or normalize_text(episode_id) in existing_ids_normalized:
            skipped.append(item['title'])
            continue

        # Validate title - skip truncated or malformed titles
        title_valid, title_reason = validate_title(item['title'], series_name)
        if not title_valid:
            skipped.append(f"{item['title']} ({title_reason})")
            continue

        # Smart duplicate detection for specific series
        ep_num = item['episode_number']

        # Validate episode number - skip unreasonable episode numbers
        ep_valid, ep_reason = validate_episode_number(ep_num, series_name, existing_weird_kids)
        if not ep_valid:
            skipped.append(f"{item['title']} ({ep_reason})")
            continue

        # Determine cooldown campaign prefix from title (used for tracking)
        # Must handle both wiki format "(C3)" and beacon placeholder format "C3E"
        cooldown_prefix = ''
        title_lower = item['title'].lower()
        if series_name == 'Critical Role Cooldown':
            if '(c4)' in title_lower or 'c4e' in title_lower:
                cooldown_prefix = 'c4'
            elif '(candela)' in title_lower:
                cooldown_prefix = 'candela'
            elif '(c3)' in title_lower or 'c3e' in title_lower:
                cooldown_prefix = 'c3'
            else:
                # Generic-fallback (or any other campaign-numbered) cooldown -
                # bucket by its own parent series/campaign instead of the
                # shared '' bucket, matching the CSV-scan side above.
                cooldown_prefix = normalize_text(item.get('campaign', ''))

        # Check Cooldowns - skip if we already have a cooldown for this campaign/episode
        if series_name == 'Critical Role Cooldown' and ep_num:
            if (cooldown_prefix, ep_num) in existing_cooldowns:
                skipped.append(f"{item['title']} (cooldown already exists for {cooldown_prefix} ep {ep_num})")
                continue

        # Check Fireside Chats - skip if we already have one with this guest combination
        if series_name == 'Fireside Chat':
            guests = extract_fireside_guests(item['title'])
            if guests and any(fireside_guests_match(guests, existing) for existing in existing_fireside_chats):
                skipped.append(f"{item['title']} (fireside chat with {', '.join(guests)} already exists)")
                continue

        # Check Weird Kids - skip if we already have this episode
        if series_name == 'Weird Kids' and ep_num:
            if ep_num in existing_weird_kids:
                skipped.append(f"{item['title']} (weird kids ep {ep_num} already exists)")
                continue

        # Check Tale Gate - skip if we already have this arc or same title
        if series_name == 'Tale Gate':
            arc_name = extract_arc_name(item['title'])
            if arc_name in existing_tale_gates:
                skipped.append(f"{item['title']} (tale gate for {arc_name} already exists)")
                continue
            if ('tale gate', normalize_text(item['title'])) in existing_normalized_titles:
                skipped.append(f"{item['title']} (tale gate with same title already exists)")
                continue

        # Check Previously On... - skip if we already have this arc or same title
        if series_name == 'Previously On...':
            arc_name = extract_arc_name(item['title'])
            if arc_name in existing_previously_on:
                skipped.append(f"{item['title']} (previously on for {arc_name} already exists)")
                continue
            if ('previously on', normalize_text(item['title'])) in existing_normalized_titles:
                skipped.append(f"{item['title']} (previously on with same title already exists)")
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
                event_name = normalize_text(event_match.group(1))
                if event_name in existing_backstage_pass:
                    skipped.append(f"{item['title']} (backstage pass for {event_name} already exists)")
                    continue

        # Check One-Shots - skip if we already have this title (or a substring match)
        if series_name == 'One-Shot':
            title_norm = normalize_text(item['title'])
            if title_norm in existing_one_shots or any(
                existing in title_norm or title_norm in existing
                for existing in existing_one_shots
            ):
                skipped.append(f"{item['title']} (one-shot already exists)")
                continue

        # Check Live Shows - skip if we already have this event/piece under a
        # cosmetically reworded title (e.g. with/without a "Critical Role" segment)
        if series_name == 'Live Show':
            live_show_key = normalize_live_show_title(item['title'])
            if live_show_key in existing_live_shows:
                skipped.append(f"{item['title']} (live show already exists)")
                continue
            if is_manually_reworded_live_show_duplicate(item['title']):
                skipped.append(f"{item['title']} (live show already exists, manually reworded)")
                continue

        # Check generic-fallback rows - skip if already exists under a
        # manually-cleaned-up title/campaign/arc split (see
        # _MANUALLY_REWORDED_GENERIC_ROWS for why raw-title matching is needed)
        if item.get('is_generic_fallback'):
            if is_manually_reworded_generic_duplicate(item['title'], item['episode_number']):
                skipped.append(f"{item['title']} (already exists, manually reworded)")
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
        existing_ids_normalized.add(normalize_text(episode_id))

        # Update tracking sets to prevent duplicates within the same scrape
        if series_name == 'Critical Role Cooldown' and ep_num:
            existing_cooldowns.add((cooldown_prefix, ep_num))
        if series_name == 'Fireside Chat':
            guests = extract_fireside_guests(item['title'])
            if guests:
                existing_fireside_chats.add(guests)
        if series_name == 'Weird Kids' and ep_num:
            existing_weird_kids.add(ep_num)
        if series_name == 'Tale Gate':
            arc_name = extract_arc_name(item['title'])
            existing_tale_gates.add(arc_name)
            existing_normalized_titles.add(('tale gate', normalize_text(item['title'])))
        if series_name == 'Previously On...':
            arc_name = extract_arc_name(item['title'])
            existing_previously_on.add(arc_name)
            existing_normalized_titles.add(('previously on', normalize_text(item['title'])))
        if series_name == 'Campaign Four' and ep_num:
            existing_c4_episodes.add(ep_num)
        if series_name == 'Backstage Pass':
            event_match = re.search(r'backstage pass\s*-\s*(.+)', item['title'], re.IGNORECASE)
            if event_match:
                existing_backstage_pass.add(normalize_text(event_match.group(1)))
        if series_name == 'One-Shot':
            existing_one_shots.add(normalize_text(item['title']))
        if series_name == 'Live Show':
            existing_live_shows.add(normalize_live_show_title(item['title']))

    if skipped:
        print(f"\nSkipped {len(skipped)} existing episodes:")
        for title in skipped[:5]:
            print(f"  - {title}")
        if len(skipped) > 5:
            print(f"  ... and {len(skipped) - 5} more")

    if not new_rows:
        print("\nNo new episodes to add")
        return [], skipped

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

    return new_rows, skipped


_CHANGELOG_HEADER = (
    "# Changelog\n\n"
    "Weekly scraper runs - which critrole.com schedule pages were checked and what "
    "got added, so you can open the same page and compare it against what the "
    "scraper actually did that week.\n\n"
)


def write_changelog_entry(week_urls, new_rows, skipped, changelog_path='CHANGELOG.md'):
    """
    Prepend a dated entry to CHANGELOG.md summarizing a scraper run. Newest
    entry goes right after the fixed header, so recent weeks are always at
    the top without re-reading/re-ordering the whole file.
    """
    lines = [f"## Run: {datetime.now().strftime('%Y-%m-%d')}", ""]

    if week_urls:
        lines.append("Checked:")
        lines.extend(f"- {url}" for url in week_urls)
        lines.append("")

    if new_rows:
        lines.append(f"Added ({len(new_rows)}):")
        for row in sorted(new_rows, key=lambda r: r['airdate'] or ''):
            lines.append(f"- [{row['airdate']}] {row['title']}")
    else:
        lines.append("Added: none")
    lines.append("")
    lines.append(f"Skipped as already tracked: {len(skipped)}")
    lines.append("")

    entry = "\n".join(lines) + "\n"

    try:
        with open(changelog_path, encoding='utf-8') as f:
            existing = f.read()
    except FileNotFoundError:
        existing = ''
    if not existing.startswith(_CHANGELOG_HEADER):
        existing = _CHANGELOG_HEADER + existing

    body = existing[len(_CHANGELOG_HEADER):]
    with open(changelog_path, 'w', encoding='utf-8') as f:
        f.write(_CHANGELOG_HEADER + entry + body)

    print(f"\n✓ Wrote changelog entry to {changelog_path}")


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
    new_rows, skipped = merge_into_main_csv(content)

    if new_rows:
        print(f"\n✓ Successfully added {len(new_rows)} new episode(s) to the tracker!")
    else:
        print("\n✓ No new episodes found - CSV is up to date!")

    # critrole.com URLs actually covered by this run, for the changelog - lets
    # a human open the same page and eyeball-compare it against what got added.
    urls_start = datetime.strptime(start_date, '%Y-%m-%d')
    urls_end = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()
    week_urls = sorted({
        url for _, url, source in generate_schedule_urls(urls_start, urls_end)
        if source == 'critrole'
    })
    write_changelog_entry(week_urls, new_rows, skipped)
