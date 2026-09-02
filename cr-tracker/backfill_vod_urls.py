#!/usr/bin/env python3
"""
Backfill vod_url for CSV rows currently stuck on the generic
'https://www.beacon.tv' placeholder, using Beacon's public GetContentGrid
GraphQL endpoint (see beacon_fetch.py).

Matching strategy per row: look for a Beacon episode released within a few
days of the CSV airdate (Beacon's stored releaseDate can land on an
adjacent calendar day depending on timezone truncation, and Critical Role
Cooldown airdates in this CSV run several days ahead of Beacon's actual
cooldown release for a stretch of Campaign Four - a separate airdate
data-quality issue this pass doesn't touch). A normalized-title overlap
check gates every date-based match, including same-day ones - a collection
can post unrelated content (a recap, a "Campaign Frame") on the same day as
the real episode, so date proximity alone is never trusted. Two campaigns
need dedicated matchers instead of title overlap: Critical Role Cooldown
rows encode a 'C4x12'-style code that maps onto Beacon's 'C4 E012' title
prefix directly, and Tale Gate's CSV titles ("The Soldier's Table") share
no vocabulary with Beacon's own titles ("Discussing Up To Campaign 4,
Episode 11") so they're matched by chronological position instead.

Run from the repo root: python3 backfill_vod_urls.py
Prints a MATCH/MISS report, writes accepted matches back to the CSV, and
lists unmatched rows for manual attention (nothing is silently dropped).
"""
import csv
import re
from datetime import datetime, timedelta

from beacon_fetch import fetch_collection_episodes

CSV_PATH = 'cr_episodes_series_airdates.csv'

CAMPAIGN_TO_SLUG = {
    'Critical Role Cooldown': 'critical-cooldown',
    'Campaign Four': 'campaign-4',
    'Weird Kids': 'weird-kids',
    'Get Your Sheet Together': 'get-your-sheet-together',
    'Age of Umbra': 'age-of-umbra',
    'One-Shot': 'one-shots',
    'Tale Gate': 'tale-gate',
    'Previously On...': 'previously-on',
    'Inside The Legend of Vox Machina': 'inside-the-legend-of-vox-machina',
    'EverythingIsContent': 'everythingiscontent',
    'Fireside Chat': 'fireside-chat',
    # 'Specials' has no single matching Beacon collection - skipped.
}

# Some CSV campaigns don't map 1:1 onto a single Beacon collection - a Live
# Show One-Shot is actually filed under Beacon's 'live-shows' collection,
# and a one-off Weird Kids crossover event landed in 'one-shots' rather than
# 'weird-kids'. Checked as a fallback when the primary collection misses.
EXTRA_SLUGS = {
    'One-Shot': ['live-shows'],
    'Weird Kids': ['one-shots'],
}

DATE_WINDOW = 3
MIN_OVERLAP = 0.4


# Words that recur across nearly every title within a given collection
# (e.g. every Cooldown title contains "cooldown") and so carry no
# disambiguating signal - without stripping these, two completely
# different episodes of the same show can score a misleadingly high
# overlap purely off boilerplate. Caught in practice: 'C4E33 Cooldown'
# (not yet published) scored 0.50 against 'C4 E032 | Road of Dreams |
# Cooldown' on the shared word "cooldown" alone.
STOPWORDS = {'cooldown', 'episode', 'episodes', 'live', 'show', 'critical', 'role', 'beacon', 'the'}


