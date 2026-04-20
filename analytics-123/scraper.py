"""
Voice123 audition scraper — uses the REST API directly with a Bearer token.
No browser needed after initial auth.

First run:  python3 auth.py      (saves token)
Subsequent: python3 scraper.py   (headless, uses saved token)

Token lasts ~24h. Refresh token lasts ~30 days and is used automatically.
If both are expired, run auth.py again.
"""
import base64
import json
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DB_PATH           = Path(__file__).parent / 'auditions.db'
LOCALSTORAGE_PATH = Path(__file__).parent / '.v123_localstorage.json'

BASE_API      = 'https://voice123.com/api'
ACCOUNTS_URL  = 'https://accounts.voice123.com/openid/token'
OAUTH_CLIENT  = '450535'   # Voice123's OpenID Connect client ID
PAGE_SIZE     = 50

CURRENCY_MAP  = {1: 'USD', 2: 'EUR', 3: 'GBP', 4: 'CAD', 5: 'AUD'}

# voice_types IDs observed from the API, mapped to app role_type values.
# Priority order when multiple types are present: character > narration > commercial.
VOICE_TYPE_ROLE = {
    1000: 'commercial',
    1001: 'narration',
    1003: 'narration',
    1004: 'narration',   # audiobook
    1006: 'narration',   # documentary
    1008: 'character',   # video games
    1009: 'narration',   # historical/documentary
    1012: 'narration',   # corporate case study
    1013: 'character',   # animation/dialogue
    1015: 'narration',   # corporate/educational
    1021: 'character',   # dubbing
    1023: 'narration',   # medical/patient
    1026: 'commercial',  # social media / mixed
}
_ROLE_PRIORITY = ['character', 'narration', 'commercial']

def infer_role_type(voice_types):
    mapped = {VOICE_TYPE_ROLE.get(vt) for vt in voice_types} - {None}
    for rt in _ROLE_PRIORITY:
        if rt in mapped:
            return rt
    return None


# ── Token helpers ─────────────────────────────────────────────────────────────

def load_storage():
    if not LOCALSTORAGE_PATH.exists():
        raise SystemExit("No saved session. Run: python3 auth.py")
    return json.loads(LOCALSTORAGE_PATH.read_text())


def save_storage(storage):
    LOCALSTORAGE_PATH.write_text(json.dumps(storage))


def jwt_exp(token):
    try:
        payload_b64 = token.split('.')[1]
        payload_b64 += '=' * (-len(payload_b64) % 4)
        return json.loads(base64.b64decode(payload_b64)).get('exp', 0)
    except Exception:
        return 0


def is_expired(token):
    return jwt_exp(token) < datetime.now(timezone.utc).timestamp()


def refresh_token(rt):
    """Use the refresh token to obtain a new auth_token."""
    data = urllib.parse.urlencode({
        'grant_type':    'refresh_token',
        'refresh_token': rt,
    }).encode()
    req = urllib.request.Request(ACCOUNTS_URL, data=data,
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"[auth] Token refresh failed ({e.code}): {e.read().decode()[:200]}")
        return None


def get_token():
    storage = load_storage()
    token = storage.get('auth_token', '')
    if not token:
        raise SystemExit("No auth token found. Run: python3 auth.py")
    return token, storage


def _do_refresh(storage):
    rt = storage.get('rt', '')
    if not rt:
        raise SystemExit("No refresh token. Run: python3 auth.py")
    result = refresh_token(rt)
    if not result or 'access_token' not in result:
        raise SystemExit("Token refresh failed. Run: python3 auth.py")
    storage['auth_token'] = result['access_token']
    if 'refresh_token' in result:
        storage['rt'] = result['refresh_token']
    save_storage(storage)
    print("[auth] Token refreshed and saved.")
    return storage['auth_token']


# ── API helpers ───────────────────────────────────────────────────────────────

