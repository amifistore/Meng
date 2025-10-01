#!/usr/bin/env python3
import os
import re

def fix_async_functions():
    handlers_dir = 'handlers'
    
    for filename in os.listdir(handlers_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(handlers_dir, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. Tambahkan async di function definition
            new_content = re.sub(
                r'def (\w+)\(\s*update\s*,\s*context\s*\):',
                r'async def \1(update, context):',
                content
            )
            
            # 2. Tambahkan await untuk method Telegram
            telegram_methods = [
                'reply_text', 'reply_html', 'reply_markdown', 'edit_message_text',
                'answer', 'edit_message_reply_markup', 'send_message', 'send_document'
            ]
            
            for method in telegram_methods:
                # Pattern: update.method atau query.method tanpa await
                pattern1 = rf'(\bupdate\b\.\b{method}\b)'
                replacement1 = rf'await \1'
                new_content = re.sub(pattern1, replacement1, new_content)
                
                pattern2 = rf'(\bquery\b\.\b{method}\b)'
                replacement2 = rf'await \2'
                new_content = re.sub(pattern2, replacement2, new_content)
                
                pattern3 = rf'(\bupdate\.message\.\b{method}\b)'
                replacement3 = rf'await \3'
                new_content = re.sub(pattern3, replacement3, new_content)
                
                pattern4 = rf'(\bupdate\.effective_message\.\b{method}\b)'
                replacement4 = rf'await \4'
                new_content = re.sub(pattern4, replacement4, new_content)
            
            # Tulis file yang sudah diperbaiki
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ Fixed: {filename}")

if __name__ == '__main__':
    print("🔄 Memperbaiki semua function menjadi async...")
    fix_async_functions()
    print("🎉 Selesai! Semua file sudah diperbaiki.")
