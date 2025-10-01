#!/usr/bin/env python3
import os
import re

def fix_syntax_errors(filepath):
    """Perbaiki error syntax di semua file handler"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Hapus multiple async (contoh: "async async async def")
    content = re.sub(r'async\s+async\s+async\s+', '', content)
    content = re.sub(r'async\s+async\s+', '', content)
    
    # 2. Hapus semua async dari function definition
    content = re.sub(r'async def (\w+)', r'def \1', content)
    
    # 3. Hapus semua await
    content = re.sub(r'await ', '', content)
    
    # 4. Hapus duplicate imports jika ada
    content = re.sub(r'from telegram import [^\n]+\nfrom telegram import', 'from telegram', content)
    
    # Tulis file yang sudah diperbaiki
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

def main():
    handlers_dir = 'handlers'
    fixed_files = []
    
    print("🔄 Memperbaiki error syntax di semua file handler...")
    print("=" * 50)
    
    # Perbaiki semua file di folder handlers
    for filename in os.listdir(handlers_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(handlers_dir, filename)
            try:
                fix_syntax_errors(filepath)
                fixed_files.append(filename)
                print(f"✅ Fixed: {filename}")
            except Exception as e:
                print(f"❌ Error fixing {filename}: {e}")
    
    # Juga perbaiki main.py jika perlu
    try:
        fix_syntax_errors('main.py')
        fixed_files.append('main.py')
        print(f"✅ Fixed: main.py")
    except Exception as e:
        print(f"❌ Error fixing main.py: {e}")
    
    print("=" * 50)
    print(f"🎉 SELESAI! {len(fixed_files)} file telah diperbaiki.")
    print("\n🚀 Sekarang jalankan bot Anda kembali dengan: python main.py")

if __name__ == '__main__':
    main()
