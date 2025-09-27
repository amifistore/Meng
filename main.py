#!/usr/bin/env python3
import os
import sys
import time
import logging

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("=" * 50)
    print("🔧 BOT STARTING...")
    print("=" * 50)
    
    try:
        # Step 1: Stop any existing bots gently
        print("🔄 Step 1: Checking for existing bots...")
        os.system("pkill -f 'python main.py' 2>/dev/null")
        time.sleep(2)
        
        # Step 2: Import config
        print("🔄 Step 2: Importing config...")
        from config import TOKEN
        print(f"✅ Token loaded: {TOKEN[:10]}...")
        
        # Step 3: Create updater
        print("🔄 Step 3: Creating updater...")
        from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
        
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        print("✅ Updater created")
        
        # Step 4: Import and setup handlers
        print("🔄 Step 4: Setting up handlers...")
        
        # Basic start command
        from handlers.main_menu_handler import start, cancel
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))
        print("✅ Command handlers added")
        
        # Callback handlers
        from handlers.main_menu_handler import main_menu_callback
        from handlers.produk_pilih_handler import produk_pilih_callback
        
        dp.add_handler(CallbackQueryHandler(main_menu_callback))
        dp.add_handler(CallbackQueryHandler(produk_pilih_callback, pattern='^produk_static\|'))
        print("✅ Callback handlers added")
        
        # Step 5: Error handler
        def error_handler(update, context):
            logger.error(f"Error: {context.error}")
        
        dp.add_error_handler(error_handler)
        
        # Step 6: Clean startup
        print("🔄 Step 5: Cleaning previous state...")
        try:
            updater.bot.delete_webhook()
            print("✅ Webhook cleaned")
        except:
            print("ℹ️ No webhook to clean")
        
        time.sleep(1)
        
        # Step 7: Start polling
        print("🔄 Step 6: Starting polling...")
        updater.start_polling(
            poll_interval=1.0,
            timeout=30,
            clean=True,
            drop_pending_updates=True
        )
        
        print("=" * 50)
        print("✅ BOT STARTED SUCCESSFULLY!")
        print("🤖 Bot is now running...")
        print("📍 Press Ctrl+C to stop")
        print("=" * 50)
        
        # Keep running
        updater.idle()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start: {e}")
        print(f"💡 Error details: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
