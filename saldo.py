import sqlite3
from datetime import datetime

DB_PATH = "db_bot.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS saldo (
            user_id INTEGER PRIMARY KEY,
            saldo INTEGER NOT NULL DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS riwayat_saldo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            waktu TEXT,
            tipe TEXT,         -- 'topup', 'order', 'admin', dll
            nominal INTEGER,   -- +saldo (topup), -saldo (order)
            keterangan TEXT
        )
    """)
    conn.commit()
    conn.close()

def tambah_saldo_user(user_id, nominal, tipe="topup", keterangan=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO saldo (user_id, saldo) VALUES (?, 0)", (user_id,))
    cur.execute("UPDATE saldo SET saldo = saldo + ? WHERE user_id = ?", (nominal, user_id))
    cur.execute("INSERT INTO riwayat_saldo (user_id, waktu, tipe, nominal, keterangan) VALUES (?, ?, ?, ?, ?)",
        (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tipe, nominal, keterangan)
    )
    conn.commit()
    conn.close()

def kurang_saldo_user(user_id, nominal, tipe="order", keterangan=""):
    conn = get_conn()
    cur = conn.cursor()
    # Pastikan user ada, kalau belum insert dulu
    cur.execute("INSERT OR IGNORE INTO saldo (user_id, saldo) VALUES (?, 0)", (user_id,))
    cur.execute("UPDATE saldo SET saldo = saldo - ? WHERE user_id = ?", (nominal, user_id))
    cur.execute("INSERT INTO riwayat_saldo (user_id, waktu, tipe, nominal, keterangan) VALUES (?, ?, ?, ?, ?)",
        (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tipe, -nominal, keterangan)
    )
    conn.commit()
    conn.close()

def get_saldo_user(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT saldo FROM saldo WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0

def get_riwayat_saldo(user_id=None, limit=10):
    conn = get_conn()
    cur = conn.cursor()
    if user_id is None:
        # Admin mode: ambil semua riwayat
        cur.execute("SELECT waktu, user_id, tipe, nominal, keterangan FROM riwayat_saldo ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
    else:
        cur.execute("SELECT waktu, tipe, nominal, keterangan FROM riwayat_saldo WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit))
        rows = cur.fetchall()
    conn.close()
    return rows

def reset_saldo_user(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE saldo SET saldo = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_all_user_ids():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT user_id FROM saldo")
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]
