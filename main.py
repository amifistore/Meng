import os
import sys
import time
import logging
import subprocess
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

# Setup basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def ensure_single_instance():
    """Ensure only one instance of the bot is running (simplified version)"""
    try:
        # Method 1: Use pgrep to check for running processes
        result = subprocess.run(['pgrep', '-f', 'main.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            current_pid = str(os.getpid())
            for pid in pids:
                if pid and pid != current_pid:
                    print(f"⚠️ Found existing bot process PID {pid}, terminating...")
                    subprocess.run(['kill', '-9', pid])
                    time.sleep(2)
    except Exception as e:
        print(f"⚠️ Error checking processes: {e}")

def stop_existing_bots():
    """Stop any existing bot instances"""
    try:
        subprocess.run(['pkill', '-f', 'main.py'], timeout=5)
        time.sleep(2)
        subprocess.run(['pkill', '-f', 'python.*main.py'], timeout=5)
        time.sleep(2)
    except:
        pass

def main():
    try:
        print("🚀 Initializing bot...")
        
        # Stop existing bots first
        stop_existing_bots()
        time.sleep(3)
        
        # Import config
        from config import TOKEN
        
        # Create updater
        updater = Updater(TOKEN, use_context=True)
        
        # Import handlers
        from handlers.main_menu_handler import start, cancel
        from markup import get_menu
        
        dp = updater.dispatcher
        
        # Basic command handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))
        
        # Add callback handlers
        from handlers.main_menu_handler import main_menu_callback
        from handlers.produk_pilih_handler import produk_pilih_callback
        
        # Main menu handler - catch all patterns
        dp.add_handler(CallbackQueryHandler(main_menu_callback))
        
        # Produk selection handler
        dp.add_handler(CallbackQueryHandler(produk_pilih_callback, pattern='^produk_static\|'))
        
        # Simple error handler
        def error_handler(update, context):
            logger.error(f"Error: {context.error}")
            if update and update.effective_user:
                update.effective_message.reply_text(
                    "❌ Terjadi error. Silakan coba lagi.",
                    reply_markup=get_menu(update.effective_user.id)
                )
        
        dp.add_error_handler(error_handler)
        
        # Start with clean state
        print("🔄 Cleaning previous state...")
        try:
            updater.bot.delete_webhook()
        except:
            pass
        time.sleep(1)
        
        print("🤖 Starting bot polling...")
        updater.start_polling(
            poll_interval=1,
            timeout=20,
            clean=True,
            drop_pending_updates=True
        )
        
        print("✅ Bot is now running!")
        print("📍 Press Ctrl+C to stop")
        
        # Keep running
        updater.idle()
        
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        print(f"❌ Error details: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("🔧 Bot starting...")
    main()
