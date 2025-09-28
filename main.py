# find_riwayat_usage.py
import os
import re

def find_riwayat_usage():
    print("=== MENCARI PENGGUNAAN TABEL riwayat ===")
    
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Cari pattern yang mengakses tabel riwayat
                    patterns = [
                        r'FROM\s+riwayat',
                        r'INSERT\s+INTO\s+riwayat',
                        r'UPDATE\s+riwayat',
                        r'riwayat\s+WHERE',
                        r'SELECT.*riwayat',
                        r'DROP TABLE riwayat',
                        r'CREATE TABLE riwayat'
                    ]
                    
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            print(f"❌ Ditemukan di {filepath}:")
                            print(f"   Pattern: {pattern}")
                            # Tampilkan baris yang mengandung pattern
                            lines = content.split('\n')
                            for i, line in enumerate(lines, 1):
                                if re.search(pattern, line, re.IGNORECASE):
                                    print(f"   Line {i}: {line.strip()}")
                            print()
                            
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

if __name__ == "__main__":
    find_riwayat_usage()
