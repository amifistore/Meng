#!/usr/bin/env python3
import os
import re

def fix_async_syntax(filepath):
    """Perbaiki error multiple async di semua file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Hapus multiple async (contoh: "async async async def")
    content = re.sub(r'async\s+async\s+async\s+def', 'def', content)
    content = re.sub(r'async\s+async\s+def', 'def', content)
    content = re.sub(r'async\s+def', 'def', content)
    
    # 2. Hapus semua await
    content = re.sub(r'await ', '', content)
    
    # 3. Hapus komentar yang bermasalah
    content = re.sub(r'# ✅.*$', '', content, flags=re.MULTILINE)
    
    # Tulis file yang sudah diperbaiki
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed: {filepath}")
    return filepath

def main():
    handlers_dir = 'handlers'
    
    print("🔄 Memperbaiki semua file handler...")
    print("=" * 50)
    
    # Perbaiki semua file di folder handlers
    for filename in os.listdir(handlers_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(handlers_dir, filename)
            try:
                fix_async_syntax(filepath)
            except Exception as e:
                print(f"❌ Error fixing {filename}: {e}")
    
    print("=" * 50)
    print("🎉 SELESAI! Semua file telah diperbaiki.")
    print("🚀 Sekarang jalankan bot dengan: python main.py")

if __name__ == '__main__':
    main()
