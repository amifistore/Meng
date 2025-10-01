cat > init_db.py << 'EOF'
import sqlite3
import os

def init_db():
    db_path = 'bot_database.db'
    
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Database lama dihapus")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE saldo (
            user_id INTEGER PRIMARY KEY,
            saldo INTEGER DEFAULT 0,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE riwayat_order (
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
    
    cursor.execute('''
        CREATE TABLE topup (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            nominal INTEGER,
            status TEXT,
            admin_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE riwayat_saldo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tipe TEXT,
            perubahan INTEGER,
            keterangan TEXT,
            tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute("INSERT INTO saldo (user_id, saldo) VALUES (6738243352, 100000)")
    cursor.execute("INSERT INTO saldo (user_id, saldo) VALUES (7366367635, 50000)")
    
    conn.commit()
    conn.close()
    print("✅ Database diinisialisasi")

if __name__ == '__main__':
    init_db()
EOF
