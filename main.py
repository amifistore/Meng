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
        # Import config
        from config import TOKEN
        print(f"✅ Token loaded: {TOKEN[:10]}...")
        
        # Create updater
        from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler
        
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        print("✅ Updater created")
        
        # Import handlers
        from handlers.main_menu_handler import start, cancel, main_menu_callback, CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI
        from handlers.produk_pilih_handler import produk_pilih_callback
        from handlers.order_handler import handle_input_tujuan, handle_konfirmasi
        
        print("🔄 Setting up handlers...")
        
        # **FIXED: Use ConversationHandler as entry point for produk selection**
        
        # 1. Conversation Handler for PRODUCT ORDER (HIGHEST PRIORITY)
        order_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(produk_pilih_callback, pattern='^produk_static\|')],
            states={
                INPUT_TUJUAN: [MessageHandler(Filters.text & ~Filters.command, handle_input_tujuan)],
                KONFIRMASI: [MessageHandler(Filters.text & ~Filters.command, handle_konfirmasi)]
            },
            fallbacks=[CommandHandler('batal', cancel)],
            allow_reentry=True,
            name="order_conversation"
        )
        dp.add_handler(order_conv_handler)
        print("✅ Order conversation handler added")
        
        # 2. Main menu handler for other callbacks
        main_handler = CallbackQueryHandler(main_menu_callback)
        dp.add_handler(main_handler)
        print("✅ Main menu handler added")
        
        # 3. Command handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))
        print("✅ Command handlers added")
        
        # Error handler
        def error_handler(update, context):
            logger.error(f"Error: {context.error}")
        
        dp.add_error_handler(error_handler)
        
        # Clean startup
        print("🔄 Cleaning previous state...")
        try:
            updater.bot.delete_webhook()
            print("✅ Webhook cleaned")
        except:
            print("ℹ️ No webhook to clean")
        
        time.sleep(1)
        
        # Start polling
        print("🔄 Starting polling...")
        updater.start_polling(
            poll_interval=1.0,
            timeout=30,
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