def api_get(path, token, params=None, storage=None):
    url = f'{BASE_API}/{path}'
    if params:
        url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 401 and storage is not None:
            print("[auth] Token rejected (401), attempting refresh...")
            new_token = _do_refresh(storage)
            req2 = urllib.request.Request(url, headers={'Authorization': f'Bearer {new_token}'})
            with urllib.request.urlopen(req2) as resp:
                return json.loads(resp.read())
        raise


def get_provider_id(token):
    data = api_get('users/me', token)
    if data.get('provider_id'):
        return data['provider_id']
    for svc in data.get('services', []):
        if svc.get('service_id') == 'voice_over':
            return svc.get('provider_id')
    return None


def fetch_offers_page(token, provider_id, page, storage=None):
    return api_get('offers/', token, {
        'page':       page,
        'provider_id': provider_id,
        'populate':   'project,samples,winner',
        'trash':      'true',
        'size':       PAGE_SIZE,
        'order':      'newest',
    }, storage=storage)


# ── Parsing ───────────────────────────────────────────────────────────────────

def parse_offer(offer):
    project = offer.get('project') or {}
    sp      = offer.get('service_properties') or {}

    date_submitted = (offer.get('created_at') or '')[:10] or None
    role           = project.get('name')
    proj_sp        = project.get('service_properties') or {}
    voice_types    = proj_sp.get('voice_types') or []
    viewed         = offer.get('status') == 'reviewed' or bool(sp.get('listened_at'))
    liked          = (offer.get('positive_votes') or 0) > 0
    booked         = bool(offer.get('is_winner'))
    pay            = offer.get('price') if booked else None
    currency       = CURRENCY_MAP.get(offer.get('currency', 1), 'USD')
    project_id     = project.get('id')

    return {
        'platform':       'voice123',
        'external_id':    f"v123_{offer['id']}",
        'project_id':     f"v123_proj_{project_id}" if project_id else None,
        'date_submitted': date_submitted,
        'client':         None,
        'role':           role,
        'role_type':      infer_role_type(voice_types),
        'viewed':         1 if viewed else 0,
        'liked':          1 if liked else 0,
        'booked':         1 if booked else 0,
        'pay':            pay,
        'pay_currency':   currency,
    }


# ── Database ──────────────────────────────────────────────────────────────────

def _find_project_dupe(conn, p):
    """Find an existing row that represents the same Voice123 project."""
    if p['project_id']:
        row = conn.execute(
            "SELECT id FROM auditions WHERE platform='voice123' AND project_id=?",
            [p['project_id']]
        ).fetchone()
        if row:
            return row
    # Fallback: match by role name (handles rows created before project_id was stored)
    if p['role']:
        return conn.execute(
            "SELECT id FROM auditions WHERE platform='voice123' AND role=? AND project_id IS NULL",
            [p['role']]
        ).fetchone()
    return None


