import sqlite3

DB_PATH = "db_bot.db"

def cari_riwayat_order(user_id=None, ref_id=None, produk=None, status=None, tanggal=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    query = "SELECT ref_id, produk, harga, tujuan, status, tanggal, sn FROM riwayat_order WHERE 1=1"
    params = []
    if user_id:
        query += " AND user_id=?"
        params.append(user_id)
    if ref_id:
        query += " AND ref_id LIKE ?"
        params.append(f"%{ref_id}%")
    if produk:
        query += " AND produk LIKE ?"
        params.append(f"%{produk}%")
    if status:
        query += " AND status=?"
        params.append(status)
    if tanggal:
        query += " AND tanggal LIKE ?"
        params.append(f"%{tanggal}%")
    query += " ORDER BY id DESC LIMIT 20"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows
