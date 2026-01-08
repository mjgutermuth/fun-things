#!/usr/bin/env python3
"""
Scrape CritRole.com weekly programming schedules to extract Beacon-exclusive content
"""

import sys
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
import time
import csv

def generate_schedule_urls(start_date, end_date):
    """
    Generate all weekly programming schedule URLs between two dates.
    Schedules are posted on Mondays.
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
        
        url = f"https://critrole.com/programming-schedule-week-of-{month}-{day}{suffix}-{year}/"
        urls.append((current, url))
        
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
    # Matches: "Fireside Chat" anywhere near "Beacon"
    fireside_pattern = r'Fireside\s+Chat(?:\s+LIVE)?(?:\s+with\s+([\w\s]+?))?(?=\s)'
    fireside_matches = list(re.finditer(fireside_pattern, text, re.IGNORECASE))
    
    for match in fireside_matches:
        guest = match.group(1).strip() if match.group(1) else 'Unknown'
        
        content.append({
            'week_date': week_date.strftime('%Y-%m-%d'),
            'show_type': 'Beacon Exclusive',
            'series': 'Fireside Chat',
            'campaign': '',
            'episode_number': '',
            'title': f'Fireside Chat with {guest}',
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
    
    return content

def scrape_beacon_exclusives(start_date_str, end_date_str=None):
    """
    Scrape all Beacon-exclusive content from programming schedules
    """
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else datetime.now()
    
    print(f"Generating schedule URLs from {start_date.date()} to {end_date.date()}...")
    urls = generate_schedule_urls(start_date, end_date)
    print(f"Found {len(urls)} weekly schedules to check\n")
    
    all_content = []
    
    # Use proper headers to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    for week_date, url in urls:
        # Try both URL formats - with and without ordinal suffix
        url_without_suffix = url.replace('st-', '-').replace('nd-', '-').replace('rd-', '-').replace('th-', '-')
        
        success = False
        
        for attempt_url in [url, url_without_suffix]:
            if success:
                break
                
            print(f"Fetching {week_date.strftime('%Y-%m-%d')}: {attempt_url}")
            
            try:
                response = requests.get(attempt_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    content = extract_beacon_content(response.text, week_date)
                    if content:
                        print(f"  ✓ Found {len(content)} Beacon-exclusive items")
                        all_content.extend(content)
                    else:
                        print(f"  - No Beacon content found")
                    success = True
                elif response.status_code == 404:
                    print(f"  ✗ HTTP 404 (trying alternate URL format...)")
                else:
                    print(f"  ✗ HTTP {response.status_code}")
            
            except Exception as e:
                print(f"  ✗ Error: {e}")
        
        # Be nice to the server - wait longer between requests
        time.sleep(2)
    
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

if __name__ == '__main__':
    # Beacon launched May 9, 2024
    start_date = '2024-05-06'  # Monday of that week
    
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
    save_to_csv(content)
