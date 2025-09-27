import os
import sys
import time
import logging
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

# Setup basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def ensure_single_instance():
    """Ensure only one instance of the bot is running"""
    import psutil
    current_pid = os.getpid()
    current_script = os.path.abspath(__file__)
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if (proc.info['pid'] != current_pid and 
                proc.info['cmdline'] and 
                'main.py' in ' '.join(proc.info['cmdline'])):
                print(f"⚠️ Found existing bot process PID {proc.info['pid']}, terminating it...")
                proc.terminate()
                proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            pass

def main():
    try:
        # Ensure single instance
        ensure_single_instance()
        time.sleep(2)
        
        print("🚀 Initializing bot...")
        
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
        
        # Simple error handler
        def error_handler(update, context):
            logger.error(f"Error: {context.error}")
        
        dp.add_error_handler(error_handler)
        
        # Start with clean state
        print("🔄 Cleaning previous state...")
        updater.bot.delete_webhook()
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
        sys.exit(1)

if __name__ == '__main__':
    print("🔧 Bot starting...")
    main()
