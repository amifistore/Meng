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

def log_topup_error(error_text):
    with open("topup_error.log", "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_text}\n")

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
        from handlers.topup_handler import topup_callback, topup_nominal_step, TOPUP_NOMINAL
        from handlers.riwayat_handler import riwayat_callback
        from handlers.stock_handler import stock_akrab_callback
        from handlers.saldo_handler import lihat_saldo_callback, tambah_saldo_callback
        from handlers.admin_produk_handler import admin_edit_produk_step
        from handlers.produk_daftar_handler import lihat_produk_callback
        from handlers.status_handler import cek_status_callback, input_refid_step, INPUT_REFID
        # Tambahkan handler lain sesuai kebutuhan menu
        
        print("🔄 Setting up handlers...")
        
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
        
        topup_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(topup_callback, pattern='^topup$')],
            states={
                TOPUP_NOMINAL: [MessageHandler(Filters.text & ~Filters.command, topup_nominal_step)],
            },
            fallbacks=[],
            allow_reentry=True,
            name="topup_conversation"
        )
        dp.add_handler(topup_conv_handler)
        print("✅ Top Up conversation handler added")
        
        status_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(cek_status_callback, pattern='^cek_status$')],
            states={
                INPUT_REFID: [MessageHandler(Filters.text & ~Filters.command, input_refid_step)],
            },
            fallbacks=[],
            allow_reentry=True,
            name="status_conversation"
        )
        dp.add_handler(status_conv_handler)
        print("✅ Status conversation handler added")
        
        dp.add_handler(CallbackQueryHandler(start, pattern='^start$'))
        dp.add_handler(CallbackQueryHandler(lihat_produk_callback, pattern='^lihat_produk$'))
        dp.add_handler(CallbackQueryHandler(riwayat_callback, pattern='^riwayat$'))
        dp.add_handler(CallbackQueryHandler(stock_akrab_callback, pattern='^stock_akrab$'))
        dp.add_handler(CallbackQueryHandler(lihat_saldo_callback, pattern='^lihat_saldo$'))
        dp.add_handler(CallbackQueryHandler(tambah_saldo_callback, pattern='^tambah_saldo$'))
        dp.add_handler(CallbackQueryHandler(admin_edit_produk_step, pattern='^manajemen_produk$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback))
        
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))
        print("✅ Command handlers added")
        
        def error_handler(update, context):
            err_msg = f"Error: {context.error}"
            logger.error(err_msg)
            log_topup_error(err_msg)
        
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
        log_topup_error(f"❌ Failed to start: {e}")
        print(f"💡 Error details: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
