import sqlite3

DB_PATH = "db_bot.db"

def init_db_riwayat():
    """Inisialisasi tabel riwayat_order dan riwayat jika belum ada"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS riwayat_order (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ref_id TEXT,
                kode TEXT,
                tujuan TEXT,
                harga INTEGER,
                tanggal TEXT,
                status TEXT,
                sn TEXT,
                keterangan TEXT,
                raw_response TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS riwayat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ref_id TEXT,
                kode TEXT,
                tujuan TEXT,
                harga INTEGER,
                tanggal TEXT,
                status TEXT
            )
        """)
        conn.commit()
        conn.close()
        print("✅ Tabel riwayat siap")
    except Exception as e:
        print(f"Error init_db_riwayat: {e}")

def tambah_riwayat(user_id, transaksi):
    """
    Menambahkan riwayat transaksi ke tabel riwayat_order dan riwayat.
    transaksi = dict dengan key:
      ref_id, kode, tujuan, harga, tanggal, status, sn, keterangan, raw_response
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Simpan ke riwayat_order
        cur.execute(
            "INSERT INTO riwayat_order (user_id, ref_id, kode, tujuan, harga, tanggal, status, sn, keterangan, raw_response) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                transaksi.get("ref_id", ""),
                transaksi.get("kode", ""),
                transaksi.get("tujuan", ""),
                transaksi.get("harga", 0),
                transaksi.get("tanggal", ""),
                transaksi.get("status", ""),
                transaksi.get("sn", ""),
                transaksi.get("keterangan", ""),
                transaksi.get("raw_response", "")
            )
        )
        conn.commit()

        # Simpan ke tabel riwayat
        cur.execute(
            "INSERT INTO riwayat (user_id, ref_id, kode, tujuan, harga, tanggal, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                transaksi.get("ref_id", ""),
                transaksi.get("kode", ""),
                transaksi.get("tujuan", ""),
                transaksi.get("harga", 0),
                transaksi.get("tanggal", ""),
                transaksi.get("status", "")
            )
        )
        conn.commit()

        conn.close()
        return True
    except Exception as e:
        print(f"Error tambah_riwayat: {e}")
        return False

def get_riwayat_order(order_id):
    """Ambil detail satu riwayat order by order_id (id dari riwayat_order)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, ref_id, kode, tujuan, harga, tanggal, status, sn, keterangan, raw_response
            FROM riwayat_order
            WHERE id = ?
            LIMIT 1
        """, (order_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                "id": row[0],
                "user_id": row[1],
                "ref_id": row[2],
                "kode": row[3],
                "tujuan": row[4],
                "harga": row[5],
                "tanggal": row[6],
                "status": row[7],
                "sn": row[8],
                "keterangan": row[9],
                "raw_response": row[10]
            }
        else:
            return None
    except Exception as e:
        print(f"Error get_riwayat_order: {e}")
        return None

def get_riwayat_user(user_id, limit=20):
    """Ambil semua riwayat order untuk user tertentu, hasil list of dict"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, ref_id, kode, tujuan, harga, tanggal, status, sn, keterangan, raw_response
            FROM riwayat_order
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit))
        rows = cur.fetchall()
        conn.close()
        hasil = []
        for row in rows:
            hasil.append({
                "id": row[0],
                "user_id": row[1],
                "ref_id": row[2],
                "kode": row[3],
                "tujuan": row[4],
                "harga": row[5],
                "tanggal": row[6],
                "status": row[7],
                "sn": row[8],
                "keterangan": row[9],
                "raw_response": row[10]
            })
        return hasil
    except Exception as e:
        print(f"Error get_riwayat_user: {e}")
        return []
