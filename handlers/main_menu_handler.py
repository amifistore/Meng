import logging
from telegram import ParseMode
from markup import reply_main_menu
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
    update.message.reply_text(
        "❌ Operasi dibatalkan.",
        reply_markup=reply_main_menu(is_admin(user.id))
    )

def reply_menu_handler(update, context):
    user = update.effective_user
    text = update.message.text.strip().lower()
    admin = is_admin(user.id)

    if "order produk" in text:
        from handlers.produk_daftar_handler import lihat_produk_callback
        return lihat_produk_callback(update, context)
    elif "cek stok" in text:
        from handlers.stock_handler import stock_akrab_callback
        return stock_akrab_callback(update, context)
    elif "top up saldo" in text:
        from handlers.topup_handler import topup_callback
        return topup_callback(update, context)
    elif "riwayat transaksi" in text:
        from handlers.riwayat_handler import riwayat_callback
        return riwayat_callback(update, context)
    elif "lihat saldo" in text:
        from handlers.saldo_handler import lihat_saldo_callback
        return lihat_saldo_callback(update, context)
    elif "cek status" in text:
        from handlers.status_handler import cek_status_callback
        return cek_status_callback(update, context)
    elif "bantuan" in text or "❓" in text or "?" in text:
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
    elif "admin panel" in text:
        if admin:
            update.message.reply_text("🛠 <b>Admin Panel</b>\nSilakan pilih menu admin:", parse_mode="HTML", reply_markup=reply_main_menu(True))
        else:
            update.message.reply_text("❌ Kamu bukan admin.", reply_markup=reply_main_menu(False))
        return
    else:
        update.message.reply_text(
            "Selamat datang! Silakan pilih menu:",
            parse_mode="HTML",
            reply_markup=reply_main_menu(admin)
        )
