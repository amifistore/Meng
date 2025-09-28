#!/usr/bin/env python3
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
        from telegram.ext import (
            Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler
        )

        # === Import all handlers and states from handlers/ ===
        from handlers.main_menu_handler import (
            start, cancel, main_menu_callback,
            CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI
        )
        from handlers.produk_pilih_handler import produk_pilih_callback
        from handlers.order_handler import input_tujuan_step, handle_konfirmasi
        from handlers.topup_handler import (
            topup_callback, topup_nominal_step, TOPUP_NOMINAL, admin_topup_callback,
            admin_topup_list_callback, admin_topup_detail_callback
        )
        from handlers.riwayat_handler import riwayat_callback
        from handlers.stock_handler import stock_akrab_callback
        from handlers.saldo_handler import lihat_saldo_callback, tambah_saldo_callback
        from handlers.admin_produk_handler import (
            admin_edit_produk_callback,
            admin_edit_harga_prompt,
            admin_edit_deskripsi_prompt,
            admin_edit_produk_step
        )
        from handlers.produk_daftar_handler import lihat_produk_callback
        from handlers.status_handler import cek_status_callback, input_refid_step, INPUT_REFID

        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        print("✅ Updater created")

        print("🔄 Setting up handlers...")

        # === Order Produk Conversation ===
        order_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(produk_pilih_callback, pattern='^beli_produk$')],
            states={
                CHOOSING_PRODUK: [CallbackQueryHandler(produk_pilih_callback, pattern='^produk_static\\|')],
                INPUT_TUJUAN: [MessageHandler(Filters.text & ~Filters.command, input_tujuan_step)],
                KONFIRMASI: [
                    CallbackQueryHandler(handle_konfirmasi, pattern='^(konfirmasi_order|batal_order)$'),
                    MessageHandler(Filters.text & ~Filters.command, handle_konfirmasi)
                ]
            },
            fallbacks=[CommandHandler('batal', cancel)],
            allow_reentry=True,
            name="order_conversation"
        )
        dp.add_handler(order_conv_handler)

        # === Top Up Conversation ===
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

        # === Status Cek Conversation ===
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

        # === Admin Edit Produk Conversation ===
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

        # === CallbackQuery Handlers for ALL Menu ===
        dp.add_handler(CallbackQueryHandler(start, pattern='^start$'))
        dp.add_handler(CallbackQueryHandler(lihat_produk_callback, pattern='^lihat_produk$'))
        dp.add_handler(CallbackQueryHandler(produk_pilih_callback, pattern='^beli_produk$'))
        dp.add_handler(CallbackQueryHandler(riwayat_callback, pattern='^riwayat$'))
        dp.add_handler(CallbackQueryHandler(stock_akrab_callback, pattern='^stock_akrab$'))
        dp.add_handler(CallbackQueryHandler(lihat_saldo_callback, pattern='^lihat_saldo$'))
        dp.add_handler(CallbackQueryHandler(tambah_saldo_callback, pattern='^tambah_saldo$'))
        dp.add_handler(CallbackQueryHandler(admin_edit_produk_callback, pattern='^admin_edit_produk\\|'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^manajemen_produk$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^back_main$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^back_admin$'))

        # === Handler Approve/Batal Topup Admin ===
        dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern='^topup_approve|'))
        dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern='^topup_batal|'))

        # === Handler Riwayat Top Up User (Admin) ===
        dp.add_handler(CallbackQueryHandler(admin_topup_list_callback, pattern='^riwayat_topup_admin$'))
        dp.add_handler(CallbackQueryHandler(admin_topup_detail_callback, pattern='^admin_topup_detail\\|'))

        # === Fallback text handler (default reply) ===
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, start)) # Fallback: balas dengan menu

        # === Command Handlers ===
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))

        # === Error logging handler ===
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
