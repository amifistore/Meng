from telegram import InlineKeyboardMarkup, InlineKeyboardButton

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

def produk_inline_keyboard(produk_list):
    buttons = [
        [InlineKeyboardButton(f"{prod['nama']} ({prod['harga']:,})", callback_data=f"produk|{prod['kode']}")]
        for prod in produk_list
    ]
    buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")])
    return InlineKeyboardMarkup(buttons)

def admin_edit_produk_keyboard(produk_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Edit Harga", callback_data=f"editharga|{produk_id}"),
         InlineKeyboardButton("Edit Deskripsi", callback_data=f"editdeskripsi|{produk_id}")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="manajemen_produk")]
    ])

def get_menu(is_admin=False):
    info_text = (
        "<b>🤖 Selamat datang di Bot PPOB!</b>\n\n"
        "Silakan pilih menu di bawah ini untuk mulai transaksi, cek saldo, riwayat, dan lain-lain."
    )
    markup = main_menu_markup(is_admin=is_admin)
    return info_text, markup
