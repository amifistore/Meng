import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "botdb.sqlite3")

def get_conn():
    return sqlite3.connect(DB_PATH)

def ensure_waktu_column():
    """Pastikan kolom 'waktu' ada di tabel topup. Jika belum, tambahkan."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(topup)")
    columns = [row[1] for row in cur.fetchall()]
    if "waktu" not in columns:
        cur.execute("ALTER TABLE topup ADD COLUMN waktu TEXT;")
        print("✅ Kolom 'waktu' berhasil ditambahkan ke tabel topup.")
    conn.commit()
    conn.close()

def setup_topup_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS topup (
        id TEXT PRIMARY KEY,
        user_id INTEGER,
        nominal INTEGER,
        status TEXT,
        waktu TEXT,
        admin_id INTEGER
    )""")
    conn.commit()
    conn.close()
    ensure_waktu_column()

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

# Untuk inisialisasi manual
if __name__ == "__main__":
    setup_topup_db()
    print("Topup database initialized.")
