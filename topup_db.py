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
        waktu TEXT
    )""")
    conn.commit()
    conn.close()

def simpan_topup(topup_id, user_id, nominal, status="pending"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO topup (id, user_id, nominal, status, waktu)
        VALUES (?, ?, ?, ?, ?)
    """, (
        topup_id, user_id, nominal, status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

def update_status_topup(topup_id, status, admin_id=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE topup SET status=? WHERE id=?", (status, topup_id))
    conn.commit()
    conn.close()

def get_topup_by_id(topup_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, nominal, status, waktu FROM topup WHERE id=?", (topup_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(zip(["id", "user_id", "nominal", "status", "waktu"], row))
    return None

def get_topup_pending_list():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, nominal, status, waktu FROM topup WHERE status='pending' ORDER BY waktu DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(["id", "user_id", "nominal", "status", "waktu"], row)) for row in rows]

# Panggil setup saat inisialisasi bot
if __name__ == "__main__":
    setup_topup_db()
    print("Topup database initialized.")
