from telegram import ReplyKeyboardMarkup, KeyboardButton

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

# Dummy agar import error tidak muncul
def main_menu_markup(is_admin=False):
    return reply_main_menu(is_admin)
