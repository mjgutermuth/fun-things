#!/usr/bin/env python3
"""
Fold episode_overrides (corrections made via the tracker's browser Edit Mode)
back into cr_episodes_series_airdates.csv, then delete the applied rows from
Supabase - so the override table stays a short-lived staging area instead of
a permanent shadow layer the CSV can silently drift out of sync with.

Requires the Supabase SERVICE ROLE key (not the public anon key already in
index.html) via the SUPABASE_SERVICE_ROLE_KEY environment variable - find it
in the Supabase dashboard under Project Settings > API. This key bypasses
Row Level Security, so: never commit it, never put it in index.html, never
share it - treat it like a database admin password.

Usage:
    SUPABASE_SERVICE_ROLE_KEY=... python3 apply_overrides.py
"""

import csv
import json
import os
import sys
import urllib.request
from urllib.parse import quote

SUPABASE_URL = 'https://wkqjgakouqjvfoyseaui.supabase.co'
CSV_PATH = 'cr_episodes_series_airdates.csv'
OVERRIDE_FIELDS = ('show_type', 'campaign', 'episode_number', 'title')


def _request(method, path, service_key, body=None):
    url = f'{SUPABASE_URL}/rest/v1/{path}'
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('apikey', service_key)
    req.add_header('Authorization', f'Bearer {service_key}')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else None


def fetch_overrides(service_key):
    return _request('GET', 'episode_overrides?select=*', service_key) or []


def delete_override(episode_id, service_key):
    # episode_id embeds "|" and other punctuation, so it needs URL-encoding
    # as a PostgREST filter value.
    path = f'episode_overrides?episode_id=eq.{quote(episode_id, safe="")}'
    _request('DELETE', path, service_key)


def main():
    service_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    if not service_key:
        print('Error: set SUPABASE_SERVICE_ROLE_KEY (Supabase dashboard > Project Settings > API).')
        print('This is the SERVICE ROLE key, not the anon key already in index.html - never commit it.')
        sys.exit(1)

    print('Fetching overrides from Supabase...')
    overrides = fetch_overrides(service_key)
    if not overrides:
        print('No overrides to apply.')
        return

    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    rows_by_id = {row['episode_id']: row for row in rows if row['episode_id']}

    applied = []
    orphaned = []
    for override in overrides:
        episode_id = override['episode_id']
        row = rows_by_id.get(episode_id)
        if not row:
            orphaned.append(episode_id)
            continue
        for field in OVERRIDE_FIELDS:
            value = override.get(field)
            if value:
                row[field] = value
        applied.append(episode_id)

    if applied:
        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f'Applied {len(applied)} override(s) to {CSV_PATH}:')
        for episode_id in applied:
            print(f'  - {episode_id}')

        print('Clearing applied overrides from Supabase...')
        for episode_id in applied:
            delete_override(episode_id, service_key)

    if orphaned:
        print(f'\n{len(orphaned)} override(s) left in place - no matching episode_id in the CSV (investigate manually):')
        for episode_id in orphaned:
            print(f'  - {episode_id}')

    if applied:
        print(f'\nDone. Review with: git diff {CSV_PATH}')


if __name__ == '__main__':
    main()
