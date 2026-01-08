#!/usr/bin/env python3
"""
Critical Role Complete Episode Scraper
Fetches all episodes from the CR wiki and outputs to CSV
"""

import re
import csv
import sys
from datetime import datetime
from bs4 import BeautifulSoup

def clean_text(text):
    """Remove wiki formatting artifacts like [edit], [1], etc."""
    if not text:
        return ''
    # Remove [edit] links
    text = re.sub(r'\[edit\]', '', text)
    # Remove reference numbers like [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)
    # Remove other brackets artifacts
    text = re.sub(r'\[\]', '', text)
    return text.strip()


def parse_episode_from_row(row, headers, current_context):
    """
    Parse a single episode row based on dynamic headers
    
    Args:
        row: BeautifulSoup TR element
        headers: List of header names from the table
        current_context: Dict with 'campaign', 'arc', 'show_type'
    
    Returns:
        Dict with episode data
    """
    cells = row.find_all('td')
    if len(cells) < 2:
        return None
    
    episode = {
        'show_type': current_context.get('show_type', ''),
        'campaign': current_context.get('campaign', ''),
        'arc': current_context.get('arc', ''),
        'episode_number': '',
        'title': '',
        'airdate': '',
        'vod_url': '',
        'wiki_url': '',
        'runtime': '',
        'watched': '',  # Leave empty - will be a real checkbox in Sheets
        'notes': ''
    }
    
    # Map headers to cell indices
    header_map = {header.lower(): idx for idx, header in enumerate(headers)}
    
    # Extract data based on which columns exist
    try:
        # Episode Number - try multiple variations
        for num_header in ['no.overall', 'no.in chapter', 'no.', 'no', 'episode', '#', 'ep.', 'ep']:
            if num_header in header_map:
                idx = header_map[num_header]
                if idx < len(cells):
                    ep_num = clean_text(cells[idx].get_text(strip=True))
                    episode['episode_number'] = ep_num
                break
        
        # Title (required)
        for title_header in ['title', 'episode title', 'name']:
            if title_header in header_map:
                idx = header_map[title_header]
                if idx < len(cells):
                    title_cell = cells[idx]
                    title_link = title_cell.find('a')
                    if title_link:
                        title = clean_text(title_link.get_text(strip=True))
                        # Remove episode code from title (e.g., "(1x01)")
                        title = re.sub(r'\s*\(\d+x\d+\)\s*$', '', title)
                        episode['title'] = title
                        episode['wiki_url'] = 'https://criticalrole.fandom.com' + title_link['href']
                    else:
                        episode['title'] = clean_text(title_cell.get_text(strip=True))
                break
        
        # Airdate
        for date_header in ['original airdate', 'airdate', 'air date', 'date', 'premiere date']:
            if date_header in header_map:
                idx = header_map[date_header]
                if idx < len(cells):
                    airdate = clean_text(cells[idx].get_text(strip=True))
                    episode['airdate'] = airdate
                break
        
        # VOD Link
        for link_header in ['link', 'vod', 'video', 'youtube']:
            if link_header in header_map:
                idx = header_map[link_header]
                if idx < len(cells):
                    link_cell = cells[idx]
                    vod_link = link_cell.find('a')
                    if vod_link and 'href' in vod_link.attrs:
                        episode['vod_url'] = vod_link['href']
                    # Special case: if no link but cell has text like "Prime Video"
                    elif link_cell.get_text(strip=True) and not vod_link:
                        platform = clean_text(link_cell.get_text(strip=True))
                        if platform.lower() not in ['n/a', 'tbd', 'upcoming', '']:
                            episode['notes'] = f"Available on {platform}"
                break
        
        # Runtime
        for runtime_header in ['runtime', 'length', 'duration']:
            if runtime_header in header_map:
                idx = header_map[runtime_header]
                if idx < len(cells):
                    runtime = clean_text(cells[idx].get_text(strip=True))
                    episode['runtime'] = runtime
                break
        
        # Add note for animated series with no VOD
        if episode['show_type'] == 'Animated Series' and not episode['vod_url']:
            if not episode['notes']:
                episode['notes'] = 'Available on Prime Video'
            elif 'Prime Video' not in episode['notes']:
                episode['notes'] += ' | Available on Prime Video'
        
        return episode
        
    except Exception as e:
        print(f"Warning: Error parsing row: {e}", file=sys.stderr)
        return None


