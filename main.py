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

def get_current_pid():
    """Get current process PID"""
    return os.getpid()

def stop_other_bots():
    """Stop other bot instances without killing ourselves"""
    current_pid = get_current_pid()
    print(f"🔍 Current PID: {current_pid}")
    
    try:
        # Find other Python processes running main.py
        import subprocess
        result = subprocess.run(['pgrep', '-f', 'python.*main.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid and pid.strip() and int(pid.strip()) != current_pid:
                    print(f"🛑 Stopping other bot PID: {pid}")
                    subprocess.run(['kill', pid.strip()])
                    time.sleep(1)
        else:
            print("✅ No other bots running")
            
    except Exception as e:
        print(f"⚠️ Error checking processes: {e}")

def main():
    print("=" * 50)
    print("🔧 BOT STARTING...")
    print("=" * 50)
    
    try:
        # Step 1: Stop OTHER bots only (not ourselves)
        print("🔄 Step 1: Stopping other bot instances...")
        stop_other_bots()
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
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
