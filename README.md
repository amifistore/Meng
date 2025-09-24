# Bot Telegram Penjualan Produk Digital 🤖

Selamat datang di repositori Bot Telegram untuk Penjualan Produk Digital. Bot ini dirancang untuk mengotomatisasi penjualan produk seperti kuota atau pulsa (contoh kasus: Akrab XL/Axis) langsung melalui platform Telegram. Bot ini dilengkapi dengan panel admin, sistem top-up saldo, dan notifikasi transaksi real-time melalui webhook.

Dibuat pada tanggal 24 September 2025.

## Fitur Utama ✨

-   **Menu Pengguna:**
    -   🛒 Beli Produk
    -   💳 Top-up Saldo (QRIS Otomatis & Kode Unik Manual)
    -   📋 Cek Riwayat Transaksi & Riwayat Top-up
    -   📦 Cek Stok Produk Real-time
-   **Panel Admin:**
    -   👥 Manajemen Pengguna (Cek data & saldo)
    -   ⚙️ Manajemen Produk (Ubah harga & deskripsi)
    -   📢 Broadcast Pesan ke semua pengguna
    -   ✅ Konfirmasi Top-up manual
    -   🔑 Generate Kode Unik untuk Top-up
-   **Backend & Integrasi:**
    -   🖥️ Webhook untuk menerima status transaksi (Sukses/Gagal) secara real-time.
    -   🗃️ Database menggunakan SQLite3 untuk menyimpan data pengguna, saldo, dan riwayat.
    -   ⚙️ Arsitektur terpisah antara logika bot (`bot.py`), database (`database.py`), dan server webhook (`webhook_server.py`).

## Struktur Folder 📂
Prasyarat 📋

Sebelum memulai, pastikan sistem Anda telah terinstall:
-   [Python 3.8](https://www.python.org/downloads/) atau versi lebih baru
-   [pip](https://pip.pypa.io/en/stable/installation/) (biasanya sudah terpasang bersama Python)
-   Server atau VPS dengan IP publik (diperlukan agar fitur Webhook berfungsi)

---

## 🚀 Panduan Instalasi (Langkah demi Langkah)

Ikuti langkah-langkah berikut untuk menginstall dan menjalankan bot di server Anda.

### Langkah 1: Clone Repositori

Buka terminal di server Anda, lalu clone repositori ini dan masuk ke dalam direktorinya.

```bash
git clone https://github.com/amifistore/Meng.git
cd Meng

python3 -m venv venv
source venv/bin/activate


pip install -r requirements.txt


python bot.py
