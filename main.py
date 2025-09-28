#!/usr/bin/env python3
import os
import sys
import time
import logging

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
        from config import TOKEN
        print(f"✅ Token loaded: {TOKEN[:10]}...")
        
        from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler
        
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        print("✅ Updater created")
        
        # Import handlers
        from handlers.main_menu_handler import start, cancel, main_menu_callback, CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI
        from handlers.produk_pilih_handler import produk_pilih_callback
        from handlers.order_handler import handle_input_tujuan, handle_konfirmasi
        from handlers.topup_handler import topup_callback
        from handlers.riwayat_handler import riwayat_callback
        from handlers.stock_handler import stock_akrab_callback
        from handlers.saldo_handler import lihat_saldo_callback, tambah_saldo_callback
        from handlers.admin_produk_handler import admin_edit_produk_step
        from handlers.produk_daftar_handler import lihat_produk_callback
        from handlers.status_handler import cek_status_callback
        # Tambahkan handler lain sesuai kebutuhan menu
        
        print("🔄 Setting up handlers...")
        
        # Conversation Handler untuk order produk
        order_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(produk_pilih_callback, pattern='^produk_static\\|')],
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
        
        # Handler untuk menu utama sesuai callback
        dp.add_handler(CallbackQueryHandler(start, pattern='^start$'))
        dp.add_handler(CallbackQueryHandler(lihat_produk_callback, pattern='^lihat_produk$'))
        dp.add_handler(CallbackQueryHandler(topup_callback, pattern='^topup$'))
        dp.add_handler(CallbackQueryHandler(riwayat_callback, pattern='^riwayat$'))
        dp.add_handler(CallbackQueryHandler(stock_akrab_callback, pattern='^stock_akrab$'))
        dp.add_handler(CallbackQueryHandler(cek_status_callback, pattern='^cek_status$'))
        dp.add_handler(CallbackQueryHandler(lihat_saldo_callback, pattern='^lihat_saldo$'))
        dp.add_handler(CallbackQueryHandler(tambah_saldo_callback, pattern='^tambah_saldo$'))
        dp.add_handler(CallbackQueryHandler(admin_edit_produk_step, pattern='^manajemen_produk$'))
        # Admin fitur lain, misal semua_riwayat, dsb...
        
        # Handler fallback untuk callback yang tidak dikenali
        dp.add_handler(CallbackQueryHandler(main_menu_callback))
        
        # Command handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))
        print("✅ Command handlers added")
        
        def error_handler(update, context):
            logger.error(f"Error: {context.error}")
        
        dp.add_error_handler(error_handler)
        
        print("🔄 Cleaning previous state...")
        try:
            updater.bot.delete_webhook()
            print("✅ Webhook cleaned")
        except Exception:
            print("ℹ️ No webhook to clean")
        
        time.sleep(1)
        
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
