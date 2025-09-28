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
