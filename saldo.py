import sqlite3

DB_PATH = "db_bot.db"

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
            cur.execute("INSERT INTO saldo (user_id, saldo) VALUES (?, ?)", (user_id, jumlah))
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
