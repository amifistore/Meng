#!/usr/bin/env python3
import sys
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def log_error(error_text):
    """Log error to file"""
    with open("error.log", "a", encoding='utf-8') as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_text}\n")

def init_all_databases():
    """Initialize semua database dengan struktur yang benar"""
    print("🔄 Initializing all databases...")
    # Import modules untuk trigger auto-init
    import saldo
    import riwayat
    import topup_db
    # Inisialisasi tabel
    saldo.setup_db()
    riwayat.setup_db()
    topup_db.setup_topup_db()
    print("✅ All databases initialized")

def main():
    print("=" * 60)
    print("🤖 BOT STARTING - FIXED VERSION")
    print("=" * 60)
    try:
        # Load config
        from config import TOKEN, ADMIN_IDS
        print(f"✅ Token loaded: {TOKEN[:10]}...")
        print(f"✅ Admin IDs: {ADMIN_IDS}")

        # Import Telegram modules
        from telegram.ext import (
            Updater, CommandHandler, CallbackQueryHandler,
            MessageHandler, Filters, ConversationHandler
        )

        # Initialize all databases
        init_all_databases()

        # Import handlers (pastikan semua handler sudah ada!)
        from handlers.main_menu_handler import (
            start, cancel, main_menu_callback,
            CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI
        )
        from handlers.produk_pilih_handler import produk_pilih_callback
        from handlers.input_tujuan_handler import input_tujuan_step, handle_konfirmasi
        from handlers.topup_handler import (
            topup_callback, topup_nominal_step, TOPUP_NOMINAL,
            admin_topup_callback, admin_topup_list_callback, admin_topup_detail_callback
        )
        from handlers.riwayat_handler import riwayat_callback, semua_riwayat_callback
        from handlers.stock_handler import stock_akrab_callback
        from handlers.saldo_handler import lihat_saldo_callback, tambah_saldo_callback
        from handlers.admin_produk_handler import (
            admin_edit_produk_callback, admin_edit_harga_prompt,
            admin_edit_deskripsi_prompt, admin_edit_produk_step
        )
        from handlers.produk_daftar_handler import lihat_produk_callback
        from handlers.status_handler import cek_status_callback, input_refid_step, INPUT_REFID

        # Create updater and dispatcher
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        print("✅ Updater created")

        # === Conversation Handlers ===
        order_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(produk_pilih_callback, pattern='^beli_produk$')],
            states={
                CHOOSING_PRODUK: [CallbackQueryHandler(produk_pilih_callback, pattern='^produk_static\\|')],
                INPUT_TUJUAN: [MessageHandler(Filters.text & ~Filters.command, input_tujuan_step)],
                KONFIRMASI: [
                    CallbackQueryHandler(handle_konfirmasi, pattern='^(konfirmasi_order|batal_order|order_konfirmasi|order_batal)$'),
                    MessageHandler(Filters.text & ~Filters.command, handle_konfirmasi)
                ]
            },
            fallbacks=[CommandHandler('batal', cancel)],
            allow_reentry=True,
            name="order_conversation"
        )
        dp.add_handler(order_conv_handler)

        topup_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(topup_callback, pattern='^topup$')],
            states={
                TOPUP_NOMINAL: [MessageHandler(Filters.text & ~Filters.command, topup_nominal_step)],
            },
            fallbacks=[CommandHandler('batal', cancel)],
            allow_reentry=True,
            name="topup_conversation"
        )
        dp.add_handler(topup_conv_handler)

        status_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(cek_status_callback, pattern='^cek_status$')],
            states={
                INPUT_REFID: [MessageHandler(Filters.text & ~Filters.command, input_refid_step)],
            },
            fallbacks=[CommandHandler('batal', cancel)],
            allow_reentry=True,
            name="status_conversation"
        )
        dp.add_handler(status_conv_handler)

        admin_edit_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(admin_edit_harga_prompt, pattern='^editharga\\|'),
                CallbackQueryHandler(admin_edit_deskripsi_prompt, pattern='^editdeskripsi\\|'),
            ],
            states={
                4: [MessageHandler(Filters.text & ~Filters.command, admin_edit_produk_step)],
            },
            fallbacks=[CommandHandler('batal', cancel)],
            allow_reentry=True,
            name="admin_edit_conversation"
        )
        dp.add_handler(admin_edit_conv_handler)

        # === CallbackQuery Handlers ===
        dp.add_handler(CallbackQueryHandler(start, pattern='^start$'))
        dp.add_handler(CallbackQueryHandler(lihat_produk_callback, pattern='^lihat_produk$'))
        dp.add_handler(CallbackQueryHandler(produk_pilih_callback, pattern='^beli_produk$'))
        dp.add_handler(CallbackQueryHandler(riwayat_callback, pattern='^riwayat$'))
        dp.add_handler(CallbackQueryHandler(semua_riwayat_callback, pattern='^semua_riwayat$'))
        dp.add_handler(CallbackQueryHandler(stock_akrab_callback, pattern='^stock_akrab$'))
        dp.add_handler(CallbackQueryHandler(lihat_saldo_callback, pattern='^lihat_saldo$'))
        dp.add_handler(CallbackQueryHandler(tambah_saldo_callback, pattern='^tambah_saldo$'))
        dp.add_handler(CallbackQueryHandler(admin_edit_produk_callback, pattern='^admin_edit_produk\\|'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^manajemen_produk$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^back_main$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^back_admin$'))
        dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern='^topup_approve\\|'))
        dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern='^topup_batal\\|'))
        dp.add_handler(CallbackQueryHandler(admin_topup_list_callback, pattern='^riwayat_topup_admin$'))
        dp.add_handler(CallbackQueryHandler(admin_topup_detail_callback, pattern='^admin_topup_detail\\|'))

        # === Basic Commands ===
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))

        # === Fallback text handler ===
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, start)) # Fallback: balas dengan menu

        def error_handler(update, context):
            err_msg = f"Error: {context.error}"
            logger.error(err_msg)
            log_error(err_msg)
            if update and hasattr(update, 'message') and update.message:
                update.message.reply_text("❌ Error sistem. Silakan hubungi admin.")

        dp.add_error_handler(error_handler)

        print("🔄 Cleaning previous webhook state...")
        try:
            updater.bot.delete_webhook()
            print("✅ Webhook cleaned")
        except Exception:
            print("ℹ️ No webhook to clean")

        print("🔄 Starting polling...")
        updater.start_polling(
            poll_interval=1.0,
            timeout=30,
            drop_pending_updates=True
        )

        print("=" * 60)
        print("✅ BOT STARTED SUCCESSFULLY!")
        print("🤖 Bot is now running...")
        print("📍 Press Ctrl+C to stop")
        print("=" * 60)
        updater.idle()

    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Failed to start: {e}")
        log_error(f"❌ Failed to start: {e}")
        print(f"💡 Error details: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
