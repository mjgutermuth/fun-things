#!/usr/bin/env python3
"""
Scrape Critical Role wiki for new main campaign episodes
and merge them into the main CSV.

Uses the Fandom MediaWiki API (action=parse) to render arc pages server-side,
bypassing Cloudflare entirely. No Playwright required.
"""

import csv
import json
import re
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime
from bs4 import BeautifulSoup


API_BASE = "https://criticalrole.fandom.com/api.php"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; cr-tracker-bot/1.0; wiki episode scraper)'
}

# Arc pages to check for each campaign. The scraper only fetches the arcs listed
# here, so add a new entry when a new arc starts. Order doesn't matter.
ARC_PAGES = {
    'Campaign One: Vox Machina': [
        'Campaign One Arc 1: Kraghammer and Vasselheim',
        'Campaign One Arc 2: The Briarwoods',
        'Campaign One Arc 3: The Chroma Conclave',
        'Campaign One Arc 4: Taryon Darrington',
        'Campaign One Arc 5: Vecna',
    ],
    'Campaign Two: The Mighty Nein': [
        'Campaign Two Arc 1: Come Together',
        'Campaign Two Arc 2: The Bad Guys',
        'Campaign Two Arc 3: The Bright Queen\'s Favor',
        'Campaign Two Arc 4: Swords and Angels',
        'Campaign Two Arc 5: Family Ties',
        'Campaign Two Arc 6: Weird Magic',
    ],
    'Campaign Three: Bells Hells': [
        'Campaign Three Arc 1: Jrusar',
        'Campaign Three Arc 2: Ruidus Rising',
        'Campaign Three Arc 3: Separations and Explorations',
        'Campaign Three Arc 4: Ruidus to Aeor',
        'Campaign Three Arc 5: Downfall',
        'Campaign Three Arc 6: The End of an Age',
    ],
    'Campaign Four': [
        'Campaign Four Arc 1',
        'Campaign Four Arc 2',
        'Campaign Four Arc 3',
        'Campaign Four Arc 4',
        'Campaign Four Arc 5',
    ],
}


