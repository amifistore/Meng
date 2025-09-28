import sqlite3

DB_PATH = "db_bot.db"

def init_db_topup():
    """Inisialisasi tabel topup jika belum ada"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS topup (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                nominal INTEGER,
                status TEXT,
                tanggal TEXT,
                admin_id INTEGER,
                keterangan TEXT
            )
        """)
        conn.commit()
        conn.close()
        print("✅ Tabel topup siap")
    except Exception as e:
        print(f"Error init_db_topup: {e}")
