#!/usr/bin/env python3
import sys
import time
import logging

from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
)

from config import TOKEN, ADMIN_IDS
from markup import reply_main_menu
from handlers.main_menu_handler import start, cancel, reply_menu_handler
from handlers.produk_daftar_handler import lihat_produk_callback
from handlers.produk_pilih_handler import produk_pilih_callback, CHOOSING_PRODUK, INPUT_TUJUAN
from handlers.input_tujuan_handler import handle_input_tujuan, KONFIRMASI
from handlers.order_handler import handle_konfirmasi
from handlers.stock_handler import stock_akrab_callback
from handlers.topup_handler import topup_callback
from handlers.riwayat_handler import riwayat_callback
from handlers.saldo_handler import lihat_saldo_callback
from handlers.status_handler import cek_status_callback
from handlers.admin_panel_handler import admin_panel_callback  # contoh handler admin

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def log_error(error_text):
    with open("error.log", "a", encoding='utf-8') as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_text}\n")

def main():
    print("=" * 60)
    print("🤖 BOT STARTING - FULL FEATURE VERSION")
    print("=" * 60)
    try:
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher

        # ConversationHandler untuk order produk
        order_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(Filters.regex("^(🛒 Order Produk)$"), lihat_produk_callback)],
            states={
                CHOOSING_PRODUK: [
                    CallbackQueryHandler(produk_pilih_callback, pattern="^produk_static\\|"),
                    CallbackQueryHandler(produk_pilih_callback, pattern="^back_main$")
                ],
                INPUT_TUJUAN: [MessageHandler(Filters.text & ~Filters.command, handle_input_tujuan)],
                KONFIRMASI: [
                    CallbackQueryHandler(handle_konfirmasi, pattern="^(order_konfirmasi|order_batal)$"),
                    MessageHandler(Filters.text & ~Filters.command, handle_konfirmasi)
                ]
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            allow_reentry=True,
        )
        dp.add_handler(order_conv_handler)

        # Handler untuk menu lain
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", start))
        dp.add_handler(CommandHandler("menu", start))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))
        dp.add_handler(MessageHandler(Filters.regex("^(📦 Cek Stok)$"), stock_akrab_callback))
        dp.add_handler(MessageHandler(Filters.regex("^(💳 Top Up Saldo)$"), topup_callback))
        dp.add_handler(MessageHandler(Filters.regex("^(📋 Riwayat Transaksi)$"), riwayat_callback))
        dp.add_handler(MessageHandler(Filters.regex("^(💰 Lihat Saldo)$"), lihat_saldo_callback))
        dp.add_handler(MessageHandler(Filters.regex("^(🔍 Cek Status)$"), cek_status_callback))
        dp.add_handler(MessageHandler(Filters.regex("^(🛠 Admin Panel)$"), admin_panel_callback))  # menu admin

        # Fallback ke reply_menu_handler untuk semua menu
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reply_menu_handler))

        # Error handler
        def error_handler(update, context):
            try:
                error_msg = f"Error: {context.error}"
                logger.error(error_msg)
                log_error(error_msg)
                # Cek admin untuk reply_main_menu
                is_admin = update.effective_user and update.effective_user.id in ADMIN_IDS
                update.effective_message.reply_text(
                    "❌ Maaf, terjadi kesalahan sistem. Silakan coba lagi.",
                    reply_markup=reply_main_menu(is_admin=is_admin)
                )
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
        dp.add_error_handler(error_handler)

        updater.bot.delete_webhook()
        time.sleep(1)
        print("🔄 Memulai polling...")
        updater.start_polling(
            poll_interval=1.0,
            timeout=30,
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        print("=" * 60)
        print("🎉 BOT BERHASIL DIJALANKAN!")
        print("=" * 60)
        updater.idle()
    except Exception as e:
        logger.error(f"❌ Gagal menjalankan: {e}")
        log_error(f"❌ Gagal menjalankan: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
