from database import tambah_riwayat as db_tambah_riwayat

def tambah_riwayat(user_id, transaksi):
    # Bisa tambahkan log, notifikasi, dll, jika perlu
    return db_tambah_riwayat(user_id, transaksi)
