#!/usr/bin/env python3
"""
Data validation script for CR-Tracker CSV
Checks for missing fields, duplicates, and data consistency issues
"""

import csv
import re
import sys
from collections import Counter
from datetime import datetime


def load_csv(filepath='cr_episodes_series_airdates.csv'):
    """Load the CSV file and return rows"""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames


def validate_required_fields(rows):
    """Check for missing required fields"""
    issues = []
    required_fields = ['episode_id', 'show_type', 'title', 'airdate']

    for i, row in enumerate(rows, 1):
        for field in required_fields:
            value = row.get(field, '').strip()
            # Allow 'Forthcoming' as valid for airdate
            if not value or (field == 'airdate' and value == ''):
                # Skip airdate check for future episodes
                if field == 'airdate' and row.get('notes', '').lower() in ['forthcoming', 'available soon']:
                    continue
                issues.append({
                    'row': i,
                    'type': 'missing_field',
                    'field': field,
                    'title': row.get('title', 'Unknown'),
                    'message': f"Missing {field}"
                })

    return issues


def validate_duplicates(rows):
    """Check for duplicate episode_ids"""
    issues = []
    id_counts = Counter(row['episode_id'] for row in rows if row.get('episode_id'))

    for episode_id, count in id_counts.items():
        if count > 1:
            issues.append({
                'type': 'duplicate',
                'episode_id': episode_id,
                'count': count,
                'message': f"Duplicate episode_id appears {count} times"
            })

    return issues


def validate_dates(rows):
    """Check for invalid date formats"""
    issues = []
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')

    for i, row in enumerate(rows, 1):
        airdate = row.get('airdate', '').strip()
        if airdate and airdate != 'Forthcoming':
            if not date_pattern.match(airdate):
                issues.append({
                    'row': i,
                    'type': 'invalid_date',
                    'field': 'airdate',
                    'value': airdate,
                    'title': row.get('title', 'Unknown'),
                    'message': f"Invalid date format: {airdate} (expected YYYY-MM-DD)"
                })
            else:
                # Check if date is reasonable (not in far future or past)
                try:
                    date = datetime.strptime(airdate, '%Y-%m-%d')
                    if date.year < 2015 or date.year > 2030:
                        issues.append({
                            'row': i,
                            'type': 'suspicious_date',
                            'field': 'airdate',
                            'value': airdate,
                            'title': row.get('title', 'Unknown'),
                            'message': f"Suspicious date (year {date.year})"
                        })
                except ValueError:
                    pass

    return issues


def validate_urls(rows):
    """Check for malformed URLs"""
    issues = []
    url_pattern = re.compile(r'^https?://[^\s]+$')

    for i, row in enumerate(rows, 1):
        for field in ['vod_url', 'wiki_url']:
            url = row.get(field, '').strip()
            if url and url != 'https://www.beacon.tv':
                if not url_pattern.match(url):
                    issues.append({
                        'row': i,
                        'type': 'invalid_url',
                        'field': field,
                        'value': url,
                        'title': row.get('title', 'Unknown'),
                        'message': f"Invalid URL format in {field}"
                    })

    return issues


def validate_episode_numbers(rows):
    """Check for missing or invalid episode numbers for main content"""
    issues = []

    for i, row in enumerate(rows, 1):
        show_type = row.get('show_type', '')
        ep_num = row.get('episode_number', '').strip()

        # Main Campaign and Talk Shows should have episode numbers
        if show_type in ['Main Campaign', 'Talk Show', 'Miniseries']:
            if not ep_num:
                issues.append({
                    'row': i,
                    'type': 'missing_episode_number',
                    'show_type': show_type,
                    'title': row.get('title', 'Unknown'),
                    'message': f"Missing episode number for {show_type}"
                })

    return issues


def validate_runtime_format(rows):
    """Check for invalid runtime formats"""
    issues = []
    runtime_pattern = re.compile(r'^(\d+:)?\d{1,2}:\d{2}$')  # H:MM:SS or MM:SS

    for i, row in enumerate(rows, 1):
        runtime = row.get('runtime', '').strip()
        if runtime and runtime != '0:00:00':
            if not runtime_pattern.match(runtime):
                issues.append({
                    'row': i,
                    'type': 'invalid_runtime',
                    'value': runtime,
                    'title': row.get('title', 'Unknown'),
                    'message': f"Invalid runtime format: {runtime}"
                })

    return issues


