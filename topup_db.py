import sqlite3
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "botdb.sqlite3")

def get_conn():
    return sqlite3.connect(DB_PATH)

def setup_topup_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS topup (
        id TEXT PRIMARY KEY,
        user_id INTEGER,
        nominal INTEGER,
        status TEXT,           -- 'pending', 'approved', 'canceled'
        waktu TEXT,
        admin_id INTEGER
    )""")
    conn.commit()
    conn.close()

def simpan_topup(topup_id, user_id, nominal, status="pending", admin_id=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO topup (id, user_id, nominal, status, waktu, admin_id) VALUES (?, ?, ?, ?, ?, ?)",
        (
            topup_id,
            user_id,
            nominal,
            status,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            admin_id
        )
    )
    conn.commit()
    conn.close()

def update_status_topup(topup_id, status, admin_id=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE topup SET status=?, admin_id=? WHERE id=?", (status, admin_id, topup_id))
    conn.commit()
    conn.close()

def get_topup_by_id(topup_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, nominal, status, waktu, admin_id FROM topup WHERE id=?", (topup_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "user_id": row[1],
            "nominal": row[2],
            "status": row[3],
            "waktu": row[4],
            "admin_id": row[5]
        }
    return None

def get_topup_pending_list(limit=20):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, nominal, waktu FROM topup WHERE status='pending' ORDER BY waktu DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "user_id": row[1],
            "nominal": row[2],
            "waktu": row[3]
        }
        for row in rows
    ]

def get_riwayat_topup_user(user_id, limit=10):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, nominal, status, waktu FROM topup WHERE user_id=? ORDER BY waktu DESC LIMIT ?", (user_id, limit))
    rows = cur.fetchall()
    conn.close()
    return rows

def cari_riwayat_topup(user_id=None, status=None, tanggal=None, min_nominal=None, max_nominal=None, limit=20):
    conn = get_conn()
    cur = conn.cursor()
    query = "SELECT id, user_id, nominal, status, waktu, admin_id FROM topup WHERE 1=1"
    params = []
    if user_id:
        query += " AND user_id=?"
        params.append(user_id)
    if status:
        query += " AND status=?"
        params.append(status)
    if tanggal:
        query += " AND waktu LIKE ?"
        params.append(f"%{tanggal}%")
    if min_nominal:
        query += " AND nominal>=?"
        params.append(min_nominal)
    if max_nominal:
        query += " AND nominal<=?"
        params.append(max_nominal)
    query += " ORDER BY waktu DESC LIMIT ?"
    params.append(limit)
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_all_topup_user_ids():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT user_id FROM topup")
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]

# Untuk inisialisasi manual
if __name__ == "__main__":
    setup_topup_db()
    print("Topup database initialized.")
