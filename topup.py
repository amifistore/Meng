import sqlite3

DB_PATH = "db_bot.db"

def init_db_topup():
    """Inisialisasi tabel topup jika belum ada"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS topup (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                nominal INTEGER,
                status TEXT,
                tanggal TEXT,
                admin_id INTEGER,
                keterangan TEXT
            )
        """)
        conn.commit()
        conn.close()
        print("✅ Tabel topup siap")
    except Exception as e:
        print(f"Error init_db_topup: {e}")

def simpan_topup(user_id, nominal, status="pending", admin_id=None, keterangan=""):
    """Simpan data topup ke tabel topup"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO topup (user_id, nominal, status, tanggal, admin_id, keterangan)
            VALUES (?, ?, ?, datetime('now'), ?, ?)
        """, (user_id, nominal, status, admin_id, keterangan))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error simpan_topup: {e}")
        return False

def get_topup_by_id(topup_id):
    """Ambil detail topup berdasarkan ID (untuk handler detail/topup admin)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, nominal, status, tanggal, admin_id, keterangan
            FROM topup WHERE id = ? LIMIT 1
        """, (topup_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                "id": row[0],
                "user_id": row[1],
                "nominal": row[2],
                "status": row[3],
                "tanggal": row[4],
                "admin_id": row[5],
                "keterangan": row[6]
            }
        else:
            return None
    except Exception as e:
        print(f"Error get_topup_by_id: {e}")
        return None

def get_riwayat_topup_user(user_id, limit=20):
    """Ambil riwayat topup user, hasil list of dict (untuk handler riwayat)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, nominal, status, tanggal, admin_id, keterangan
            FROM topup
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit))
        rows = cur.fetchall()
        conn.close()
        topups = []
        for row in rows:
            topups.append({
                "id": row[0],
                "user_id": row[1],
                "nominal": row[2],
                "status": row[3],
                "tanggal": row[4],
                "admin_id": row[5],
                "keterangan": row[6]
            })
        return topups
    except Exception as e:
        print(f"Error get_riwayat_topup_user: {e}")
        return []

def update_status_topup(topup_id, status):
    """
    Update status topup pada tabel topup.
    status: misal "pending", "approved", "rejected"
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("UPDATE topup SET status = ? WHERE id = ?", (status, topup_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error update_status_topup: {e}")
        return False

def get_topup_pending_list(limit=20):
    """
    Ambil daftar topup yang statusnya 'pending' untuk admin approve/reject.
    Return: list of dict [{id, user_id, nominal, status, tanggal, admin_id, keterangan}, ...]
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, nominal, status, tanggal, admin_id, keterangan
            FROM topup
            WHERE status = 'pending'
            ORDER BY tanggal DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "user_id": row[1],
                "nominal": row[2],
                "status": row[3],
                "tanggal": row[4],
                "admin_id": row[5],
                "keterangan": row[6]
            })
        return result
    except Exception as e:
        print(f"Error get_topup_pending_list: {e}")
        return []

def get_all_topup(limit=50):
    """
    Ambil seluruh data topup (untuk admin, laporan, dsb)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, nominal, status, tanggal, admin_id, keterangan
            FROM topup
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "user_id": row[1],
                "nominal": row[2],
                "status": row[3],
                "tanggal": row[4],
                "admin_id": row[5],
                "keterangan": row[6]
            })
        return result
    except Exception as e:
        print(f"Error get_all_topup: {e}")
        return []
