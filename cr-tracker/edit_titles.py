#!/usr/bin/env python3
"""
Interactive CLI for fixing up mis-scraped episode rows in
cr_episodes_series_airdates.csv, without hand-editing the CSV directly.

Usage:
    python3 edit_titles.py [search term]

Search for episodes by title/series substring, pick one from the results,
and edit its show type, campaign/series, arc, episode number, and title.
Leave the search blank to browse the most recent episodes by airdate
instead - that's usually where a "weird" row needs fixing. For each field,
press enter to keep its current value, or type "-" to clear it. episode_id
(which embeds several of these fields) is regenerated automatically.
Edits are written straight back to the CSV in place - it's git-tracked, so
`git diff`/`git checkout` is the undo button.
"""

import csv
import sys

CSV_PATH = 'cr_episodes_series_airdates.csv'
RECENT_COUNT = 15

# (csv column, prompt label) - shown/edited in this order.
EDITABLE_FIELDS = [
    ('show_type', 'Show type'),
    ('campaign', 'Campaign/Series'),
    ('arc', 'Arc'),
    ('episode_number', 'Episode #'),
    ('title', 'Title'),
]


def load_rows():
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def save_rows(fieldnames, rows):
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def make_episode_id(row):
    return f"{row['show_type']}|{row['campaign']}|{row['episode_number']}|{row['title']}"


def search(rows, term):
    term = term.lower()
    return [row for row in rows
            if term in row['title'].lower() or term in row['campaign'].lower()]


def most_recent(rows, n=RECENT_COUNT):
    return sorted(rows, key=lambda row: row['airdate'], reverse=True)[:n]


def print_results(matches):
    for i, row in enumerate(matches):
        print(f"  [{i}] {row['title']!r}  ({row['campaign']}, {row['airdate']})")


def edit_row(row):
    print(f"\nEditing: {row['title']!r}  (airdate: {row['airdate']})")
    print(f"  notes: {row['notes']}")
    print("Press enter to keep a field as-is, or type - to clear it.\n")
    changed = False
    for key, label in EDITABLE_FIELDS:
        current = row[key]
        new_value = input(f"{label} [{current}]: ").strip()
        if not new_value:
            continue
        if new_value == '-':
            new_value = ''
        if new_value != current:
            row[key] = new_value
            changed = True
    if not changed:
        print("No changes.")
        return False
    row['episode_id'] = make_episode_id(row)
    return True


def main():
    fieldnames, rows = load_rows()
    initial_term = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else None
    dirty = False

    while True:
        term = initial_term if initial_term is not None else input(
            "\nSearch title (blank for most recent, 'q' to quit): ").strip()
        initial_term = None
        if term.lower() in ('q', 'quit'):
            break

        if term:
            matches = search(rows, term)
            if not matches:
                print("No matches.")
                continue
        else:
            print(f"Most recent {RECENT_COUNT} episodes:")
            matches = most_recent(rows)

        print_results(matches)
        choice = input(f"Pick a result to edit [0-{len(matches) - 1}], or blank to search again: ").strip()
        if not choice:
            continue
        try:
            row = matches[int(choice)]
        except (ValueError, IndexError):
            print("Not a valid choice.")
            continue

        snapshot = dict(row)
        if edit_row(row):
            new_id = row['episode_id']
            collision = next((r for r in rows if r is not row and r['episode_id'] == new_id), None)
            if collision:
                print(f"Warning: this now collides with an existing episode_id ({new_id!r}) - reverting.")
                row.update(snapshot)
                continue
            save_rows(fieldnames, rows)
            dirty = True
            print(f"Saved: {row['title']!r}  ({row['show_type']}, {row['campaign']}, "
                  f"ep {row['episode_number'] or '-'})")

    if dirty:
        print(f"\nDone - changes written to {CSV_PATH}. Review with `git diff {CSV_PATH}`.")
    else:
        print("\nNo changes made.")


if __name__ == '__main__':
    main()