def upsert(proposals):
    conn = sqlite3.connect(DB_PATH)
    inserted = updated = 0
    try:
        for p in proposals:
            row = conn.execute(
                "SELECT id FROM auditions WHERE platform='voice123' AND external_id=?",
                [p['external_id']]
            ).fetchone()
            if row:
                conn.execute("""
                    UPDATE auditions
                       SET viewed=MAX(COALESCE(viewed,0), ?), liked=MAX(COALESCE(liked,0), ?),
                           booked=MAX(COALESCE(booked,0), ?),
                           pay=CASE WHEN booked=1 THEN pay ELSE COALESCE(pay, ?) END,
                           pay_currency=CASE WHEN booked=1 THEN pay_currency ELSE COALESCE(pay_currency, ?) END,
                           project_id=COALESCE(project_id, ?),
                           role_type=COALESCE(role_type, ?), updated_at=datetime('now')
                     WHERE id=?
                """, [p['viewed'], p['liked'], p['booked'], p['pay'], p['pay_currency'],
                      p['project_id'], p['role_type'], row[0]])
                updated += 1
            else:
                # Voice123 creates a separate offer record when you win a booking.
                # Check if we already have a row for this project before inserting.
                dupe = _find_project_dupe(conn, p)
                if dupe:
                    conn.execute("""
                        UPDATE auditions
                           SET viewed=MAX(COALESCE(viewed,0), ?), liked=MAX(COALESCE(liked,0), ?),
                               booked=MAX(COALESCE(booked,0), ?),
                               pay=CASE WHEN booked=1 THEN pay ELSE COALESCE(pay, ?) END,
                               pay_currency=CASE WHEN booked=1 THEN pay_currency ELSE COALESCE(pay_currency, ?) END,
                               project_id=COALESCE(project_id, ?),
                               role_type=COALESCE(role_type, ?), updated_at=datetime('now')
                         WHERE id=?
                    """, [p['viewed'], p['liked'], p['booked'], p['pay'], p['pay_currency'],
                          p['project_id'], p['role_type'], dupe[0]])
                    updated += 1
                else:
                    conn.execute("""
                        INSERT INTO auditions
                            (platform, external_id, project_id, date_submitted, client, role,
                             role_type, viewed, liked, booked, pay, pay_currency)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [p[k] for k in ('platform', 'external_id', 'project_id', 'date_submitted',
                                         'client', 'role', 'role_type', 'viewed', 'liked',
                                         'booked', 'pay', 'pay_currency')])
                    inserted += 1
        conn.commit()
    finally:
        conn.close()
    return inserted, updated


# ── Main ──────────────────────────────────────────────────────────────────────

TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS auditions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    platform      TEXT NOT NULL,
    external_id   TEXT,
    project_id    TEXT,
    date_submitted TEXT,
    client        TEXT,
    role          TEXT,
    role_type     TEXT,
    viewed        INTEGER DEFAULT 0,
    liked         INTEGER DEFAULT 0,
    booked        INTEGER DEFAULT 0,
    pay           REAL,
    pay_currency  TEXT DEFAULT 'USD',
    notes         TEXT,
    created_at    TEXT DEFAULT (datetime('now')),
    updated_at    TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_external
    ON auditions(platform, external_id)
    WHERE external_id IS NOT NULL;
"""

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(TABLE_SCHEMA)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(auditions)")}
    if 'project_id' not in cols:
        conn.execute("ALTER TABLE auditions ADD COLUMN project_id TEXT")
        conn.commit()
    try:
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_project
                ON auditions(platform, project_id)
                WHERE project_id IS NOT NULL
        """)
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()

def main():
    init_db()
    token, storage = get_token()

    print("[scraper] Fetching provider ID...")
    try:
        provider_id = get_provider_id(token)
        if not provider_id:
            raise ValueError("Could not determine provider ID from /api/users/me")
        print(f"[scraper] Provider ID: {provider_id}")
    except Exception as e:
        print(f"[scraper] Error: {e}")
        return

    print("[scraper] Fetching offers...")
    all_offers = []
    page = 1

    while True:
        try:
            data = fetch_offers_page(token, provider_id, page, storage=storage)
        except Exception as e:
            print(f"  [error] Page {page}: {e}")
            break

        # API may return list or dict with results key
        if isinstance(data, list):
            offers = data
        elif isinstance(data, dict):
            offers = data.get('results') or data.get('items') or data.get('data') or []
        else:
            break

        print(f"  Page {page}: {len(offers)} offers")
        all_offers.extend(offers)

        if len(offers) < PAGE_SIZE:
            break
        page += 1

    if '--debug-offer' in __import__('sys').argv:
        import pprint
        pprint.pprint(all_offers[0] if all_offers else {})
        return

    submitted = [o for o in all_offers if o.get('custom_sample') or o.get('related_samples')]
    print(f"[scraper] {len(all_offers)} total offers, {len(submitted)} with submitted audio")
    parsed = [parse_offer(o) for o in submitted]
    inserted, updated = upsert(parsed)
    print(f"[scraper] Done — {inserted} new, {updated} updated")


if __name__ == '__main__':
    main()
