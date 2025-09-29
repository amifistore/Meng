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

def get_menu(is_admin=False):
    info_text = (
        "<b>🤖 Selamat datang di Bot PPOB!</b>\n\n"
        "Silakan pilih menu di bawah ini untuk mulai transaksi, cek saldo, riwayat, dan lain-lain."
    )
    markup = main_menu_markup(is_admin=is_admin)
    return info_text, markup
