from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def reply_main_menu(is_admin=False):
    buttons = [
        [KeyboardButton("🛒 Order Produk"), KeyboardButton("💳 Top Up Saldo")],
        [KeyboardButton("📦 Cek Stok"), KeyboardButton("📋 Riwayat Transaksi")],
        [KeyboardButton("💰 Lihat Saldo"), KeyboardButton("🔍 Cek Status")],
        [KeyboardButton("❓ Bantuan")]
    ]
    if is_admin:
        buttons.append([KeyboardButton("🛠 Admin Panel")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def produk_inline_keyboard(produk_list):
    keyboard = [
        [InlineKeyboardButton(p['nama'], callback_data=f"produk_static|{i}")]
        for i, p in enumerate(produk_list)
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)

def admin_panel_keyboard():
    keyboard = [
        [InlineKeyboardButton("📦 Admin Produk", callback_data="admin_produk")],
        [InlineKeyboardButton("👤 Admin User", callback_data="admin_user")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_edit_produk_keyboard(kode):
    keyboard = [
        [InlineKeyboardButton("Edit Harga", callback_data=f"edit_harga|{kode}")],
        [InlineKeyboardButton("Edit Deskripsi", callback_data=f"edit_deskripsi|{kode}")],
        [InlineKeyboardButton("Reset Custom", callback_data=f"resetcustom|{kode}")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data=f"back_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)
