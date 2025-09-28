# saldo.py
import sqlite3

DB_PATH = "db_bot.db"

def init_db_saldo():
    """Initialize database table untuk saldo"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS saldo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            saldo INTEGER DEFAULT 0,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Buat tabel riwayat_saldo jika belum ada
    cur.execute('''
        CREATE TABLE IF NOT EXISTS riwayat_saldo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tipe TEXT NOT NULL,
            jumlah INTEGER NOT NULL,
            keterangan TEXT,
            tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("[DEBUG] Tabel saldo & riwayat_saldo siap")

def get_saldo_user(user_id):
    """Ambil saldo user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT saldo FROM saldo WHERE user_id = ?', (user_id,))
        result = cur.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            # Jika user belum ada, buat record baru dengan saldo 0
            init_saldo_user(user_id)
            return 0
    except Exception as e:
        print(f"[ERROR] Gagal get saldo user {user_id}: {e}")
        return 0

def init_saldo_user(user_id, saldo_awal=0):
    """Initialize saldo untuk user baru"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('''
            INSERT OR IGNORE INTO saldo (user_id, saldo) 
            VALUES (?, ?)
        ''', (user_id, saldo_awal))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Gagal init saldo user {user_id}: {e}")
        return False

def kurang_saldo_user(user_id, jumlah, tipe="order", keterangan=""):
    """Kurangi saldo user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Cek saldo cukup
        saldo_sekarang = get_saldo_user(user_id)
        if saldo_sekarang < jumlah:
            print(f"[ERROR] Saldo tidak cukup: {saldo_sekarang} < {jumlah}")
            return False
        
        # Kurangi saldo
        cur.execute('''
            UPDATE saldo 
            SET saldo = saldo - ?, last_update = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        ''', (jumlah, user_id))
        
        # Catat di riwayat saldo
        cur.execute('''
            INSERT INTO riwayat_saldo (user_id, tipe, jumlah, keterangan)
            VALUES (?, ?, ?, ?)
        ''', (user_id, tipe, -jumlah, keterangan))
        
        conn.commit()
        conn.close()
        
        print(f"[DEBUG] Saldo berhasil dikurangi: user={user_id}, jumlah={jumlah}, saldo_baru={saldo_sekarang - jumlah}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Gagal kurangi saldo user {user_id}: {e}")
        return False

def tambah_saldo_user(user_id, jumlah, tipe="topup", keterangan=""):
    """Tambah saldo user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Pastikan user ada
        init_saldo_user(user_id)
        
        # Tambah saldo
        cur.execute('''
            UPDATE saldo 
            SET saldo = saldo + ?, last_update = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        ''', (jumlah, user_id))
        
        # Catat di riwayat saldo
        cur.execute('''
            INSERT INTO riwayat_saldo (user_id, tipe, jumlah, keterangan)
            VALUES (?, ?, ?, ?)
        ''', (user_id, tipe, jumlah, keterangan))
        
        conn.commit()
        conn.close()
        
        print(f"[DEBUG] Saldo berhasil ditambah: user={user_id}, jumlah={jumlah}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Gagal tambah saldo user {user_id}: {e}")
        return False

def get_riwayat_saldo(user_id=None, limit=10):
    """Ambil riwayat saldo user (compatibility function)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        if user_id:
            # Return: (tipe, jumlah, keterangan, tanggal)
            cur.execute('''
                SELECT tipe, jumlah, keterangan, tanggal 
                FROM riwayat_saldo 
                WHERE user_id = ? 
                ORDER BY id DESC 
                LIMIT ?
            ''', (user_id, limit))
        else:
            # Return: (user_id, tipe, jumlah, keterangan, tanggal) - untuk admin
            cur.execute('''
                SELECT user_id, tipe, jumlah, keterangan, tanggal 
                FROM riwayat_saldo 
                ORDER BY id DESC 
                LIMIT ?
            ''', (limit,))
            
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"[ERROR] Gagal get riwayat saldo: {e}")
        return []

def get_all_user_ids():
    """Ambil semua user ID yang ada di database (compatibility function)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT DISTINCT user_id FROM saldo')
        rows = cur.fetchall()
        conn.close()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"[ERROR] Gagal get all user ids: {e}")
        return []

# ========== COMPATIBILITY FUNCTIONS ==========

def init_db():
    """Compatibility function for old main.py"""
    print("[COMPAT] Using init_db_saldo via init_db()")
    return init_db_saldo()

def init_saldo():
    """Compatibility function"""
    return init_db_saldo()

# Initialize database saat module di-load
init_db_saldo()
