import logging
import sys
import re
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler
from config import TOKEN

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,  # Changed to DEBUG for more info
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

def stop_bot():
    import os
    os.system("pkill -f 'python main.py'")
    os.system("pkill -f 'python3 main.py'")

def main():
    try:
        stop_bot()
        import time
        time.sleep(2)
        
        print("🚀 Starting bot with DEBUG mode...")
        
        updater = Updater(
            TOKEN, 
            use_context=True,
            request_kwargs={
                'read_timeout': 30, 
                'connect_timeout': 30,
            }
        )
        
        # Import handlers
        from markup import get_menu
        from handlers.main_menu_handler import main_menu_callback, start, cancel, CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, TOPUP_NOMINAL, ADMIN_EDIT
        from handlers.produk_pilih_handler import produk_pilih_callback
        from handlers.order_handler import handle_input_tujuan, handle_konfirmasi
        from debug_handler import debug_callback
        
        dp = updater.dispatcher
        
        try:
            updater.bot.delete_webhook()
            print("✅ Webhook deleted")
        except Exception as e:
            print(f"ℹ️ No webhook to delete: {e}")
        
        # **FIXED: SINGLE CATCH-ALL HANDLER FIRST**
        debug_handler = CallbackQueryHandler(debug_callback, pattern='.*')
        
        # **FIXED: SIMPLIFIED PATTERN MATCHING**
        produk_handler = CallbackQueryHandler(
            produk_pilih_callback, 
            pattern=r'^produk_static\|'
        )
        
        main_handler = CallbackQueryHandler(
            main_menu_callback,
            pattern=r'^(lihat_produk|beli_produk|topup|cek_status|riwayat|stock_akrab|semua_riwayat|lihat_saldo|tambah_saldo|manajemen_produk|admin_edit_produk\||editharga\||editdeskripsi\||resetcustom\||back_main|back_admin)$'
        )
        
        # **PRIORITY: Debug handler dulu, lalu specific handlers**
        dp.add_handler(debug_handler, group=0)
        dp.add_handler(produk_handler, group=1)
        dp.add_handler(main_handler, group=1)
        
        # Command handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("debug", lambda u,c: debug_callback(u,c)))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))
        
        # Conversation handler
        order_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(produk_pilih_callback, pattern='^produk_static\|')],
            states={
                INPUT_TUJUAN: [MessageHandler(Filters.text & ~Filters.command, handle_input_tujuan)],
                KONFIRMASI: [MessageHandler(Filters.text & ~Filters.command, handle_konfirmasi)]
            },
            fallbacks=[CommandHandler('batal', cancel)],
            allow_reentry=True
        )
        dp.add_handler(order_conv_handler)
        
        def error_handler(update, context):
            logger.error(f"Error: {context.error}", exc_info=context.error)
            if update and update.effective_user:
                update.effective_message.reply_text(
                    "❌ Terjadi error sistem. Silakan coba lagi.",
                    reply_markup=get_menu(update.effective_user.id)
                )
        
        dp.add_error_handler(error_handler)
        
        # Start polling
        print("✅ Starting polling...")
        updater.start_polling(
            poll_interval=0.5,
            timeout=20,
            clean=True,
            drop_pending_updates=True
        )
        
        print("🤖 Bot successfully started in DEBUG mode!")
        print("📍 Press Ctrl+C to stop the bot")
        
        updater.idle()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
