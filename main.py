import shutil

def init_all_databases():
    """Inisialisasi semua database dengan struktur yang benar"""
    print("🔄 Inisialisasi semua database...")
    try:
        # Hapus cache Python (.pyc dan folder __pycache__)
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(".pyc"):
                    os.remove(os.path.join(root, file))
            for dir in dirs:
                if dir == "__pycache__":
                    shutil.rmtree(os.path.join(root, dir))

        # Import modul untuk trigger auto-init
        import saldo
        import riwayat  
        import topup

        # Paksa re-inisialisasi database
        saldo.init_db_saldo()
        riwayat.init_db_riwayat()
        topup.init_db_topup()

        print("✅ Semua database berhasil diinisialisasi")
        return True

    except Exception as e:
        logger.error(f"❌ Gagal inisialisasi database: {e}")
        return False
