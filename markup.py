from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_menu(user_id):
    keyboard = [
        [InlineKeyboardButton("📦 Produk", callback_data="lihat_produk"),
         InlineKeyboardButton("🛒 Beli", callback_data="beli_produk"),
         InlineKeyboardButton("💰 Top Up", callback_data="topup")],
        [InlineKeyboardButton("📋 Riwayat", callback_data="riwayat"),
         InlineKeyboardButton("🔍 Cek Status", callback_data="cek_status"),
         InlineKeyboardButton("📊 Stock XL/Axis", callback_data="stock_akrab")],
        [InlineKeyboardButton("🔧 Manajemen Produk", callback_data="manajemen_produk"),
         InlineKeyboardButton("📑 Semua Riwayat", callback_data="semua_riwayat")],
        [InlineKeyboardButton("💲 Lihat Saldo", callback_data="lihat_saldo"),
         InlineKeyboardButton("➕ Tambah Saldo", callback_data="tambah_saldo")]
    ]
    return InlineKeyboardMarkup(keyboard)

def produk_inline_keyboard():
    # Ambil daftar produk dari produk.py
    from produk import get_produk_list
    produk_list = get_produk_list()
    keyboard = []
    for idx, p in enumerate(produk_list):
        label = f"{p['nama']} - Rp {p['harga']:,}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"produk_static|{idx}")])
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)

def admin_edit_produk_keyboard(kode):
    keyboard = [
        [InlineKeyboardButton("Edit Harga", callback_data=f"editharga|{kode}")],
        [InlineKeyboardButton("Edit Deskripsi", callback_data=f"editdeskripsi|{kode}")],
        [InlineKeyboardButton("Reset Custom", callback_data=f"resetcustom|{kode}")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

def is_admin(user_id):
    # Ganti dengan daftar user admin
    admin_ids = [123456789, 111222333]
    return user_id in admin_ids
