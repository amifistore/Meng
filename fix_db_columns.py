import sqlite3

DB_PATH = "db_bot.db"

def column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return any(col[1] == column for col in cur.fetchall())

def add_column(cur, table, column, coltype, default=None):
    if not column_exists(cur, table, column):
        default_sql = f" DEFAULT {default}" if default is not None else ""
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}{default_sql}")
            print(f"✅ Kolom {column} ditambahkan ke {table}")
        except Exception as e:
            print(f"❌ Error tambah kolom {column} ke {table}: {e}")
    else:
        print(f"ℹ️ Kolom {column} sudah ada di {table}")

def fix_tables():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    add_column(cur, "riwayat_saldo", "perubahan", "INTEGER", 0)
    add_column(cur, "riwayat_saldo", "tipe", "TEXT")
    add_column(cur, "riwayat_saldo", "keterangan", "TEXT")
    add_column(cur, "riwayat_saldo", "tanggal", "TEXT")
    add_column(cur, "topup", "tanggal", "TEXT")
    add_column(cur, "topup", "admin_id", "INTEGER")
    add_column(cur, "topup", "keterangan", "TEXT")
    add_column(cur, "saldo", "nama", "TEXT")
    add_column(cur, "saldo", "tanggal_daftar", "TEXT")

    conn.commit()
    conn.close()
    print("✅ Semua kolom yang hilang telah diperbaiki!")

if __name__ == "__main__":
    fix_tables()
