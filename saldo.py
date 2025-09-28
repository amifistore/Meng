# saldo.py - PASTIKAN fungsi get_riwayat_saldo seperti ini:

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
