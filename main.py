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
from handlers.topup_handler import topup_callback, topup_nominal_step, TOPUP_NOMINAL, admin_topup_callback, admin_topup_list_callback, admin_topup_detail_callback
from handlers.riwayat_handler import riwayat_callback, semua_riwayat_callback
from handlers.saldo_handler import lihat_saldo_callback
from handlers.status_handler import cek_status_callback
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

async def error_handler(update, context):
    try:
        error_msg = f"Error: {context.error}"
        logger.error(error_msg)
        log_error(error_msg)
        if update and update.effective_message:
            is_admin = update.effective_user and update.effective_user.id in ADMIN_IDS
            await update.effective_message.reply_text(
                "❌ Maaf, terjadi kesalahan sistem. Silakan coba lagi.",
                reply_markup=reply_main_menu(is_admin=is_admin)
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

def main():
    print("=" * 60)
    print("🤖 BOT STARTING - MODERN ASYNC VERSION")
    print("=" * 60)
    
    try:
        # GUNAKAN Application BUKAN Updater
        application = Application.builder().token(TOKEN).build()

        application.add_handler(CallbackQueryHandler(handle_all_callbacks))

        # CONVERSATION HANDLER DENGAN ASYNC
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

        topup_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^(💳 Top Up Saldo)$"), topup_callback)],
            states={TOPUP_NOMINAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, topup_nominal_step)]},
            fallbacks=[CommandHandler('cancel', cancel)],
            allow_reentry=True,
        )
        application.add_handler(topup_conv_handler)

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", start))
        application.add_handler(CommandHandler("menu", start))
        application.add_handler(CommandHandler("cancel", cancel))
        application.add_handler(CommandHandler("batal", cancel))

        application.add_handler(MessageHandler(filters.Regex("^(📦 Cek Stok)$"), stock_akrab_callback))
        application.add_handler(MessageHandler(filters.Regex("^(📋 Riwayat Transaksi)$"), riwayat_callback))
        application.add_handler(MessageHandler(filters.Regex("^(💰 Lihat Saldo)$"), lihat_saldo_callback))
        application.add_handler(MessageHandler(filters.Regex("^(🔍 Cek Status)$"), cek_status_callback))
        application.add_handler(MessageHandler(filters.Regex("^(❓ Bantuan)$"), start))

        application.add_handler(CallbackQueryHandler(admin_topup_callback, pattern="^topup_(approve|batal)\\|"))
        application.add_handler(CallbackQueryHandler(admin_topup_list_callback, pattern="^riwayat_topup_admin$"))
        application.add_handler(CallbackQueryHandler(admin_topup_detail_callback, pattern="^admin_topup_detail\\|"))
        application.add_handler(CallbackQueryHandler(semua_riwayat_callback, pattern="^semua_riwayat$"))

        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_menu_handler))

        application.add_error_handler(error_handler)
        
        print("🔄 Memulai polling...")
        print("✅ Semua handler terpasang (Async Version)")
        
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Gagal menjalankan bot: {e}")
        log_error(f"❌ Gagal menjalankan bot: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
