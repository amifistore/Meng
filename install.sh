#!/bin/bash
echo "=============== MEMULAI INSTALASI LINGKUNGAN ==============="

# 1. Membuat virtual environment
echo "[1/3] Membuat virtual environment di folder 'venv'..."
python3 -m venv venv

# 2. Menyiapkan daftar library
echo "[2/3] Membuat file requirements.txt..."
cat <<EOL > requirements.txt
python-telegram-bot==13.15
requests
flask
EOL

# 3. Menginstall library dari requirements.txt
echo "[3/3] Mengaktifkan venv dan menginstall semua library..."
source venv/bin/activate
pip install -r requirements.txt

echo "✅ INSTALASI SELESAI. Lingkungan siap digunakan."
echo "➡️  Gunakan './start.sh' untuk menjalankan bot."
