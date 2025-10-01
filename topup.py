cat > topup.py << 'EOF'
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Database path
DB_PATH = 'bot_database.db'

def get_connection():
    """Dapatkan koneksi database"""
    return sqlite3.connect(DB_PATH)

def simpan_topup(topup_id, user_id, nominal, status="pending"):
    """Simpan data topup"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO topup (id, user_id, nominal, status)
            VALUES (?, ?, ?, ?)
        ''', (topup_id, user_id, nominal, status))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error simpan_topup: {e}")
        return False

def get_topup_by_id(topup_id):
    """Dapatkan data topup by ID"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM topup WHERE id = ?", (topup_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'user_id': row[1],
                'nominal': row[2],
                'status': row[3],
                'admin_id': row[4],
                'created_at': row[5]
            }
        return None
    except Exception as e:
        logger.error(f"Error get_topup_by_id: {e}")
        return None

def update_status_topup(topup_id, status, admin_id=None):
    """Update status topup"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if admin_id:
            cursor.execute("UPDATE topup SET status = ?, admin_id = ? WHERE id = ?", 
                         (status, admin_id, topup_id))
        else:
            cursor.execute("UPDATE topup SET status = ? WHERE id = ?", (status, topup_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error update_status_topup: {e}")
        return False

def get_topup_pending_list():
    """Dapatkan list topup pending"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM topup WHERE status = 'pending' ORDER BY created_at DESC")
        
        topup_list = []
        for row in cursor.fetchall():
            topup_list.append({
                'id': row[0],
                'user_id': row[1],
                'nominal': row[2],
                'status': row[3],
                'admin_id': row[4],
                'created_at': row[5]
            })
        
        conn.close()
        return topup_list
    except Exception as e:
        logger.error(f"Error get_topup_pending_list: {e}")
        return []

def get_riwayat_topup_user(user_id, limit=10):
    """Dapatkan riwayat topup user"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM topup 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        riwayat = []
        for row in cursor.fetchall():
            riwayat.append({
                'id': row[0],
                'user_id': row[1],
                'nominal': row[2],
                'status': row[3],
                'admin_id': row[4],
                'tanggal': row[5]
            })
        
        conn.close()
        return riwayat
    except Exception as e:
        logger.error(f"Error get_riwayat_topup_user: {e}")
        return []
EOF
