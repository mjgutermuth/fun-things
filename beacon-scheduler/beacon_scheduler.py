#!/usr/bin/env python3
"""
beacon_scheduler.py - Extract Beacon.tv programming schedule and add to Google Calendar
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from typing import List, Dict
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

# critrole.com sits behind Cloudflare, which 403s requests without a browser-like UA
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

def fetch_schedule(url: str) -> tuple:
    """Fetch the HTML from critrole.com

    Returns: (html, actual_url_used)
    """
    urls_to_try = [url]

    # Also try previous year variant (for early January edge cases)
    current_year = str(datetime.now().year)
    prev_year = str(datetime.now().year - 1)

    if current_year in url:
        urls_to_try.append(url.replace(current_year, prev_year))

    last_response = None
    for attempt_url in urls_to_try:
        last_response = requests.get(attempt_url, headers=REQUEST_HEADERS)
        if last_response.status_code == 200:
            return last_response.text, attempt_url
        elif last_response.status_code == 404:
            print(f"  404 error for: {attempt_url}")

    # If all URLs failed, raise the last error
    if last_response is not None:
        last_response.raise_for_status()
    raise ValueError(f"Failed to fetch schedule from any URL: {urls_to_try}")

def get_this_weeks_monday_url() -> tuple:
    """Generate the Beacon.tv schedule URL for this week's Monday (most recent Monday)"""
    today = datetime.now()
    
    # Calculate days since last Monday (0=Monday, 6=Sunday)
    days_since_monday = today.weekday()  # Monday is 0
    
    # Get this week's Monday
    this_monday = today - timedelta(days=days_since_monday)
    
    # Format: "january-5th-2025"
    month = this_monday.strftime("%B").lower()
    day = this_monday.day
    year = this_monday.year
    
    # Add ordinal suffix (st, nd, rd, th)
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    
    url = f"https://critrole.com/programming-schedule-week-of-{month}-{day}{suffix}-{year}/"
    return url, this_monday

def parse_schedule(html: str) -> List[Dict]:
    """Parse the schedule from the page HTML.

    The page is a WordPress/Elementor post: each show is an <h3> title
    followed by a <ul> of <li> lines with the release day/date/time text.
    """
    soup = BeautifulSoup(html, 'html.parser')
    content = soup.find('div', class_='qt-the-content')

    if not content:
        raise ValueError("Could not find schedule content container")

    events = []
    current_series = None
    for element in content.find_all(['h3', 'ul']):
        if element.name == 'h3':
            current_series = element.get_text(strip=True)
        elif element.name == 'ul' and current_series:
            for li in element.find_all('li', recursive=False):
                info_text = li.get_text(separator=' ', strip=True)

                event = parse_event_text(current_series, info_text)
                if event:
                    events.append(event)

    return events

def is_beacon_premiere(text: str) -> bool:
    """True if this schedule line is a first-run release on Beacon.

    Excludes lines whose only platforms are YouTube/Twitch/podcast (already
    covered by the corresponding Beacon release) and rebroadcasts/reruns.
    """
    lowered = text.lower()
    if 'beacon' not in lowered:
        return False
    if any(keyword in lowered for keyword in ('rebroadcast', 'rerun', 're-run', 'repeat broadcast')):
        return False
    return True

def parse_event_text(series: str, text: str) -> Dict | None:
    """
    Parse event details from text like:
    'Episode 34 releases Monday, January 5th at 12am Pacific on Beacon'
    'Campaign 3, Episode 104 releases Tuesday, January 6th at 8am Pacific on Beacon'
    """
    
    # Extract episode info (everything before "releases" or "Tune in")
    episode_match = re.search(r'^(.+?)\s+(?:releases|Tune in)', text, re.IGNORECASE)
    episode = episode_match.group(1).strip() if episode_match else None
    
    # Extract day of week
    day_match = re.search(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)', text)
    day = day_match.group(1) if day_match else None
    
    # Extract date (month + day)
    date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+)(?:st|nd|rd|th)', text)
    month = date_match.group(1) if date_match else None
    day_num = date_match.group(2) if date_match else None
    
    # Extract time
    time_match = re.search(r'at\s+(\d+):?(\d*)([ap]m)\s+Pacific', text, re.IGNORECASE)
    hour = time_match.group(1) if time_match else None
    minute = time_match.group(2) if time_match else "00"
    am_pm = time_match.group(3).lower() if time_match else None
    
    if not minute:
        minute = "00"
    
    # Return None if we couldn't parse required fields
    if not all([month, day_num, hour, am_pm]):
        print(f"  Warning: Could not parse event: {text[:80]}...")
        return None

    # Only keep first-run releases on Beacon; skip YouTube/Twitch-only drops and reruns
    if not is_beacon_premiere(text):
        print(f"  Skipped (not a Beacon premiere): {text[:80]}...")
        return None

    return {
        'series': series,
        'episode': episode,
        'day_of_week': day,
        'month': month,
        'day': day_num,
        'hour': hour,
        'minute': minute,
        'am_pm': am_pm,
        'raw_text': text
    }

def get_credentials():
    """Authenticate and return credentials for Google APIs"""
    creds = None

    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def get_calendar_service(creds):
    """Return Google Calendar service"""
    return build('calendar', 'v3', credentials=creds)

