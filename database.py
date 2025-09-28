# database.py - PERBAIKI SEMUA AKSES KE TABEL riwayat
import sqlite3
import time

DB_PATH = "db_bot.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize database - COMPATIBILITY FUNCTION"""
    # Database sudah di-init oleh module lain, jadi tidak perlu buat table di sini
    print("[COMPAT] Database sudah diinisialisasi oleh module lain")
    return True

def simpan_riwayat(ref_id, user_id, produk_kode, tujuan, harga, status="pending", keterangan=""):
    """Simpan riwayat transaksi - COMPATIBILITY FUNCTION"""
    try:
        from riwayat import tambah_riwayat
        
        transaksi = {
            "ref_id": ref_id,
            "kode": produk_kode,
            "tujuan": tujuan,
            "harga": harga,
            "status": status,
            "keterangan": keterangan,
            "sn": "",
            "raw_response": ""
        }
        
        return tambah_riwayat(user_id, transaksi)
        
    except Exception as e:
        print(f"[ERROR] Gagal simpan riwayat: {e}")
        return False

def update_status_riwayat(ref_id, status, keterangan=""):
    """Update status riwayat - COMPATIBILITY FUNCTION"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # Update di riwayat_order (tabel baru)
        cur.execute("UPDATE riwayat_order SET status=?, keterangan=? WHERE ref_id=?", 
                   (status, keterangan, ref_id))
        
        # Juga update di riwayat (tabel compatibility)
        cur.execute("UPDATE riwayat SET status=?, keterangan=? WHERE ref_id=?", 
                   (status, keterangan, ref_id))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Gagal update status riwayat: {e}")
        return False

def get_riwayat_by_refid(ref_id):
    """Ambil riwayat by ref_id - COMPATIBILITY FUNCTION"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # Coba ambil dari riwayat_order dulu
        cur.execute("SELECT * FROM riwayat_order WHERE ref_id=? ORDER BY id DESC LIMIT 1", (ref_id,))
        row = cur.fetchone()
        
        if not row:
            # Fallback ke riwayat (compatibility)
            cur.execute("SELECT * FROM riwayat WHERE ref_id=? ORDER BY id DESC LIMIT 1", (ref_id,))
            row = cur.fetchone()
        
        conn.close()
        return row
        
    except Exception as e:
        print(f"[ERROR] Gagal get riwayat by refid: {e}")
        return None

def get_semua_riwayat(limit=20):
    """Ambil semua riwayat - COMPATIBILITY FUNCTION"""
    try:
        from riwayat import cari_riwayat_order
        return cari_riwayat_order(limit=limit)
        
    except Exception as e:
        print(f"[ERROR] Gagal get semua riwayat: {e}")
        return []

def get_riwayat_user(user_id, limit=10):
    """Ambil riwayat user - COMPATIBILITY FUNCTION"""
    try:
        from riwayat import get_riwayat_user as get_user_riwayat
        return get_user_riwayat(user_id, limit)
        
    except Exception as e:
        print(f"[ERROR] Gagal get riwayat user: {e}")
        return []

# Initialize compatibility
init_db()
