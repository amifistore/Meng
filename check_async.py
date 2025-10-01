#!/usr/bin/env python3
import os
import re

def check_async_functions():
    handlers_dir = 'handlers'
    
    for filename in os.listdir(handlers_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(handlers_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Cari function yang belum async
            functions = re.findall(r'def (\w+)\s*\(\s*update\s*,\s*context\s*\):', content)
            for func_name in functions:
                # Cek apakah function sudah async
                async_pattern = rf'async def {func_name}\s*\(\s*update\s*,\s*context\s*\):'
                if not re.search(async_pattern, content):
                    print(f"❌ {filename}: {func_name} - BELUM ASYNC")
                else:
                    print(f"✅ {filename}: {func_name} - SUDAH ASYNC")

if __name__ == '__main__':
    check_async_functions()
