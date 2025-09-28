# riwayat.py
import sqlite3
import time

DB_PATH = "db_bot.db"

def init_db_riwayat():
    """Initialize database table untuk riwayat order"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
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
    conn.commit()
    conn.close()
    print("[DEBUG] Tabel riwayat_order siap")

def tambah_riwayat(user_id, transaksi):
    """
    Tambahkan riwayat transaksi ke database
    
    Args:
        user_id: ID user telegram
        transaksi: dict dengan keys:
            - ref_id, kode, tujuan, harga, status, sn, keterangan, raw_response
    
    Returns:
        bool: True jika berhasil, False jika gagal
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Pastikan semua field required ada
        required_fields = ['ref_id', 'kode', 'tujuan', 'harga', 'status']
        for field in required_fields:
            if field not in transaksi:
                print(f"[ERROR] Field {field} tidak ada di transaksi")
                return False
        
        # Execute insert
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
        
        conn.commit()
        conn.close()
        print(f"[DEBUG] Riwayat berhasil disimpan: {transaksi['ref_id']}")
        return True
        
    except sqlite3.IntegrityError:
        print(f"[ERROR] Ref ID {transaksi['ref_id']} sudah ada di database")
        return False
    except Exception as e:
        print(f"[ERROR] Gagal menyimpan riwayat: {e}")
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
        print(f"[ERROR] Gagal get riwayat user {user_id}: {e}")
        return []

def cari_riwayat_order(user_id=None, ref_id=None, produk=None, status=None, tanggal=None):
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
        query += " ORDER BY id DESC LIMIT 20"
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"[ERROR] Gagal cari riwayat: {e}")
        return []

# ========== COMPATIBILITY FUNCTIONS ==========

def init_db():
    """Compatibility function for old main.py"""
    print("[COMPAT] Using init_db_riwayat via init_db()")
    return init_db_riwayat()

# Initialize database saat module di-load
init_db_riwayat()
