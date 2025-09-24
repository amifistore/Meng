#!/bin/bash
echo "🧼 Memulai proses pembersihan..."

# Hapus virtual environment
if [ -d "venv" ]; then
    echo "Menghapus folder virtual environment (venv)..."
    rm -rf venv
fi

# Hapus cache Python
echo "Menghapus cache Python (__pycache__)..."
find . -type d -name "__pycache__" -exec rm -r {} +

# Hapus file log dan requirements
rm -f bot_error.log requirements.txt

echo "✅ Proses pembersihan selesai."
echo "Anda bisa menjalankan './install.sh' lagi untuk instalasi baru."
