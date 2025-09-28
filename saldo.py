# saldo.py - PERBAIKI fungsi tambah_saldo_user
def tambah_saldo_user(user_id, jumlah, tipe="topup", keterangan=""):
    """Tambah saldo user"""
    try:
        # PASTIKAN jumlah adalah integer
        if isinstance(jumlah, str):
            jumlah = int(jumlah)
            
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
        
        logger.info(f"✅ Saldo ditambah: user={user_id}, jumlah={jumlah}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Gagal tambah saldo user {user_id}: {e}")
        return False