def find_missing_vod_urls(rows):
    """Find episodes that should have VOD URLs but don't"""
    issues = []

    for i, row in enumerate(rows, 1):
        show_type = row.get('show_type', '')
        vod_url = row.get('vod_url', '').strip()
        airdate = row.get('airdate', '')
        notes = row.get('notes', '').lower()

        # Skip future episodes or beacon exclusives
        if 'forthcoming' in notes or 'available soon' in notes:
            continue
        if 'beacon' in notes.lower() or vod_url == 'https://www.beacon.tv':
            continue

        # Main Campaign episodes should have YouTube URLs
        if show_type == 'Main Campaign' and not vod_url:
            # Only flag if airdate is in the past
            if airdate and airdate != 'Forthcoming':
                try:
                    ep_date = datetime.strptime(airdate, '%Y-%m-%d')
                    if ep_date < datetime.now():
                        issues.append({
                            'row': i,
                            'type': 'missing_vod_url',
                            'show_type': show_type,
                            'title': row.get('title', 'Unknown'),
                            'airdate': airdate,
                            'message': f"Main Campaign episode missing VOD URL"
                        })
                except ValueError:
                    pass

    return issues


def find_missing_runtimes(rows):
    """Find episodes that should have runtimes but don't"""
    issues = []

    for i, row in enumerate(rows, 1):
        show_type = row.get('show_type', '')
        runtime = row.get('runtime', '').strip()
        airdate = row.get('airdate', '')
        notes = row.get('notes', '').lower()

        # Skip future episodes
        if 'forthcoming' in notes or 'available soon' in notes:
            continue

        # Main Campaign episodes should have runtimes
        if show_type == 'Main Campaign' and (not runtime or runtime == '0:00:00'):
            if airdate and airdate != 'Forthcoming':
                try:
                    ep_date = datetime.strptime(airdate, '%Y-%m-%d')
                    if ep_date < datetime.now():
                        issues.append({
                            'row': i,
                            'type': 'missing_runtime',
                            'show_type': show_type,
                            'title': row.get('title', 'Unknown'),
                            'airdate': airdate,
                            'message': f"Main Campaign episode missing runtime"
                        })
                except ValueError:
                    pass

    return issues


def generate_report(all_issues):
    """Generate a summary report of all issues"""
    print("=" * 80)
    print("CR-TRACKER DATA VALIDATION REPORT")
    print("=" * 80)

    if not all_issues:
        print("\n✓ No issues found! Data is clean.\n")
        return

    # Group by type
    by_type = {}
    for issue in all_issues:
        issue_type = issue['type']
        if issue_type not in by_type:
            by_type[issue_type] = []
        by_type[issue_type].append(issue)

    print(f"\nFound {len(all_issues)} issues:\n")

    for issue_type, issues in sorted(by_type.items()):
        print(f"\n{issue_type.upper().replace('_', ' ')} ({len(issues)}):")
        print("-" * 40)
        for issue in issues[:10]:  # Show first 10
            if 'title' in issue:
                print(f"  - {issue['title']}: {issue['message']}")
            else:
                print(f"  - {issue['message']}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")

    print("\n" + "=" * 80)
    print(f"SUMMARY: {len(all_issues)} total issues across {len(by_type)} categories")
    print("=" * 80)


def main():
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'cr_episodes_series_airdates.csv'

    print(f"Loading {csv_file}...")
    rows, fieldnames = load_csv(csv_file)
    print(f"Loaded {len(rows)} episodes\n")

    all_issues = []

    print("Running validations...")

    # Core validations
    all_issues.extend(validate_required_fields(rows))
    all_issues.extend(validate_duplicates(rows))
    all_issues.extend(validate_dates(rows))
    all_issues.extend(validate_urls(rows))
    all_issues.extend(validate_episode_numbers(rows))
    all_issues.extend(validate_runtime_format(rows))

    # Data quality checks
    all_issues.extend(find_missing_vod_urls(rows))
    all_issues.extend(find_missing_runtimes(rows))

    generate_report(all_issues)

    # Return exit code based on critical issues
    critical_types = ['duplicate', 'invalid_date', 'missing_field']
    critical_issues = [i for i in all_issues if i['type'] in critical_types]

    return 1 if critical_issues else 0


if __name__ == '__main__':
    sys.exit(main())