def find_beacon_calendar(service):
    """Find the 'Beacon Schedule' calendar, or None if not found"""
    try:
        calendar_list = service.calendarList().list().execute()
        for calendar in calendar_list.get('items', []):
            if calendar.get('summary') == 'Beacon Schedule':
                return calendar['id']
        return None
    except HttpError as error:
        print(f'Error finding calendar: {error}')
        return None

def convert_to_datetime(event: Dict, year: int = None) -> datetime:
    """Convert event dict to datetime object in Pacific time"""
    months = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    
    month_num = months[event['month']]
    day = int(event['day'])
    hour = int(event['hour'])
    minute = int(event['minute'])
    
    # Convert to 24-hour format
    if event['am_pm'] == 'pm' and hour != 12:
        hour += 12
    elif event['am_pm'] == 'am' and hour == 12:
        hour = 0
    
    # Use provided year or guess based on current date
    if year is None:
        year = datetime.now().year
    
    # Create datetime (Pacific time will be handled by timezone in the event)
    return datetime(year, month_num, day, hour, minute)

def event_exists(service, calendar_id: str, title: str, start_datetime: datetime) -> bool:
    """Check if an event with this title and start time already exists"""
    try:
        # Search for events on this day
        time_min = start_datetime.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        time_max = start_datetime.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
                
        # Check if any event matches our title and start time
        for event in events:
            event_title = event.get('summary', '')
            
            if event_title == title:
                # Check if start time matches (within 1 minute to account for formatting)
                event_start = event.get('start', {}).get('dateTime', '')
                if event_start:
                    # Parse the existing event's start time
                    existing_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                    time_diff = abs((existing_dt.replace(tzinfo=None) - start_datetime).total_seconds())
                    
                    if time_diff < 60:
                        return True
        
        return False
        
    except HttpError as error:
        print(f'Error checking for existing events: {error}')
        return False

def create_calendar_event(service, calendar_id: str, event: Dict, actual_year: int):
    """Create a Google Calendar event"""
    
    # Create event title
    if event['episode']:
        title = f"{event['series']}: {event['episode']}"
    else:
        title = event['series']
    
    # Convert to datetime - use the actual year from the URL we successfully fetched
    event_datetime = convert_to_datetime(event, year=actual_year)
    
    # Check if event already exists
    if event_exists(service, calendar_id, title, event_datetime):
        print(f"⊘ Skipped (already exists): {title}")
        return None
    
    # Format for Google Calendar (ISO 8601 with Pacific timezone)
    start_time = event_datetime.isoformat()
    # Assume 3-hour duration for shows
    end_time = (event_datetime + timedelta(hours=3)).isoformat()
    
    calendar_event = {
        'summary': title,
        'description': f"Watch on Beacon.tv\n\n{event['raw_text']}",
        'start': {
            'dateTime': start_time,
            'timeZone': 'America/Los_Angeles',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'America/Los_Angeles',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 30},
            ],
        },
    }
    
    try:
        event = service.events().insert(calendarId=calendar_id, body=calendar_event).execute()
        print(f"✓ Created event: {title}")
        print(f"  {event_datetime.strftime('%A, %B %d at %I:%M%p')} Pacific")
        return event
    except HttpError as error:
        print(f'✗ Error creating event: {error}')
        return None

def main():
    """Main function"""
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"URL: {url}\n")
    else:
        # Generate URL for this week's Monday
        url, week_start = get_this_weeks_monday_url()
        print(f"Week starting: {week_start.strftime('%B %d, %Y')}")
        print(f"URL: {url}\n")
    
    print("Fetching schedule from Beacon.tv...")
    html, actual_url = fetch_schedule(url)
    
    # Extract the actual year from the URL we successfully fetched
    actual_year = int(actual_url.rstrip('/').split('-')[-1])
    print(f"Using year: {actual_year}\n")

    print("Parsing schedule...")
    events = parse_schedule(html)
    print(f"Found {len(events)} events\n")
    
    # Authenticate with Google Calendar
    print("Authenticating with Google Calendar...")
    creds = get_credentials()
    calendar_service = get_calendar_service(creds)

    # Find the Beacon Schedule calendar
    print("Finding 'Beacon Schedule' calendar...")
    calendar_id = find_beacon_calendar(calendar_service)

    if not calendar_id:
        print("\n❌ ERROR: Could not find 'Beacon Schedule' calendar!")
        print("Please create it manually in Google Calendar first:")
        print("  1. Go to https://calendar.google.com")
        print("  2. Click '+' next to 'Other calendars'")
        print("  3. Create new calendar named 'Beacon Schedule'")
        print("  4. Set timezone to Pacific Time")
        return

    print(f"Found calendar! ID: {calendar_id}\n")

    # Create calendar events
    print("Creating calendar events...\n")
    created_count = 0
    skipped_count = 0

    for event in events:
        result = create_calendar_event(calendar_service, calendar_id, event, actual_year)
        if result:
            created_count += 1
        else:
            skipped_count += 1
        print()

    print(f"✓ Done! Created {created_count} events, skipped {skipped_count} duplicates")

if __name__ == "__main__":
    main()