cat > saldo.py << 'EOF'
import sqlite3
import logging

logger = logging.getLogger(__name__)

# Database path
DB_PATH = 'bot_database.db'

def get_connection():
    """Dapatkan koneksi database"""
    return sqlite3.connect(DB_PATH)

def get_saldo_user(user_id):
    """Dapatkan saldo user"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT saldo FROM saldo WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            # Jika user belum ada, buat entry baru dengan saldo 0
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO saldo (user_id, saldo) VALUES (?, 0)", (user_id,))
            conn.commit()
            conn.close()
            return 0
    except Exception as e:
        logger.error(f"Error get_saldo_user: {e}")
        return 0

def tambah_saldo_user(user_id, amount, tipe="topup", keterangan=""):
    """Tambah saldo user"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Update saldo
        cursor.execute('''
            INSERT INTO saldo (user_id, saldo) 
            VALUES (?, ?) 
            ON CONFLICT(user_id) DO UPDATE SET 
            saldo = saldo + excluded.saldo,
            last_update = CURRENT_TIMESTAMP
        ''', (user_id, amount))
        
        # Simpan riwayat
        cursor.execute('''
            INSERT INTO riwayat_saldo (user_id, tipe, perubahan, keterangan)
            VALUES (?, ?, ?, ?)
        ''', (user_id, tipe, amount, keterangan))
        
        conn.commit()
        conn.close()
        return {"success": True, "saldo_sekarang": get_saldo_user(user_id)}
    except Exception as e:
        logger.error(f"Error tambah_saldo_user: {e}")
        return {"success": False, "error": str(e)}

def kurang_saldo_user(user_id, amount):
    """Kurangi saldo user"""
    try:
        saldo_sekarang = get_saldo_user(user_id)
        if saldo_sekarang < amount:
            return {"success": False, "message": "Saldo tidak cukup", "saldo_sekarang": saldo_sekarang}
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE saldo SET saldo = saldo - ? WHERE user_id = ?", (amount, user_id))
        
        # Simpan riwayat
        cursor.execute('''
            INSERT INTO riwayat_saldo (user_id, tipe, perubahan, keterangan)
            VALUES (?, ?, ?, ?)
        ''', (user_id, "order", -amount, "Pembelian produk"))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "saldo_sekarang": get_saldo_user(user_id)}
    except Exception as e:
        logger.error(f"Error kurang_saldo_user: {e}")
        return {"success": False, "error": str(e)}

def get_riwayat_saldo(user_id=None, limit=10, admin_mode=False):
    """Dapatkan riwayat saldo"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if admin_mode and user_id is None:
            # Mode admin - semua riwayat
            cursor.execute('''
                SELECT tanggal, user_id, tipe, perubahan, keterangan 
                FROM riwayat_saldo 
                ORDER BY tanggal DESC 
                LIMIT ?
            ''', (limit,))
        else:
            # Mode user - riwayat user tertentu
            cursor.execute('''
                SELECT tanggal, user_id, tipe, perubahan, keterangan 
                FROM riwayat_saldo 
                WHERE user_id = ? 
                ORDER BY tanggal DESC 
                LIMIT ?
            ''', (user_id, limit))
        
        riwayat = []
        for row in cursor.fetchall():
            riwayat.append({
                "tanggal": row[0],
                "user_id": row[1],
                "tipe": row[2],
                "perubahan": row[3],
                "keterangan": row[4]
            })
        
        conn.close()
        return riwayat
    except Exception as e:
        logger.error(f"Error get_riwayat_saldo: {e}")
        return []

def get_all_user_ids():
    """Dapatkan semua user_id yang ada"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT user_id FROM saldo")
        user_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return user_ids
    except Exception as e:
        logger.error(f"Error get_all_user_ids: {e}")
        return []
EOF
