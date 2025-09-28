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

def get_topup_by_user(user_id, limit=20):
    """Ambil riwayat topup user, hasil list of dict"""
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
        print(f"Error get_topup_by_user: {e}")
        return []

def update_status_topup(topup_id, status, admin_id=None, keterangan=None):
    """Update status topup (misal: approve, batal, dll)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        sql = "UPDATE topup SET status = ?, admin_id = ?, keterangan = keterangan || ? WHERE id = ?"
        tambahan_ket = f"\nStatus diubah menjadi {status} oleh admin {admin_id}." if admin_id else f"\nStatus diubah menjadi {status}."
        cur.execute(sql, (status, admin_id, tambahan_ket if keterangan is None else f"\n{keterangan}", topup_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error update_status_topup: {e}")
        return False

def get_laporan_topup(status=None, user_id=None, limit=50):
    """Laporan admin topup: filter by status/user/limit"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        query = "SELECT id, user_id, nominal, status, tanggal, admin_id, keterangan FROM topup WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        cur.execute(query, params)
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
        print(f"Error get_laporan_topup: {e}")
        return []

def get_topup_detail(topup_id):
    """Ambil detail satu data topup by id"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, nominal, status, tanggal, admin_id, keterangan
            FROM topup
            WHERE id = ?
            LIMIT 1
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
        print(f"Error get_topup_detail: {e}")
        return None
