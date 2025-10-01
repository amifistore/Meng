#!/usr/bin/env python3
import os
import re

def fix_async_in_file(filepath):
    """Perbaiki satu file handler menjadi async"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Tambahkan async di semua function handler
    content = re.sub(
        r'def (\w+)\(\s*update\s*,\s*context\s*\):',
        r'async def \1(update, context):', 
        content
    )
    
    # 2. Tambahkan await untuk semua method Telegram
    telegram_methods = [
        'reply_text', 'reply_html', 'reply_markdown', 'edit_message_text',
        'answer', 'edit_message_reply_markup', 'send_message', 'send_document',
        'reply_photo', 'send_photo', 'reply_video', 'send_video'
    ]
    
    for method in telegram_methods:
        # Pattern untuk berbagai variasi pemanggilan
        patterns = [
            rf'(\bupdate\b\.\b{method}\b)',
            rf'(\bquery\b\.\b{method}\b)', 
            rf'(\bupdate\.message\.\b{method}\b)',
            rf'(\bupdate\.effective_message\.\b{method}\b)',
            rf'(\bcontext\.bot\.\b{method}\b)'
        ]
        
        for pattern in patterns:
            # Hanya tambahkan await jika belum ada
            if re.search(pattern, content):
                content = re.sub(pattern, rf'await \1', content)
    
    # Tulis file yang sudah diperbaiki
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

def main():
    handlers_dir = 'handlers'
    fixed_files = []
    
    print("🔄 Memperbaiki semua file handler menjadi async...")
    print("=" * 50)
    
    # Perbaiki semua file di folder handlers
    for filename in os.listdir(handlers_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(handlers_dir, filename)
            try:
                fix_async_in_file(filepath)
                fixed_files.append(filename)
                print(f"✅ Fixed: {filename}")
            except Exception as e:
                print(f"❌ Error fixing {filename}: {e}")
    
    print("=" * 50)
    print(f"🎉 SELESAI! {len(fixed_files)} file handler telah diperbaiki:")
    for file in fixed_files:
        print(f"   - {file}")
    print("\n🚀 Sekarang jalankan bot Anda kembali dengan: python main.py")

if __name__ == '__main__':
    main()
