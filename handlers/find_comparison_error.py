# find_comparison_error.py
import os
import re

def find_comparison_errors():
    print("=== MENCARI PERBANDINGAN STRING vs INTEGER ===")
    
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Cari pattern perbandingan yang mungkin bermasalah
                    patterns = [
                        r'if .* > .*:',
                        r'if .* < .*:',
                        r'if .* >= .*:',
                        r'if .* <= .*:',
                        r'while .* > .*:',
                        r'while .* < .*:'
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            print(f"⚠️ Ditemukan di {filepath}:")
                            for match in matches[:3]:
                                print(f"   - {match}")
                            
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

if __name__ == "__main__":
    find_comparison_errors()
