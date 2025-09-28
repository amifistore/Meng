from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def main_menu_markup(is_admin=False):
    buttons = [
        [InlineKeyboardButton("🛒 Order Produk", callback_data="beli_produk")],
        [InlineKeyboardButton("💳 Top Up Saldo", callback_data="topup")],
        [InlineKeyboardButton("📦 Cek Stok", callback_data="stock_akrab")],
        [InlineKeyboardButton("📋 Riwayat Transaksi", callback_data="riwayat")],
        [InlineKeyboardButton("💰 Lihat Saldo", callback_data="lihat_saldo")],
        [InlineKeyboardButton("🔍 Cek Status", callback_data="cek_status")],
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="back_admin")])
    return InlineKeyboardMarkup(buttons)

def admin_menu_markup():
    buttons = [
        [InlineKeyboardButton("📝 Manajemen Produk", callback_data="manajemen_produk")],
        [InlineKeyboardButton("💳 Approve Topup", callback_data="riwayat_topup_admin")],
        [InlineKeyboardButton("👤 Tambah Saldo User", callback_data="tambah_saldo")],
        [InlineKeyboardButton("🏠 Kembali ke Main Menu", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(buttons)

def produk_list_markup(produk_list):
    buttons = [[InlineKeyboardButton(f"{prod['nama']} ({prod['harga']:,})", callback_data=f"produk|{prod['id']}")] for prod in produk_list]
    buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")])
    return InlineKeyboardMarkup(buttons)

def edit_produk_markup(produk_id):
    buttons = [
        [InlineKeyboardButton("Edit Harga", callback_data=f"editharga|{produk_id}"),
         InlineKeyboardButton("Edit Deskripsi", callback_data=f"editdeskripsi|{produk_id}")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="manajemen_produk")]
    ]
    return InlineKeyboardMarkup(buttons)

def admin_edit_produk_keyboard(produk_id):
    return edit_produk_markup(produk_id)

def get_menu(is_admin=False):
    return main_menu_markup(is_admin=is_admin)
