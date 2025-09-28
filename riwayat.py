# riwayat.py - PASTIKAN init_db_riwayat() seperti ini:

def init_db_riwayat():
    """Initialize database table untuk riwayat order"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # ✅ BUAT KEDUA TABEL 
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
    
    # ✅ BUAT TABEL COMPATIBILITY untuk kode lama (database.py)
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
    print("[DEBUG] Tabel riwayat_order & riwayat (compatibility) siap")
