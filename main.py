#!/usr/bin/env python3
import sys
import time
import logging

from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
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

# ✅ IMPORT HANDLER BARU
from handlers.callback_handler import handle_all_callbacks

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
        # ✅ GUNAKAN Application BUKAN Updater (untuk versi terbaru)
        application = Application.builder().token(TOKEN).build()

        # ✅ 1. TAMBAHKAN GLOBAL CALLBACK HANDLER PERTAMA - INI YANG PENTING!
        application.add_handler(CallbackQueryHandler(handle_all_callbacks))

        # ✅ 2. CONVERSATION HANDLER
        order_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^(🛒 Order Produk)$"), lihat_produk_callback)],
            states={
                CHOOSING_PRODUK: [
                    CallbackQueryHandler(produk_pilih_callback, pattern="^produk_static\\|"),
                    CallbackQueryHandler(produk_pilih_callback, pattern="^back_main$")
                ],
                INPUT_TUJUAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input_tujuan)],
                KONFIRMASI: [
                    CallbackQueryHandler(handle_konfirmasi, pattern="^(order_konfirmasi|order_batal)$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_konfirmasi)
                ]
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            allow_reentry=True,
        )
        application.add_handler(order_conv_handler)

        # ✅ 3. HANDLER LAINNYA
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", start))
        application.add_handler(CommandHandler("menu", start))
        application.add_handler(CommandHandler("cancel", cancel))
        application.add_handler(CommandHandler("batal", cancel))
        application.add_handler(MessageHandler(filters.Regex("^(📦 Cek Stok)$"), stock_akrab_callback))
        application.add_handler(MessageHandler(filters.Regex("^(💳 Top Up Saldo)$"), topup_callback))
        application.add_handler(MessageHandler(filters.Regex("^(📋 Riwayat Transaksi)$"), riwayat_callback))
        application.add_handler(MessageHandler(filters.Regex("^(💰 Lihat Saldo)$"), lihat_saldo_callback))
        application.add_handler(MessageHandler(filters.Regex("^(🔍 Cek Status)$"), cek_status_callback))
        application.add_handler(MessageHandler(filters.Regex("^(❓ Bantuan)$"), start))

        # Fallback handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_menu_handler))

        # Error handler
        async def error_handler(update, context):
            try:
                error_msg = f"Error: {context.error}"
                logger.error(error_msg)
                log_error(error_msg)
                if update.effective_message:
                    is_admin = update.effective_user and update.effective_user.id in ADMIN_IDS
                    await update.effective_message.reply_text(
                        "❌ Maaf, terjadi kesalahan sistem. Silakan coba lagi.",
                        reply_markup=reply_main_menu(is_admin=is_admin)
                    )
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
        application.add_error_handler(error_handler)

        print("🔄 Memulai polling...")
        application.run_polling(
            poll_interval=1.0,
            timeout=30,
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        
    except Exception as e:
        logger.error(f"❌ Gagal menjalankan: {e}")
        log_error(f"❌ Gagal menjalankan: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
