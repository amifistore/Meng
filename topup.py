# topup.py - VERSI LENGKAP & FIX
import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
DB_PATH = "db_bot.db"

def init_db_topup():
    """Initialize database table untuk topup"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Buat tabel topup
        cur.execute("""
            CREATE TABLE IF NOT EXISTS topup (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                nominal INTEGER,
                status TEXT,           -- 'pending', 'approved', 'canceled'
                waktu TEXT,
                admin_id INTEGER
            )
        """)
        conn.commit()
        conn.close()
        logger.info("✅ Tabel topup siap")
        return True
        
    except Exception as e:
        logger.error(f"❌ Gagal init database topup: {e}")
        return False

def simpan_topup(topup_id, user_id, nominal, status="pending", admin_id=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO topup (id, user_id, nominal, status, waktu, admin_id) VALUES (?, ?, ?, ?, ?, ?)",
            (topup_id, user_id, nominal, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), admin_id)
        )
        conn.commit()
        conn.close()
        logger.info(f"✅ Topup disimpan: {topup_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Gagal simpan topup: {e}")
        return False

def update_status_topup(topup_id, status, admin_id=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("UPDATE topup SET status=?, admin_id=? WHERE id=?",
            (status, admin_id, topup_id)
        )
        conn.commit()
        conn.close()
        logger.info(f"✅ Status topup diupdate: {topup_id} -> {status}")
        return True
    except Exception as e:
        logger.error(f"❌ Gagal update status topup: {e}")
        return False

def get_topup_by_id(topup_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id, user_id, nominal, status, waktu, admin_id FROM topup WHERE id=?", (topup_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                "id": row[0],
                "user_id": row[1],
                "nominal": row[2],
                "status": row[3],
                "waktu": row[4],
                "admin_id": row[5]
            }
        return None
    except Exception as e:
        logger.error(f"❌ Gagal get topup by id: {e}")
        return None

def get_topup_pending_list(limit=20):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id, user_id, nominal, waktu FROM topup WHERE status='pending' ORDER BY waktu DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "id": row[0],
                "user_id": row[1],
                "nominal": row[2],
                "waktu": row[3]
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"❌ Gagal get pending topup: {e}")
        return []

def get_riwayat_topup_user(user_id, limit=10):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id, nominal, status, waktu FROM topup WHERE user_id=? ORDER BY waktu DESC LIMIT ?", (user_id, limit))
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"❌ Gagal get riwayat topup user: {e}")
        return []

def cari_riwayat_topup(user_id=None, status=None, tanggal=None, min_nominal=None, max_nominal=None, limit=20):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        query = "SELECT id, user_id, nominal, status, waktu, admin_id FROM topup WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id=?"
            params.append(user_id)
        if status:
            query += " AND status=?"
            params.append(status)
        if tanggal:
            query += " AND waktu LIKE ?"
            params.append(f"%{tanggal}%")
        if min_nominal:
            query += " AND nominal>=?"
            params.append(min_nominal)
        if max_nominal:
            query += " AND nominal<=?"
            params.append(max_nominal)
            
        query += " ORDER BY waktu DESC LIMIT ?"
        params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"❌ Gagal cari riwayat topup: {e}")
        return []

def get_all_topup_user_ids():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT user_id FROM topup")
        rows = cur.fetchall()
        conn.close()
        return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"❌ Gagal get all topup user ids: {e}")
        return []

# ========== COMPATIBILITY FUNCTIONS ==========

def init_db():
    """Compatibility function for old code"""
    return init_db_topup()

# Initialize database saat module di-load
init_db_topup()
