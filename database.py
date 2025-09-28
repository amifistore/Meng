import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "botdb.sqlite3")

def get_conn():
    return sqlite3.connect(DB_PATH)

def setup_db():
    conn = get_conn()
    cur = conn.cursor()
    # Tabel user saldo
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_saldo (
        user_id INTEGER PRIMARY KEY,
        saldo INTEGER DEFAULT 0
    )""")
    # Tabel riwayat transaksi
    cur.execute("""
    CREATE TABLE IF NOT EXISTS riwayat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ref_id TEXT,
        user_id INTEGER,
        produk_kode TEXT,
        tujuan TEXT,
        harga INTEGER,
        tanggal TEXT,
        status TEXT,
        keterangan TEXT
    )""")
    conn.commit()
    conn.close()

def get_saldo(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT saldo FROM user_saldo WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0

def tambah_saldo(user_id, nominal):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO user_saldo(user_id, saldo) VALUES (?, 0)", (user_id,))
    cur.execute("UPDATE user_saldo SET saldo=saldo+? WHERE user_id=?", (nominal, user_id))
    conn.commit()
    conn.close()

def kurang_saldo(user_id, nominal):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE user_saldo SET saldo=saldo-? WHERE user_id=?", (nominal, user_id))
    conn.commit()
    conn.close()

def tambah_riwayat(user_id, transaksi):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO riwayat (ref_id, user_id, produk_kode, tujuan, harga, tanggal, status, keterangan)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        transaksi.get("ref_id"),
        user_id,
        transaksi.get("kode"),
        transaksi.get("tujuan"),
        transaksi.get("harga"),
        transaksi.get("tanggal", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        transaksi.get("status"),
        transaksi.get("sn") or transaksi.get("keterangan") or ""
    ))
    conn.commit()
    conn.close()

def get_riwayat_by_refid(ref_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM riwayat WHERE ref_id=? ORDER BY id DESC LIMIT 1", (ref_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_riwayat_status(ref_id, status, keterangan):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE riwayat SET status=?, keterangan=? WHERE ref_id=?", (status, keterangan, ref_id))
    conn.commit()
    conn.close()

def get_all_user_ids():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM user_saldo")
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_riwayat_saldo(user_id=None, limit=10):
    conn = get_conn()
    cur = conn.cursor()
    if user_id is None:
        cur.execute("SELECT tanggal, user_id, status, harga, keterangan FROM riwayat ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
    else:
        cur.execute("SELECT tanggal, status, harga, keterangan FROM riwayat WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit))
        rows = cur.fetchall()
    conn.close()
    return rows

# Panggil setup_db() sekali saat inisialisasi
if __name__ == "__main__":
    setup_db()
    print("Database initialized.")
