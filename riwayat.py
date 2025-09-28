# riwayat.py - VERSI LENGKAP & FIX
import sqlite3
import logging

logger = logging.getLogger(__name__)
DB_PATH = "db_bot.db"

def init_db_riwayat():
    """Initialize database table untuk riwayat order"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Tabel riwayat_order (baru)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS riwayat_order (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ref_id TEXT NOT NULL UNIQUE,
                produk TEXT NOT NULL,
                harga INTEGER NOT NULL,
                tujuan TEXT NOT NULL,
                status TEXT NOT NULL,
                sn TEXT,
                keterangan TEXT,
                raw_response TEXT,
                tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabel riwayat (compatibility untuk kode lama)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS riwayat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ref_id TEXT NOT NULL UNIQUE,
                produk_kode TEXT NOT NULL,
                tujuan TEXT NOT NULL,
                harga INTEGER NOT NULL,
                tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                keterangan TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Tabel riwayat_order & riwayat siap")
        return True
        
    except Exception as e:
        logger.error(f"❌ Gagal init database riwayat: {e}")
        return False

def tambah_riwayat(user_id, transaksi):
    """
    Tambahkan riwayat transaksi ke database
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Validasi field required
        required_fields = ['ref_id', 'kode', 'tujuan', 'harga', 'status']
        for field in required_fields:
            if field not in transaksi:
                logger.error(f"❌ Field {field} tidak ada di transaksi")
                return False
        
        # Insert ke riwayat_order
        cur.execute('''
            INSERT INTO riwayat_order 
            (user_id, ref_id, produk, harga, tujuan, status, sn, keterangan, raw_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            transaksi['ref_id'],
            transaksi['kode'],
            transaksi['harga'],
            transaksi['tujuan'],
            transaksi['status'],
            transaksi.get('sn', ''),
            transaksi.get('keterangan', ''),
            transaksi.get('raw_response', '')
        ))
        
        # Juga insert ke riwayat (compatibility)
        cur.execute('''
            INSERT OR IGNORE INTO riwayat 
            (user_id, ref_id, produk_kode, tujuan, harga, status, keterangan)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            transaksi['ref_id'],
            transaksi['kode'],
            transaksi['tujuan'],
            transaksi['harga'],
            transaksi['status'],
            transaksi.get('keterangan', '')
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Riwayat disimpan: {transaksi['ref_id']}")
        return True
        
    except sqlite3.IntegrityError:
        logger.error(f"❌ Ref ID {transaksi['ref_id']} sudah ada")
        return False
    except Exception as e:
        logger.error(f"❌ Gagal simpan riwayat: {e}")
        return False

def get_riwayat_user(user_id, limit=10):
    """Ambil riwayat order user tertentu"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('''
            SELECT ref_id, produk, harga, tujuan, status, tanggal, sn, keterangan
            FROM riwayat_order 
            WHERE user_id = ? 
            ORDER BY id DESC 
            LIMIT ?
        ''', (user_id, limit))
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"❌ Gagal get riwayat user {user_id}: {e}")
        return []

def cari_riwayat_order(user_id=None, ref_id=None, produk=None, status=None, tanggal=None, limit=20):
    """Cari riwayat order berdasarkan filter"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        query = "SELECT ref_id, produk, harga, tujuan, status, tanggal, sn FROM riwayat_order WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id=?"
            params.append(user_id)
        if ref_id:
            query += " AND ref_id LIKE ?"
            params.append(f"%{ref_id}%")
        if produk:
            query += " AND produk LIKE ?"
            params.append(f"%{produk}%")
        if status:
            query += " AND status=?"
            params.append(status)
        if tanggal:
            query += " AND tanggal LIKE ?"
            params.append(f"%{tanggal}%")
            
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"❌ Gagal cari riwayat: {e}")
        return []

# ========== COMPATIBILITY FUNCTIONS ==========

def init_db():
    """Compatibility function for old code"""
    return init_db_riwayat()

# Initialize database saat module di-load
init_db_riwayat()
