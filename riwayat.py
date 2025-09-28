import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "db_bot.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def setup_db():
    conn = get_conn()
    cur = conn.cursor()
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
        )
    """)
    conn.commit()
    conn.close()

# Tambahkan fungsi-fungsi lain sesuai kebutuhan:
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
        transaksi.get("tanggal"),
        transaksi.get("status"),
        transaksi.get("sn") or transaksi.get("keterangan") or ""
    ))
    conn.commit()
    conn.close()
