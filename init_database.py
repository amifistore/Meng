cat > init_database.py << 'EOF'
#!/usr/bin/env python3
import sqlite3
import os

def init_database():
    """Inisialisasi database dengan tabel yang diperlukan"""
    db_path = 'bot_database.db'
    
    # Hapus database lama jika ada
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Database lama dihapus")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Buat tabel saldo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saldo (
            user_id INTEGER PRIMARY KEY,
            saldo INTEGER DEFAULT 0,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Buat tabel riwayat_order
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS riwayat_order (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_name TEXT,
            target TEXT,
            price INTEGER,
            status TEXT,
            trx_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Buat tabel topup
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topup (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            nominal INTEGER,
            status TEXT,
            admin_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert data sample
    cursor.execute("INSERT OR IGNORE INTO saldo (user_id, saldo) VALUES (6738243352, 100000)")
    cursor.execute("INSERT OR IGNORE INTO saldo (user_id, saldo) VALUES (7366367635, 50000)")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database diinisialisasi: {db_path}")
    print("✅ Tabel created: saldo, riwayat_order, topup")
    print("✅ Sample data inserted")

if __name__ == '__main__':
    init_database()
EOF

python init_database.py
