import base64
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, request, send_file, abort

app = Flask(__name__, static_folder='.', static_url_path='')
DB_PATH             = Path(__file__).parent / 'auditions.db'
LOCALSTORAGE_PATH   = Path(__file__).parent / '.v123_localstorage.json'

SCHEMA = """
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
    project_status TEXT,
    notes         TEXT,
    created_at    TEXT DEFAULT (datetime('now')),
    updated_at    TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_external
    ON auditions(platform, external_id)
    WHERE external_id IS NOT NULL;
"""

VALID_SORTS = {'date_submitted', 'client', 'role', 'role_type', 'platform', 'pay', 'created_at'}
FIELDS = ['platform', 'external_id', 'project_id', 'date_submitted', 'client', 'role',
          'role_type', 'viewed', 'liked', 'booked', 'pay', 'pay_currency', 'project_status', 'notes']


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(auditions)")}
        for col, defn in [('project_id', 'TEXT'), ('project_status', 'TEXT')]:
            if col not in cols:
                conn.execute(f"ALTER TABLE auditions ADD COLUMN {col} {defn}")
        try:
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_project
                    ON auditions(platform, project_id)
                    WHERE project_id IS NOT NULL
            """)
        except Exception:
            pass


@app.route('/')
def index():
    return send_file('index.html')


@app.route('/api/auditions', methods=['GET'])
def list_auditions():
    platform  = request.args.get('platform')
    role_type = request.args.get('role_type')
    viewed    = request.args.get('viewed')
    liked     = request.args.get('liked')
    booked    = request.args.get('booked')
    search    = request.args.get('search', '')
    sort_field = request.args.get('sort', 'date_submitted')
    sort_order = request.args.get('order', 'desc')

    if sort_field not in VALID_SORTS:
        sort_field = 'date_submitted'
    if sort_order not in ('asc', 'desc'):
        sort_order = 'desc'

    query  = "SELECT * FROM auditions WHERE 1=1"
    params = []

    if platform:
        query += " AND platform = ?"; params.append(platform)
    if role_type:
        query += " AND role_type = ?"; params.append(role_type)
    if viewed is not None and viewed != '':
        query += " AND viewed = ?"; params.append(1 if viewed == '1' else 0)
    if liked is not None and liked != '':
        query += " AND liked = ?";  params.append(1 if liked == '1' else 0)
    if booked is not None and booked != '':
        query += " AND booked = ?"; params.append(1 if booked == '1' else 0)
    if search:
        query += " AND (client LIKE ? OR role LIKE ? OR notes LIKE ?)"
        like = f'%{search}%'
        params.extend([like, like, like])

    query += f" ORDER BY COALESCE({sort_field}, '') {sort_order.upper()}"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()

    return jsonify([dict(r) for r in rows])


@app.route('/api/auditions', methods=['POST'])
def create_audition():
    data = request.get_json()
    with get_db() as conn:
        conn.execute(
            f"INSERT INTO auditions ({', '.join(FIELDS)}) VALUES ({', '.join('?' * len(FIELDS))})",
            [data.get(f) for f in FIELDS]
        )
        row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        row = conn.execute("SELECT * FROM auditions WHERE id = ?", [row_id]).fetchone()
    return jsonify(dict(row)), 201


@app.route('/api/auditions/<int:audition_id>', methods=['PUT'])
def update_audition(audition_id):
    data = request.get_json()
    update_fields = [f for f in FIELDS if f in data]
    if not update_fields:
        abort(400)

    with get_db() as conn:
        if not conn.execute("SELECT id FROM auditions WHERE id = ?", [audition_id]).fetchone():
            abort(404)
        sets   = ', '.join(f"{f} = ?" for f in update_fields)
        values = [data[f] for f in update_fields] + [audition_id]
        conn.execute(f"UPDATE auditions SET {sets}, updated_at = datetime('now') WHERE id = ?", values)
        row = conn.execute("SELECT * FROM auditions WHERE id = ?", [audition_id]).fetchone()

    return jsonify(dict(row))


@app.route('/api/auditions/<int:audition_id>', methods=['DELETE'])
def delete_audition(audition_id):
    with get_db() as conn:
        if not conn.execute("SELECT id FROM auditions WHERE id = ?", [audition_id]).fetchone():
            abort(404)
        conn.execute("DELETE FROM auditions WHERE id = ?", [audition_id])
    return '', 204


@app.route('/api/stats', methods=['GET'])
def get_stats():
    with get_db() as conn:
        totals = conn.execute("""
            SELECT
                COUNT(*)                                         AS all_count,
                SUM(viewed)                                      AS viewed,
                SUM(liked)                                       AS liked,
                SUM(booked)                                      AS booked,
                COALESCE(SUM(CASE WHEN booked=1 THEN pay END),0) AS earnings,
                SUM(CASE WHEN booked=0 AND COALESCE(project_status,'active') != 'awarded'
                         THEN 1 ELSE 0 END)                      AS active,
                SUM(CASE WHEN booked=0 AND project_status = 'awarded'
                         THEN 1 ELSE 0 END)                      AS confirmed_rejections
            FROM auditions
        """).fetchone()

        by_platform = conn.execute("""
            SELECT platform,
                COUNT(*)                                         AS total,
                SUM(viewed)                                      AS viewed,
                SUM(liked)                                       AS liked,
                SUM(booked)                                      AS booked,
                COALESCE(SUM(CASE WHEN booked=1 THEN pay END),0) AS earnings
            FROM auditions GROUP BY platform ORDER BY total DESC
        """).fetchall()

        by_role_type = conn.execute("""
            SELECT COALESCE(role_type,'unset') AS role_type,
                COUNT(*)                                         AS total,
                SUM(viewed)                                      AS viewed,
                SUM(liked)                                       AS liked,
                SUM(booked)                                      AS booked,
                COALESCE(SUM(CASE WHEN booked=1 THEN pay END),0) AS earnings
            FROM auditions GROUP BY role_type ORDER BY total DESC
        """).fetchall()

        by_month = conn.execute("""
            SELECT strftime('%Y-%m', date_submitted) AS month,
                COUNT(*)   AS total,
                SUM(booked) AS booked
            FROM auditions
            WHERE date_submitted IS NOT NULL
              AND date_submitted >= date('now', '-12 months')
            GROUP BY month ORDER BY month
        """).fetchall()

        recent = conn.execute("""
            SELECT COUNT(*) AS total, SUM(booked) AS booked
            FROM auditions WHERE date_submitted >= date('now', '-30 days')
        """).fetchone()

    def rate(n, d):
        return round((n or 0) / d, 4) if d else 0

    t = dict(totals)
    total   = t['all_count'] or 0
    viewed  = t['viewed']    or 0
    booked  = t['booked']    or 0
    earnings = round(t['earnings'] or 0, 2)

    return jsonify({
        'totals': {
            'all':      total,
            'viewed':   viewed,
            'liked':    t['liked']  or 0,
            'booked':   booked,
            'earnings': earnings,
            'active':              t['active']              or 0,
            'confirmed_rejections': t['confirmed_rejections'] or 0,
        },
        'rates': {
            'view':               rate(viewed,         total),
            'like':               rate(t['liked'],     total),
            'booking':            rate(booked,         total),
            'liked_of_listened':  rate(t['liked'],     viewed),
            'booked_of_listened': rate(booked,         viewed),
        },
        'derived': {
            'auditions_per_booking': round(total / booked, 1) if booked else None,
            'earnings_per_booking':  round(earnings / booked, 2) if booked else None,
            'earnings_per_audition': round(earnings / total, 2) if total else None,
        },
        'by_platform':  [dict(r) for r in by_platform],
        'by_role_type': [dict(r) for r in by_role_type],
        'by_month':     [dict(r) for r in by_month],
        'recent_30d':   dict(recent) if recent else {'total': 0, 'booked': 0},
    })


def _token_expiry():
    if not LOCALSTORAGE_PATH.exists():
        return None
    try:
        token = json.loads(LOCALSTORAGE_PATH.read_text()).get('auth_token', '')
        payload = token.split('.')[1]
        payload += '=' * (-len(payload) % 4)
        exp = json.loads(base64.b64decode(payload)).get('exp', 0)
        return datetime.fromtimestamp(exp, tz=timezone.utc)
    except Exception:
        return None


@app.route('/auth')
def auth_page():
    expiry = _token_expiry()
    if expiry:
        now = datetime.now(timezone.utc)
        if expiry > now:
            delta = expiry - now
            h = int(delta.total_seconds() // 3600)
            status_html = f'<p class="token-ok">token valid — expires in {h}h ({expiry.strftime("%Y-%m-%d %H:%M")} UTC)</p>'
        else:
            status_html = '<p class="token-expired">token expired</p>'
    else:
        status_html = '<p class="token-expired">no token saved</p>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>analytics 123 — auth</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/styles.css">
  <style>
    .auth-card {{ background: white; border-radius: 12px; padding: 2rem; max-width: 640px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }}
    .steps {{ list-style: none; counter-reset: steps; margin: 1.25rem 0; }}
    .steps li {{ counter-increment: steps; display: flex; gap: 0.75rem; margin-bottom: 0.75rem; line-height: 1.5; }}
    .steps li::before {{ content: counter(steps); background: #a78bfa; color: white; border-radius: 50%; width: 1.4rem; height: 1.4rem; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; flex-shrink: 0; margin-top: 0.1rem; }}
    code {{ background: #f3f0ff; color: #7c3aed; padding: 0.15rem 0.4rem; border-radius: 4px; font-family: inherit; font-size: 0.85em; word-break: break-all; }}
    textarea {{ width: 100%; height: 120px; font-family: inherit; font-size: 0.8rem; border: 2px solid #e9d5ff; border-radius: 8px; padding: 0.75rem; resize: vertical; margin-top: 1rem; }}
    textarea:focus {{ outline: none; border-color: #a78bfa; }}
    .btn {{ background: linear-gradient(135deg, #a78bfa, #8b5cf6); color: white; border: none; padding: 0.65rem 1.5rem; border-radius: 8px; font-family: inherit; font-weight: 700; cursor: pointer; margin-top: 0.75rem; }}
    .btn:hover {{ opacity: 0.9; }}
    .token-ok {{ color: #059669; margin-bottom: 1rem; font-size: 0.85rem; }}
    .token-expired {{ color: #dc2626; margin-bottom: 1rem; font-size: 0.85rem; }}
    #result {{ margin-top: 0.75rem; font-size: 0.85rem; }}
  </style>
</head>
<body>
  <div class="container">
    <header class="site-header">
      <a href="/" class="back-link">← analytics 123</a>
      <h1>auth</h1>
    </header>
    <div class="auth-card">
      {status_html}
      <ol class="steps">
        <li>Open <a href="https://voice123.com" target="_blank">voice123.com</a> in any browser and log in</li>
        <li>Open the console (F12 → Console tab)</li>
        <li>Run: <code>copy(JSON.stringify(Object.fromEntries(Object.entries(localStorage))))</code></li>
        <li>Paste below and click save</li>
      </ol>
      <textarea id="payload" placeholder="paste localStorage JSON here..."></textarea>
      <br>
      <button class="btn" onclick="save()">save token</button>
      <div id="result"></div>
    </div>
  </div>
  <script>
    async function save() {{
      const raw = document.getElementById('payload').value.trim();
      const result = document.getElementById('result');
      if (!raw) {{ result.textContent = 'nothing to save'; return; }}
      try {{
        const r = await fetch('/api/auth', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{payload: raw}}),
        }});
        const data = await r.json();
        if (r.ok) {{
          result.style.color = '#059669';
          result.textContent = data.message;
          document.getElementById('payload').value = '';
        }} else {{
          result.style.color = '#dc2626';
          result.textContent = data.error;
        }}
      }} catch(e) {{
        result.style.color = '#dc2626';
        result.textContent = 'request failed';
      }}
    }}
  </script>
</body>
</html>'''


@app.route('/api/auth', methods=['POST'])
def save_auth():
    data = request.get_json()
    if not data or 'payload' not in data:
        return jsonify({'error': 'missing payload'}), 400
    try:
        storage = json.loads(data['payload'])
    except (json.JSONDecodeError, TypeError):
        return jsonify({'error': 'invalid JSON'}), 400
    if not storage.get('auth_token'):
        return jsonify({'error': 'no auth_token found — make sure you are logged in'}), 400
    LOCALSTORAGE_PATH.write_text(json.dumps(storage))
    expiry = _token_expiry()
    exp_str = expiry.strftime('%Y-%m-%d %H:%M UTC') if expiry else 'unknown'
    return jsonify({'message': f'token saved — expires {exp_str}'})


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002, debug=False)
