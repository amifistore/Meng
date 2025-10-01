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
        conn.commit()
        conn.close()
        
        return {"success": True, "saldo_sekarang": get_saldo_user(user_id)}
    except Exception as e:
        logger.error(f"Error kurang_saldo_user: {e}")
        return {"success": False, "error": str(e)}
EOF
