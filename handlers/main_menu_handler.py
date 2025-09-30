from telegram import ParseMode
from markup import reply_main_menu
from config import ADMIN_IDS

def start(update, context):
    user = update.message.from_user
    is_admin = user.id in ADMIN_IDS
    
    welcome_text = (
        "🤖 *SELAMAT DATANG DI BOT RESELLER* 🤖\n\n"
        "Silakan pilih menu yang tersedia:\n\n"
        "🛒 *Order Produk* - Beli produk digital\n"
        "💳 *Top Up Saldo* - Isi saldo akun\n"
        "📦 *Cek Stok* - Lihat stok produk\n"
        "📋 *Riwayat Transaksi* - Lihat history order\n"
        "💰 *Lihat Saldo* - Cek saldo Anda\n"
        "🔍 *Cek Status* - Cek status order\n"
        "❓ *Bantuan* - Panduan penggunaan\n"
    )
    
    if is_admin:
        welcome_text += "\n🛠 *Admin Panel* - Menu khusus admin"
    
    update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_main_menu(is_admin=is_admin)
    )

def cancel(update, context):
    user = update.effective_user
    is_admin = user.id in ADMIN_IDS
    context.user_data.clear()
    
    if update.callback_query:
        update.callback_query.answer()
        update.callback_query.edit_message_text(
            "❌ Operasi dibatalkan.",
            reply_markup=reply_main_menu(is_admin=is_admin)
        )
    else:
        update.message.reply_text(
            "❌ Operasi dibatalkan.",
            reply_markup=reply_main_menu(is_admin=is_admin)
        )

def reply_menu_handler(update, context):
    user = update.message.from_user
    text = update.message.text
    is_admin = user.id in ADMIN_IDS
    
    # Handle menu yang belum ada handler khusus
    if text == "❓ Bantuan":
        help_text = (
            "📖 *PANDUAN PENGGUNAAN BOT*\n\n"
            "1. 🛒 *Order Produk* - Pilih produk, input nomor tujuan, konfirmasi\n"
            "2. 💳 *Top Up Saldo* - Transfer ke admin untuk isi saldo\n"
            "3. 📦 *Cek Stok* - Lihat ketersediaan produk\n"
            "4. 📋 *Riwayat* - History transaksi Anda\n"
            "5. 💰 *Saldo* - Cek saldo akun\n"
            "6. 🔍 *Status* - Cek status order terakhir\n\n"
            "❓ Butuh bantuan? Hubungi admin."
        )
        update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text(
            "ℹ️ Pilih menu yang tersedia di keyboard bawah.",
            reply_markup=reply_main_menu(is_admin=is_admin)
        )
