from telegram import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
)

def main_menu_markup(is_admin=False):
    buttons = [
        [InlineKeyboardButton("🛒 Order Produk", callback_data="beli_produk")],
        [InlineKeyboardButton("💳 Top Up Saldo", callback_data="topup")],
        [InlineKeyboardButton("📦 Cek Stok", callback_data="stock_akrab")],
        [InlineKeyboardButton("📋 Riwayat Transaksi", callback_data="riwayat")],
        [InlineKeyboardButton("💰 Lihat Saldo", callback_data="lihat_saldo")],
        [InlineKeyboardButton("🔍 Cek Status", callback_data="cek_status")],
        [InlineKeyboardButton("❓ Bantuan", callback_data="help")]
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="back_admin")])
    return InlineKeyboardMarkup(buttons)

def reply_main_menu(is_admin=False):
    buttons = [
        [KeyboardButton("🛒 Order Produk"), KeyboardButton("💳 Top Up Saldo")],
        [KeyboardButton("📦 Cek Stok"), KeyboardButton("📋 Riwayat Transaksi")],
        [KeyboardButton("💰 Lihat Saldo"), KeyboardButton("🔍 Cek Status")],
        [KeyboardButton("❓ Bantuan")],
    ]
    if is_admin:
        buttons.append([KeyboardButton("🛠 Admin Panel")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_menu(is_admin=False):
    # Bisa dipakai di mana saja, argumen sama seperti reply_main_menu
    buttons = [
        [KeyboardButton("🛒 Order Produk"), KeyboardButton("💳 Top Up Saldo")],
        [KeyboardButton("📦 Cek Stok"), KeyboardButton("📋 Riwayat Transaksi")],
        [KeyboardButton("💰 Lihat Saldo"), KeyboardButton("🔍 Cek Status")],
        [KeyboardButton("❓ Bantuan")],
    ]
    if is_admin:
        buttons.append([KeyboardButton("🛠 Admin Panel")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def produk_inline_keyboard(produk_list=None):
    buttons = []
    # produk_list bisa None atau list
    if produk_list:
        for produk in produk_list:
            buttons.append([InlineKeyboardButton(
                produk.get('nama', str(produk.get('id', 'Produk'))),
                callback_data=f"produk|{produk.get('id')}"
            )])
    else:
        buttons.append([InlineKeyboardButton("Tidak ada produk tersedia", callback_data="produk|none")])
    return InlineKeyboardMarkup(buttons)

def admin_edit_produk_keyboard(produk_id):
    buttons = [
        [InlineKeyboardButton("✏️ Edit Harga", callback_data=f"editharga|{produk_id}")],
        [InlineKeyboardButton("✏️ Edit Deskripsi", callback_data=f"editdeskripsi|{produk_id}")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_admin")]
    ]
    return InlineKeyboardMarkup(buttons)
