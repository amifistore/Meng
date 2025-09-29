from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from markup import get_menu, reply_main_menu, main_menu_markup
from config import ADMIN_IDS

def is_admin(user_id):
    return user_id in ADMIN_IDS

def start(update, context):
    user = update.effective_user
    update.message.reply_text(
        "Selamat datang! Silakan pilih menu:",
        parse_mode=ParseMode.HTML,
        reply_markup=reply_main_menu(is_admin(user.id))
    )

def cancel(update, context):
    user = update.effective_user
    context.user_data.clear()
    if update.callback_query:
        query = update.callback_query
        query.answer()
        query.edit_message_text(
            "❌ Operasi dibatalkan.",
            reply_markup=main_menu_markup(is_admin(user.id))
        )
    else:
        update.message.reply_text(
            "❌ Operasi dibatalkan.",
            reply_markup=reply_main_menu(is_admin(user.id))
        )

def reply_menu_handler(update, context):
    user = update.effective_user
    text = update.message.text.strip().lower()
    admin = is_admin(user.id)

    # --- FIX: Panggil stock_akrab_callback dari reply keyboard ---
    if text in ["cek stok", "📦 cek stok"]:
        # Panggil fungsi stok dengan message, bukan callback_query
        from handlers.stock_handler import stock_akrab_callback
        return stock_akrab_callback(update, context)

    # --- Menu lain tetap seperti biasa ---
    elif text in ["order produk", "🛒 order produk"]:
        from handlers.produk_daftar_handler import lihat_produk_callback
        return lihat_produk_callback(update, context)
    elif text in ["top up saldo", "💳 top up saldo"]:
        from handlers.topup_handler import topup_callback
        return topup_callback(update, context)
    elif text in ["riwayat transaksi", "📋 riwayat transaksi"]:
        from handlers.riwayat_handler import riwayat_callback
        return riwayat_callback(update, context)
    elif text in ["lihat saldo", "💰 lihat saldo"]:
        from handlers.saldo_handler import lihat_saldo_callback
        return lihat_saldo_callback(update, context)
    elif text in ["cek status", "🔍 cek status"]:
        from handlers.status_handler import cek_status_callback
        return cek_status_callback(update, context)
    elif text in ["bantuan", "❓ bantuan", "? bantuan", "❓"]:
        msg = (
            "❓ <b>Pusat Bantuan</b>\n\n"
            "📖 <b>Cara Penggunaan:</b>\n"
            "1. <b>Order Produk</b> - Pilih produk, masukkan nomor tujuan, konfirmasi\n"
            "2. <b>Top Up Saldo</b> - Pilih nominal, konfirmasi, saldo otomatis bertambah\n"
            "3. <b>Cek Stok</b> - Lihat ketersediaan produk\n"
            "4. <b>Riwayat</b> - Lihat history transaksi\n\n"
            "⚠️ <b>Jika mengalami kendala:</b>\n"
            "• Pastikan saldo mencukupi\n"
            "• Periksa nomor tujuan sudah benar\n"
            "• Screenshoot error dan hubungi admin\n\n"
            "📞 <b>Kontak Admin:</b> @admin"
        )
        update.message.reply_text(msg, parse_mode="HTML", reply_markup=reply_main_menu(admin))
        return
    elif text in ["admin panel", "🛠 admin panel"]:
        if admin:
            update.message.reply_text("🛠 <b>Admin Panel</b>\nSilakan pilih menu admin:", parse_mode="HTML", reply_markup=reply_main_menu(True))
        else:
            update.message.reply_text("❌ Kamu bukan admin.", reply_markup=reply_main_menu(False))
        return
    else:
        # Fallback ke menu utama
        update.message.reply_text(
            "Selamat datang! Silakan pilih menu:",
            parse_mode="HTML",
            reply_markup=reply_main_menu(admin)
        )

def main_menu_callback(update, context):
    query = update.callback_query
    user = query.from_user
    data = query.data
    admin = is_admin(user.id)

    try:
        query.answer()
    except Exception:
        pass

    if data in ["back_main", "back_menu"]:
        markup = main_menu_markup(admin)
        query.edit_message_text(
            "🏠 <b>Menu Utama</b>\nSilakan pilih menu berikut:",
            parse_mode=ParseMode.HTML,
            reply_markup=markup
        )
        return

    elif data == "back_admin":
        if admin:
            markup = main_menu_markup(True)
            query.edit_message_text(
                "🛠 <b>Admin Panel</b>\nSilakan pilih menu admin:",
                parse_mode=ParseMode.HTML,
                reply_markup=markup
            )
        else:
            markup = main_menu_markup(False)
            query.edit_message_text(
                "Kembali ke menu utama.",
                reply_markup=markup
            )
        return

    if data == 'beli_produk':
        from handlers.produk_daftar_handler import lihat_produk_callback
        return lihat_produk_callback(update, context)
    elif data == 'topup':
        from handlers.topup_handler import topup_callback
        return topup_callback(update, context)
    elif data == 'stock_akrab':
        from handlers.stock_handler import stock_akrab_callback
        return stock_akrab_callback(update, context)
    elif data == 'riwayat':
        from handlers.riwayat_handler import riwayat_callback
        return riwayat_callback(update, context)
    elif data == 'lihat_saldo':
        from handlers.saldo_handler import lihat_saldo_callback
        return lihat_saldo_callback(update, context)
    elif data == 'cek_status':
        from handlers.status_handler import cek_status_callback
        return cek_status_callback(update, context)
    elif data == "help":
        msg = (
            "❓ <b>Pusat Bantuan</b>\n\n"
            "📖 <b>Cara Penggunaan:</b>\n"
            "1. <b>Order Produk</b> - Pilih produk, masukkan nomor tujuan, konfirmasi\n"
            "2. <b>Top Up Saldo</b> - Pilih nominal, konfirmasi, saldo otomatis bertambah\n"
            "3. <b>Cek Stok</b> - Lihat ketersediaan produk\n"
            "4. <b>Riwayat</b> - Lihat history transaksi\n\n"
            "⚠️ <b>Jika mengalami kendala:</b>\n"
            "• Pastikan saldo mencukupi\n"
            "• Periksa nomor tujuan sudah benar\n"
            "• Screenshoot error dan hubungi admin\n\n"
            "📞 <b>Kontak Admin:</b> @admin"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Hubungi Admin", url="https://t.me/admin")],
            [InlineKeyboardButton("🛒 Order Produk", callback_data="beli_produk")],
            [InlineKeyboardButton("⬅️ Menu Utama", callback_data="back_main")]
        ])
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        return
    else:
        markup = main_menu_markup(admin)
        query.edit_message_text(
            "🏠 <b>Menu Utama</b>\nSilakan pilih menu berikut:",
            parse_mode=ParseMode.HTML,
            reply_markup=markup
        )
        return

# State untuk ConversationHandler (tambahkan sesuai kebutuhan)
CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI = range(3)
