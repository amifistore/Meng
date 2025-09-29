from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from markup import reply_main_menu, admin_panel_keyboard

def admin_panel_callback(update, context):
    user = update.effective_user
    msg = (
        "🛠 <b>Admin Panel</b>\n\n"
        "Silakan pilih fitur admin di bawah:"
    )
    update.message.reply_text(
        msg,
        parse_mode=ParseMode.HTML,
        reply_markup=admin_panel_keyboard()
    )

def admin_panel_menu_callback(update, context):
    query = update.callback_query
    query.answer()
    data = query.data

    if data == "admin_produk":
        msg = "📦 <b>Admin Produk</b>\n\nFitur edit produk (harga/deskripsi/stok) di bawah."
        # Lanjut ke menu produk admin, misal kirim daftar produk dengan tombol edit
        # implementasi bisa custom sesuai handler edit produk yang kamu punya
        query.edit_message_text(msg, parse_mode=ParseMode.HTML)
    elif data == "admin_user":
        msg = "👤 <b>Admin User</b>\n\nFitur admin user (saldo, riwayat, dll)."
        query.edit_message_text(msg, parse_mode=ParseMode.HTML)
    else:
        query.edit_message_text("❌ Fitur tidak dikenal.", parse_mode=ParseMode.HTML)