def parse_all_episodes(html_content):
    """
    Parse all episodes from CR wiki HTML with flexible table handling
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    episodes = []
    
    # Track current context
    current_show_type = None
    current_campaign = None
    current_arc = None
    
    # Get all content elements in order
    content_elements = soup.find_all(['h2', 'h3', 'h4', 'table'])
    
    for element in content_elements:
        if element.name in ['h2', 'h3', 'h4']:
            # Extract heading text
            heading_text = element.get_text(strip=True)
            heading_text = clean_text(heading_text)
            
            # Skip non-content headings
            if not heading_text or heading_text in ['Contents', 'References', 'Art']:
                continue
            
            # Parse context from heading
            if element.name == 'h2':
                # Major sections
                current_campaign = heading_text
                current_arc = None
                
                # Determine show type
                if 'Campaign' in heading_text and any(x in heading_text for x in ['One', 'Two', 'Three', 'Four']):
                    current_show_type = 'Main Campaign'
                elif 'Legend of Vox Machina' in heading_text or 'Mighty Nein (animated)' in heading_text:
                    current_show_type = 'Animated Series'
                elif 'Special' in heading_text:
                    current_show_type = 'Special'
                elif '4-Sided Dive' in heading_text:
                    current_show_type = 'Talk Show'
                elif 'Talks Machina' in heading_text:
                    current_show_type = 'Talk Show'
                elif any(x in heading_text for x in ['Exandria', 'Candela', 'UnDeadwood', 'Miniseries']):
                    current_show_type = 'Miniseries'
                else:
                    current_show_type = 'Other'
                    
            elif element.name in ['h3', 'h4']:
                # Arcs or sub-sections
                current_arc = heading_text
                
        elif element.name == 'table' and 'wikitable' in element.get('class', []):
            # Episode table
            if not current_campaign:
                continue
            
            # Get headers
            header_row = element.find('tr')
            if not header_row:
                continue
                
            headers = [clean_text(th.get_text(strip=True)).lower() for th in header_row.find_all('th')]
            if not headers or 'title' not in ' '.join(headers):
                continue
            
            # Context for this table
            context = {
                'show_type': current_show_type,
                'campaign': current_campaign,
                'arc': current_arc
            }
            
            # Parse all rows
            data_rows = element.find_all('tr')[1:]
            
            for row in data_rows:
                episode = parse_episode_from_row(row, headers, context)
                if episode and episode['title']:
                    episodes.append(episode)
    
    return episodes


def save_to_csv(episodes, filename='cr_episodes.csv'):
    """Save episodes to CSV file"""
    
    fieldnames = [
        'show_type', 'campaign', 'arc', 'episode_number', 'title', 
        'airdate', 'vod_url', 'wiki_url', 'runtime', 'watched', 'notes'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(episodes)
    
    print(f"\n✓ Saved {len(episodes)} episodes to {filename}")


def print_summary(episodes):
    """Print a summary of what was scraped"""
    
    print("\n" + "=" * 80)
    print("SCRAPING SUMMARY")
    print("=" * 80)
    
    # Count by show type
    by_type = {}
    for ep in episodes:
        show_type = ep['show_type']
        by_type[show_type] = by_type.get(show_type, 0) + 1
    
    print(f"\nTotal episodes: {len(episodes)}")
    print("\nBreakdown by type:")
    for show_type, count in sorted(by_type.items()):
        print(f"  {show_type:20} : {count:4} episodes")
    
    # Count by campaign
    by_campaign = {}
    for ep in episodes:
        if ep['show_type'] == 'Main Campaign':
            campaign = ep['campaign']
            by_campaign[campaign] = by_campaign.get(campaign, 0) + 1
    
    if by_campaign:
        print("\nMain campaigns:")
        for campaign, count in sorted(by_campaign.items()):
            print(f"  {campaign[:40]:40} : {count:4} episodes")
    
    # Date range
    dates = [ep['airdate'] for ep in episodes if ep['airdate']]
    if dates:
        dates_sorted = sorted(dates)
        print(f"\nDate range: {dates_sorted[0]} to {dates_sorted[-1]}")
    
    # Episodes missing episode numbers
    missing_numbers = [ep for ep in episodes if not ep['episode_number'] and ep['show_type'] != 'Special']
    if missing_numbers:
        print(f"\nEpisodes missing episode numbers: {len(missing_numbers)}")
        print("  Examples:")
        for ep in missing_numbers[:3]:
            print(f"    - {ep['campaign'][:30]:30} | {ep['title'][:40]}")


def main():
    """Main scraper function"""
    
    print("Critical Role Complete Episode Scraper")
    print("=" * 80)


if __name__ == '__main__':
    # If HTML file exists, parse it
    import os
    
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
        if os.path.exists(html_file):
            print(f"\nParsing {html_file}...")
            
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            episodes = parse_all_episodes(html_content)
            print_summary(episodes)
            save_to_csv(episodes)
            
            print("\n" + "=" * 80)
            print("NEXT STEPS:")
            print("=" * 80)
            print("""
1. Import cr_episodes.csv to Google Sheets
2. In Google Sheets, select the 'watched' column
3. Format → Number → Checkbox (to make it a real checkbox)
4. Start tracking your watched episodes!
            """)
        else:
            print(f"Error: File {html_file} not found")
            sys.exit(1)
    else:
        main()