def fetch_url(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8')


def fetch_arc_html(arc_page_title):
    """Fetch the server-rendered HTML of an arc page via the MediaWiki parse API."""
    params = urllib.parse.urlencode({
        'action': 'parse',
        'page': arc_page_title,
        'prop': 'text',
        'format': 'json',
    })
    url = f"{API_BASE}?{params}"
    raw = fetch_url(url)
    data = json.loads(raw)
    if 'error' in data:
        raise RuntimeError(f"API error for '{arc_page_title}': {data['error'].get('info', data['error'])}")
    return data['parse']['text']['*']


def clean_text(text):
    if not text:
        return ''
    text = re.sub(r'\[edit\]', '', text)
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\[\]', '', text)
    return text.strip()


def parse_runtime(runtime_str):
    if not runtime_str:
        return ''
    runtime_str = clean_text(runtime_str)
    match = re.search(r'(\d+):(\d+):(\d+)', runtime_str)
    if match:
        return f"{int(match.group(1))}:{match.group(2)}:{match.group(3)}"
    match = re.search(r'(\d+):(\d+)', runtime_str)
    if match:
        return f"{match.group(1)}:{match.group(2)}:00"
    return runtime_str


def parse_arc_episodes(html, campaign_name, arc_page_title):
    """Parse episode rows from a rendered arc page HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    episodes = []

    # Derive display arc name from the h2/h3 headers in the rendered page, or
    # fall back to the page title itself.
    arc_name = arc_page_title
    h2 = soup.find('h2')
    if h2:
        arc_name = clean_text(h2.get_text())

    tables = soup.find_all('table', class_='wikitable')
    print(f"  [DIAG] '{arc_page_title}': {len(tables)} wikitable(s) found")

    for table in tables:
        header_row = table.find('tr')
        if not header_row:
            continue
        headers = [clean_text(th.get_text()).lower() for th in header_row.find_all('th')]
        header_map = {h: i for i, h in enumerate(headers)}

        if 'title' not in header_map and 'episode title' not in header_map and 'name' not in header_map:
            print(f"  [DIAG] Skipping table — no title column (headers: {headers})")
            continue

        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            if len(cells) < 3:
                continue

            episode = {
                'campaign': campaign_name,
                'arc': arc_name,
                'episode_number': '',
                'title': '',
                'airdate': '',
                'vod_url': '',
                'wiki_url': '',
                'runtime': '',
            }

            for num_header in ['no.', 'no', '#', 'episode']:
                if num_header in header_map and header_map[num_header] < len(cells):
                    ep_num = clean_text(cells[header_map[num_header]].get_text())
                    match = re.search(r'(\d+)', ep_num)
                    if match:
                        episode['episode_number'] = match.group(1)
                    break

            for title_header in ['title', 'episode title', 'name']:
                if title_header in header_map and header_map[title_header] < len(cells):
                    title_cell = cells[header_map[title_header]]
                    title_link = title_cell.find('a')
                    if title_link:
                        episode['title'] = clean_text(title_link.get_text()).strip('"')
                        href = title_link.get('href', '')
                        if href.startswith('/wiki/'):
                            episode['wiki_url'] = 'https://criticalrole.fandom.com' + href
                    else:
                        episode['title'] = clean_text(title_cell.get_text()).strip('"')
                    break

            for date_header in ['original airdate', 'airdate', 'air date', 'date']:
                if date_header in header_map and header_map[date_header] < len(cells):
                    raw_date = clean_text(cells[header_map[date_header]].get_text())
                    # Keep valid ISO dates; skip "Forthcoming" etc.
                    if re.match(r'^\d{4}-\d{2}-\d{2}$', raw_date):
                        episode['airdate'] = raw_date
                    break

            for runtime_header in ['runtime', 'length', 'duration']:
                if runtime_header in header_map and header_map[runtime_header] < len(cells):
                    episode['runtime'] = parse_runtime(cells[header_map[runtime_header]].get_text())
                    break

            for link_header in ['link', 'vod', 'video']:
                if link_header in header_map and header_map[link_header] < len(cells):
                    link_cell = cells[header_map[link_header]]
                    vod_link = link_cell.find('a', href=re.compile(r'youtube|youtu\.be'))
                    if vod_link:
                        episode['vod_url'] = vod_link['href']
                    break

            if episode['title'] and episode['episode_number']:
                episodes.append(episode)

    return episodes


def fetch_all_episodes():
    """Fetch episodes from all known arc pages."""
    all_episodes = []

    for campaign_name, arc_list in ARC_PAGES.items():
        print(f"\nFetching {campaign_name} ({len(arc_list)} arcs)...")
        for arc_page in arc_list:
            try:
                html = fetch_arc_html(arc_page)
                eps = parse_arc_episodes(html, campaign_name, arc_page)
                print(f"  {arc_page}: {len(eps)} episodes")
                all_episodes.extend(eps)
                time.sleep(0.5)  # be polite
            except Exception as e:
                print(f"  [ERROR] Failed to fetch '{arc_page}': {e}")

    return all_episodes


def merge_into_main_csv(new_episodes, main_csv='cr_episodes_series_airdates.csv'):
    """Merge new episodes into the main CSV, updating placeholders."""
    if not new_episodes:
        print("\nNo new episodes to merge")
        return 0

    try:
        with open(main_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing_rows = list(reader)
            fieldnames = reader.fieldnames
    except FileNotFoundError:
        print(f"Error: {main_csv} not found")
        return 0

    # Index existing main campaign episodes by (campaign, episode_number)
    existing_episodes = {}
    for i, row in enumerate(existing_rows):
        if row.get('show_type') == 'Main Campaign':
            key = (row.get('campaign', ''), row.get('episode_number', ''))
            existing_episodes[key] = i

    def is_placeholder(title):
        return bool(re.match(r'^Campaign \d+ Episode \d+$', title))

    wiki_c4_numbers = {ep['episode_number'] for ep in new_episodes
                       if ep.get('campaign') == 'Campaign Four'}

    added = []
    updated = []

    for ep in new_episodes:
        key = (ep['campaign'], ep['episode_number'])

        if key not in existing_episodes:
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
            idx = existing_episodes[key]
            row = existing_rows[idx]
            existing_title = row.get('title', '')
            new_title = ep['title']

            if is_placeholder(existing_title) and not is_placeholder(new_title):
                row['title'] = new_title
                row['episode_id'] = f"Main Campaign|{ep['campaign']}|{ep['episode_number']}|{new_title}"
                if ep.get('wiki_url') and not row.get('wiki_url'):
                    row['wiki_url'] = ep['wiki_url']
                if ep.get('arc') and not row.get('arc'):
                    row['arc'] = ep['arc']
                if ep.get('runtime') and not row.get('runtime'):
                    row['runtime'] = ep['runtime']
                if 'wiki pending' in row.get('notes', '').lower():
                    row['notes'] = ''
                updated.append(ep)
                print(f"  ~ {ep['campaign']} E{ep['episode_number']}: {existing_title!r} -> {new_title!r}")

    # Report placeholders that still weren't resolved
    unresolved = [
        row for row in existing_rows
        if (row.get('show_type') == 'Main Campaign'
            and row.get('campaign') == 'Campaign Four'
            and is_placeholder(row.get('title', ''))
            and row.get('episode_number') not in wiki_c4_numbers)
    ]
    if unresolved:
        print(f"\n[DIAG] {len(unresolved)} Campaign Four placeholder(s) not found on wiki:")
        for row in unresolved:
            print(f"  E{row['episode_number']}: '{row['title']}' (airdate: {row.get('airdate', '?')})")
        if wiki_c4_numbers:
            print(f"[DIAG] Highest C4 episode returned by wiki: E{max(int(n) for n in wiki_c4_numbers if n.isdigit())}")

    if not added and not updated:
        print("\nNo new main campaign episodes to add or update")
        return 0

    existing_rows.sort(key=lambda x: x.get('airdate', '') or '9999-99-99')

    with open(main_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_rows)

    if updated:
        print(f"\n✓ Updated {len(updated)} episode(s) with real titles")
    if added:
        print(f"✓ Added {len(added)} new main campaign episode(s)")
    return len(added) + len(updated)


def main():
    print("=" * 80)
    print("CRITICAL ROLE WIKI EPISODE SCRAPER (API mode)")
    print("=" * 80)
    print("Fetching episodes via Fandom MediaWiki API (no Playwright required)\n")

    try:
        episodes = fetch_all_episodes()
    except Exception as e:
        print(f"\n[ERROR] Unexpected failure during fetch: {e}")
        return 0

    print(f"\nTotal episodes fetched: {len(episodes)}")

    by_campaign = {}
    for ep in episodes:
        by_campaign.setdefault(ep['campaign'], []).append(ep)

    print("\nLatest episode per campaign:")
    for campaign, eps in sorted(by_campaign.items()):
        try:
            latest = max(eps, key=lambda x: int(x['episode_number']))
            print(f"  {campaign}: E{latest['episode_number']} — {latest['title']}")
        except (ValueError, TypeError):
            pass

    print("\n" + "=" * 80)
    print("MERGING INTO MAIN CSV")
    print("=" * 80)

    new_count = merge_into_main_csv(episodes)

    if new_count > 0:
        print(f"\n✓ Successfully updated the tracker with {new_count} change(s)!")
    else:
        print("\n✓ No changes needed — CSV is up to date!")

    return new_count


if __name__ == '__main__':
    main()
