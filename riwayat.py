cat > riwayat.py << 'EOF'
import sqlite3
import logging

logger = logging.getLogger(__name__)

# Database path
DB_PATH = 'bot_database.db'

def get_connection():
    """Dapatkan koneksi database"""
    return sqlite3.connect(DB_PATH)

def get_riwayat_user(user_id, limit=10):
    """Dapatkan riwayat transaksi user"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM riwayat_order 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        riwayat = []
        for row in cursor.fetchall():
            riwayat.append({
                'id': row[0],
                'user_id': row[1],
                'product_name': row[2],
                'target': row[3],
                'price': row[4],
                'status': row[5],
                'trx_id': row[6],
                'created_at': row[7]
            })
        
        conn.close()
        return riwayat
    except Exception as e:
        logger.error(f"Error get_riwayat_user: {e}")
        return []

def tambah_riwayat(riwayat_data):
    """Tambah riwayat transaksi"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO riwayat_order 
            (user_id, product_name, target, price, status, trx_id) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            riwayat_data['user_id'],
            riwayat_data['product_name'],
            riwayat_data['target'],
            riwayat_data['price'],
            riwayat_data.get('status', 'pending'),
            riwayat_data.get('trx_id', '')
        ))
        
        conn.commit()
        conn.close()
        return {"success": True, "id": cursor.lastrowid}
    except Exception as e:
        logger.error(f"Error tambah_riwayat: {e}")
        return {"success": False, "error": str(e)}
EOF
