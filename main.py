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
        
        # **FIXED: Direct imports tanpa melalui __init__.py**
        from handlers.main_menu_handler import start, cancel, main_menu_callback, CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, TOPUP_NOMINAL, ADMIN_EDIT
        from handlers.produk_pilih_handler import produk_pilih_callback
        from handlers.order_handler import handle_input_tujuan, handle_konfirmasi
        
        print("🔄 Setting up handlers...")
        
        # GROUP 0: Specific pattern handlers (HIGHEST PRIORITY)
        produk_handler = CallbackQueryHandler(
            produk_pilih_callback, 
            pattern=r'^produk_static\|'
        )
        dp.add_handler(produk_handler, group=0)
        print("✅ Produk handler added (group 0)")
        
        # GROUP 1: Main menu handlers
        def main_menu_filter(update):
            """Filter untuk hanya menangani callback menu utama"""
            query = update.callback_query
            if not query:
                return False
                
            data = query.data
            # Hanya handle callback yang berupa menu utama
            menu_patterns = [
                'lihat_produk', 'beli_produk', 'topup', 'cek_status', 'riwayat', 'stock_akrab',
                'semua_riwayat', 'lihat_saldo', 'tambah_saldo', 'manajemen_produk',
                'admin_edit_produk', 'editharga', 'editdeskripsi', 'resetcustom',
                'back_main', 'back_admin'
            ]
            
            is_menu = any(data == pattern or data.startswith(pattern + '|') for pattern in menu_patterns)
            print(f"🔍 [FILTER] Data: '{data}', Is menu: {is_menu}")
            return is_menu
        
        main_handler = CallbackQueryHandler(main_menu_callback, pattern=main_menu_filter)
        dp.add_handler(main_handler, group=1)
        print("✅ Main menu handler added (group 1)")
        
        # GROUP 2: Fallback handler
        def fallback_callback(update, context):
            query = update.callback_query
            user = query.from_user
            data = query.data
            
            print(f"🔍 [FALLBACK] Unhandled callback: '{data}'")
            
            try:
                query.answer()
            except:
                pass
                
            from markup import get_menu
            query.edit_message_text(
                f"❌ Menu tidak dikenali: `{data}`\n\nSilakan gunakan /start untuk memulai ulang.",
                parse_mode="HTML",
                reply_markup=get_menu(user.id)
            )
        
        fallback_handler = CallbackQueryHandler(fallback_callback)
        dp.add_handler(fallback_handler, group=2)
        print("✅ Fallback handler added (group 2)")
        
        # Conversation handler for order process
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
        
        # Command handlers
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
