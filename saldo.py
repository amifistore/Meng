import sqlite3

DB_PATH = "db_bot.db"

def init_db_saldo():
    """Inisialisasi tabel saldo dan riwayat_saldo jika belum ada"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        # Tabel saldo
        cur.execute("""
            CREATE TABLE IF NOT EXISTS saldo (
                user_id INTEGER PRIMARY KEY,
                saldo INTEGER DEFAULT 0,
                nama TEXT,
                tanggal_daftar TEXT
            )
        """)
        # Tabel riwayat_saldo
        cur.execute("""
            CREATE TABLE IF NOT EXISTS riwayat_saldo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                perubahan INTEGER,
                tipe TEXT,
                keterangan TEXT,
                tanggal TEXT
            )
        """)
        conn.commit()
        conn.close()
        print("✅ Tabel saldo & riwayat_saldo siap")
    except Exception as e:
        print(f"Error init_db_saldo: {e}")

def kurang_saldo_user(user_id, jumlah, tipe="order", keterangan=""):
    """
    Mengurangi saldo user, return True jika berhasil, False jika saldo tidak cukup.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Cek saldo saat ini
        cur.execute("SELECT saldo FROM saldo WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        saldo_sekarang = row[0] if row else 0

        if saldo_sekarang < jumlah:
            conn.close()
            return False
        
        # Update saldo
        cur.execute("UPDATE saldo SET saldo = saldo - ? WHERE user_id = ?", (jumlah, user_id))
        conn.commit()
        
        # Catat riwayat saldo
        cur.execute(
            "INSERT INTO riwayat_saldo (user_id, perubahan, tipe, keterangan, tanggal) VALUES (?, ?, ?, ?, datetime('now'))",
            (user_id, -jumlah, tipe, keterangan)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error kurang_saldo_user: {e}")
        return False

def get_saldo_user(user_id):
    """Ambil saldo user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT saldo FROM saldo WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception as e:
        print(f"Error get_saldo_user: {e}")
        return 0

def tambah_saldo_user(user_id, jumlah, tipe="manual", keterangan=""):
    """
    Menambah saldo user, return True jika berhasil.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Jika user belum ada, tambahkan dulu
        cur.execute("SELECT saldo FROM saldo WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO saldo (user_id, saldo, tanggal_daftar) VALUES (?, ?, datetime('now'))", (user_id, jumlah))
        else:
            cur.execute("UPDATE saldo SET saldo = saldo + ? WHERE user_id = ?", (jumlah, user_id))
        conn.commit()

        # Catat riwayat saldo
        cur.execute(
            "INSERT INTO riwayat_saldo (user_id, perubahan, tipe, keterangan, tanggal) VALUES (?, ?, ?, ?, datetime('now'))",
            (user_id, jumlah, tipe, keterangan)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error tambah_saldo_user: {e}")
        return False

def get_riwayat_saldo(user_id, limit=20):
    """
    Mengambil riwayat saldo user dari tabel riwayat_saldo.
    Return: list of dict
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, perubahan, tipe, keterangan, tanggal
            FROM riwayat_saldo
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit))
        rows = cur.fetchall()
        conn.close()
        riwayat = []
        for row in rows:
            riwayat.append({
                "id": row[0],
                "user_id": row[1],
                "perubahan": row[2],
                "tipe": row[3],
                "keterangan": row[4],
                "tanggal": row[5]
            })
        return riwayat
    except Exception as e:
        print(f"Error get_riwayat_saldo: {e}")
        return []