def normalize(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    return set(w for w in text.split() if len(w) > 2 and w not in STOPWORDS)


def title_overlap(a, b):
    wa, wb = normalize(a), normalize(b)
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / min(len(wa), len(wb))


def parse_date(s):
    return datetime.strptime(s, '%Y-%m-%d').date()


def cooldown_code_match(csv_row, episodes):
    """
    Critical Role Cooldown rows encode a campaign+episode code in
    episode_number ('C4x12', or bare '32' for recent Campaign 4 rows) that
    maps directly onto Beacon's own 'C4 E012' title prefix.
    """
    ep = csv_row['episode_number']
    m = re.match(r'^C(\d+)x(\d+)$', ep)
    if m:
        camp, num = m.group(1), int(m.group(2))
    elif ep.isdigit() and csv_row['campaign'] == 'Critical Role Cooldown':
        camp, num = '4', int(ep)  # every plain-numeric cooldown row seen so far is Campaign 4
    else:
        return None
    code = f"c{camp} e{num:03d}"
    matches = [e for e in episodes if code in e['title'].lower()]
    return matches[0] if len(matches) == 1 else None


def ordinal_match(csv_row, episodes):
    """Tale Gate: match by chronological position since titles share no vocabulary (see module docstring)."""
    if csv_row['campaign'] != 'Tale Gate' or not csv_row['episode_number'].isdigit():
        return None
    ordered = sorted(episodes, key=lambda e: e['releaseDate'])
    idx = int(csv_row['episode_number']) - 1
    return ordered[idx] if 0 <= idx < len(ordered) else None


def find_match(csv_row, beacon_by_date):
    """
    Score every candidate within +/-DATE_WINDOW days by title word-overlap.
    Picks the single best-scoring candidate above MIN_OVERLAP, preferring
    an exact-day match when scores tie, and refusing to guess when two
    different candidates tie for best score (e.g. a Cooldown/Backstage-Pass/
    plain triplet posted the same day for one live-show event).
    """
    airdate = parse_date(csv_row['airdate'])
    scored = []
    for delta in range(-DATE_WINDOW, DATE_WINDOW + 1):
        for doc in beacon_by_date.get(airdate + timedelta(days=delta), []):
            score = title_overlap(csv_row['title'], doc['title'])
            scored.append((score, -abs(delta), delta, doc))
    if not scored:
        return None, None, None
    scored.sort(key=lambda x: (-x[0], x[1]))
    best_score, _, best_delta, best_doc = scored[0]
    if best_score < MIN_OVERLAP:
        return None, None, None
    if len(scored) > 1 and scored[1][0] == best_score and scored[1][3]['slug'] != best_doc['slug']:
        return None, None, None
    return best_doc, best_delta, best_score


def _by_date(episodes):
    by_date = {}
    for ep in episodes:
        if not ep['releaseDate']:
            continue
        by_date.setdefault(parse_date(ep['releaseDate']), []).append(ep)
    return by_date


def main():
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    matched = []
    unmatched = []

    for campaign, slug in CAMPAIGN_TO_SLUG.items():
        targets = [r for r in rows if r['campaign'] == campaign and r['vod_url'] == 'https://www.beacon.tv']
        if not targets:
            continue

        print(f"\n=== {campaign} ({slug}) - {len(targets)} rows to fill ===")
        try:
            _, episodes = fetch_collection_episodes(slug)
        except Exception as e:
            print(f"  ERROR fetching {slug}: {e}")
            unmatched.extend((campaign, r, f"fetch error: {e}") for r in targets)
            continue

        beacon_by_date = _by_date(episodes)

        for row in targets:
            doc = cooldown_code_match(row, episodes) or ordinal_match(row, episodes)
            if doc:
                new_url = f"https://beacon.tv/content/{doc['slug']}"
                matched.append((row, new_url))
                print(f"  MATCH  {row['airdate']}  {row['title'][:55]:55s} -> {doc['title'][:55]:55s}  [matched by code/ordinal]")
                continue

            doc, delta, overlap = find_match(row, beacon_by_date)
            source = slug
            if not doc:
                for extra_slug in EXTRA_SLUGS.get(campaign, []):
                    try:
                        _, extra_episodes = fetch_collection_episodes(extra_slug)
                    except Exception as e:
                        print(f"  ERROR fetching fallback {extra_slug}: {e}")
                        continue
                    doc, delta, overlap = find_match(row, _by_date(extra_episodes))
                    if doc:
                        source = extra_slug
                        break

            if doc:
                new_url = f"https://beacon.tv/content/{doc['slug']}"
                matched.append((row, new_url))
                flag = "" if delta == 0 else f"  [date shifted {delta:+d}d, title overlap {overlap:.2f}]"
                extra = f"  (via {source})" if source != slug else ""
                print(f"  MATCH  {row['airdate']}  {row['title'][:55]:55s} -> {doc['title'][:55]:55s}{flag}{extra}")
            else:
                unmatched.append((campaign, row, "no confident match"))
                print(f"  MISS   {row['airdate']}  {row['title'][:70]}")

    print(f"\n\nTOTAL: {len(matched)} matched, {len(unmatched)} unmatched")

    if matched:
        by_episode_id = {row['episode_id']: new_url for row, new_url in matched}
        for row in rows:
            if row['episode_id'] in by_episode_id:
                row['vod_url'] = by_episode_id[row['episode_id']]

        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nWrote {len(matched)} updated vod_url values to {CSV_PATH}")

    if unmatched:
        print(f"\n--- Unmatched rows ({len(unmatched)}) needing manual attention ---")
        for campaign, row, reason in unmatched:
            print(f"  [{campaign}] {row['airdate']} {row['title'][:60]}  ({reason})")


if __name__ == '__main__':
    main()
