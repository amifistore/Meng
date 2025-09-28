import sqlite3
from datetime import datetime

DB_PATH = "db_bot.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
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
        )
    """)
    conn.commit()
    conn.close()

def simpan_topup(topup_id, user_id, nominal, status="pending", admin_id=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO topup (id, user_id, nominal, status, waktu, admin_id) VALUES (?, ?, ?, ?, ?, ?)",
        (topup_id, user_id, nominal, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), admin_id)
    )
    conn.commit()
    conn.close()

def update_status_topup(topup_id, status, admin_id=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE topup SET status=?, admin_id=? WHERE id=?",
        (status, admin_id, topup_id)
    )
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
