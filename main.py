import os
import sys
import time
import logging
import subprocess
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler
from config import TOKEN

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

def stop_existing_bots():
    """Stop any existing bot instances"""
    try:
        # Kill existing Python processes running main.py
        subprocess.run(['pkill', '-f', 'main.py'], timeout=5)
        time.sleep(2)
        subprocess.run(['pkill', '-f', 'python.*main'], timeout=5) 
        time.sleep(2)
        print("✅ Existing bots stopped")
    except Exception as e:
        print(f"ℹ️ No existing bots to stop: {e}")

def main():
    try:
        print("🚀 Starting bot initialization...")
        
        # Stop existing bots first
        stop_existing_bots()
        time.sleep(3)
        
        # Import config
        from config import TOKEN
        
        # Create updater
        updater = Updater(
            TOKEN, 
            use_context=True,
            request_kwargs={
                'read_timeout': 30,
                'connect_timeout': 30
            }
        )
        dp = updater.dispatcher
        
        print("✅ Updater created")
        
        # Import handlers
        from handlers.main_menu_handler import start, cancel, main_menu_callback, CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, TOPUP_NOMINAL, ADMIN_EDIT
        from handlers.produk_pilih_handler import produk_pilih_callback
        from handlers.order_handler import handle_input_tujuan, handle_konfirmasi
        from markup import get_menu
        
        print("✅ Handlers imported")
        
        # ===== HANDLER SETUP =====
        
        # 1. Command handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))
        
        # 2. Main menu callback handler (catch-all for main menu)
        main_handler = CallbackQueryHandler(main_menu_callback)
        dp.add_handler(main_handler)
        
        # 3. Produk selection handler (specific pattern)
        produk_handler = CallbackQueryHandler(
            produk_pilih_callback, 
            pattern=r'^produk_static\|'
        )
        dp.add_handler(produk_handler)
        
        # 4. Conversation handler for order process
        order_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(produk_pilih_callback, pattern='^produk_static\|')],
            states={
                INPUT_TUJUAN: [
                    MessageHandler(Filters.text & ~Filters.command, handle_input_tujuan)
                ],
                KONFIRMASI: [
                    MessageHandler(Filters.text & ~Filters.command, handle_konfirmasi)
                ]
            },
            fallbacks=[
                CommandHandler('cancel', cancel),
                CommandHandler('batal', cancel)
            ],
            allow_reentry=True
        )
        dp.add_handler(order_conv_handler)
        
        print("✅ All handlers added")
        
        # ===== ERROR HANDLER =====
        def error_handler(update, context):
            logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
            
            if update and update.effective_user:
                try:
                    update.effective_message.reply_text(
                        "❌ Terjadi error sistem. Silakan coba lagi atau gunakan /start.",
                        reply_markup=get_menu(update.effective_user.id)
                    )
                except Exception as e:
                    logger.error(f"Error sending error message: {e}")
        
        dp.add_error_handler(error_handler)
        
        # ===== BOT STARTUP =====
        print("🔄 Cleaning previous state...")
        try:
            updater.bot.delete_webhook()
            print("✅ Webhook deleted")
        except Exception as e:
            print(f"ℹ️ No webhook to delete: {e}")
        
        time.sleep(1)
        
        print("🤖 Starting bot polling...")
        updater.start_polling(
            poll_interval=0.5,
            timeout=20,
            clean=True,
            drop_pending_updates=True
        )
        
        print("=" * 50)
        print("✅ BOT STARTED SUCCESSFULLY!")
        print("🤖 Bot is now running and ready")
        print("📍 Press Ctrl+C to stop the bot")
        print("=" * 50)
        
        # Keep the bot running
        updater.idle()
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install python-telegram-bot requests")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"❌ Critical error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("🔧 Bot starting...")
    main()
