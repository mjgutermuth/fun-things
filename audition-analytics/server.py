import sqlite3
from pathlib import Path
from flask import Flask, jsonify, request, send_file, abort

app = Flask(__name__, static_folder='.', static_url_path='')
DB_PATH = Path(__file__).parent / 'auditions.db'

SCHEMA = """
CREATE TABLE IF NOT EXISTS auditions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    platform      TEXT NOT NULL,
    external_id   TEXT,
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

VALID_SORTS = {'date_submitted', 'client', 'role', 'role_type', 'platform', 'pay', 'created_at'}
FIELDS = ['platform', 'external_id', 'date_submitted', 'client', 'role', 'role_type',
          'viewed', 'liked', 'booked', 'pay', 'pay_currency', 'notes']


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA)


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
                COALESCE(SUM(CASE WHEN booked=1 THEN pay END),0) AS earnings
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
    total = t['all_count'] or 0

    return jsonify({
        'totals': {
            'all':      total,
            'viewed':   t['viewed']   or 0,
            'liked':    t['liked']    or 0,
            'booked':   t['booked']   or 0,
            'earnings': round(t['earnings'] or 0, 2),
        },
        'rates': {
            'view':    rate(t['viewed'],  total),
            'like':    rate(t['liked'],   total),
            'booking': rate(t['booked'],  total),
        },
        'by_platform':  [dict(r) for r in by_platform],
        'by_role_type': [dict(r) for r in by_role_type],
        'by_month':     [dict(r) for r in by_month],
        'recent_30d':   dict(recent) if recent else {'total': 0, 'booked': 0},
    })


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002, debug=False)
