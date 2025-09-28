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
        # --- Load config & constants ---
        from config import TOKEN
        print(f"✅ Token loaded: {TOKEN[:10]}...")
        from telegram.ext import (
            Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler
        )

        # --- Import all handlers & states from bot_akrab_step_inline.py ---
        from bot_akrab_step_inline import (
            start, main_menu_callback, menu_command, callback_router, handle_text,
            CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, BC_MESSAGE,
            TOPUP_AMOUNT, TOPUP_UPLOAD, ADMIN_CEKUSER, ADMIN_EDIT_HARGA, ADMIN_EDIT_DESKRIPSI, INPUT_KODE_UNIK,
            pilih_produk_callback, input_tujuan_step, konfirmasi_step,
            topup_menu, topup_callback, topup_nominal_step, topup_amount_step,
            topup_upload_router, topup_upload_step,
            admin_topup_callback,
            admin_edit_harga_step, admin_edit_deskripsi_step,
            input_kode_unik_step, admin_generate_kode_step,
            admin_panel, admin_panel_menu,
            admin_produk_menu, admin_produk_detail, admin_edit_harga, admin_edit_deskripsi,
            admin_cekuser_menu, admin_cekuser_detail_callback,
            broadcast_step, bantuan_menu,
            topup_kode_unik_menu, topup_qris_amount,
            my_kode_unik_menu, topup_riwayat_menu,
            admin_topup_pending_menu, admin_topup_detail, admin_topup_action,
            admin_generate_kode, admin_generate_kode_step,
            riwayat_user, semua_riwayat_admin,
            cek_stok_menu, beli_produk_menu
        )

        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        print("✅ Updater created")

        print("🔄 Setting up handlers...")

        # === ConversationHandler ===
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', start),
                CommandHandler('menu', menu_command),
                CallbackQueryHandler(callback_router),
            ],
            states={
                CHOOSING_PRODUK: [CallbackQueryHandler(pilih_produk_callback)],
                INPUT_TUJUAN: [MessageHandler(Filters.text & ~Filters.command, input_tujuan_step)],
                KONFIRMASI: [MessageHandler(Filters.text & ~Filters.command, konfirmasi_step)],
                TOPUP_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, topup_amount_step)],
                TOPUP_UPLOAD: [MessageHandler(Filters.photo, topup_upload_step)],
                BC_MESSAGE: [MessageHandler(Filters.text & ~Filters.command, broadcast_step)],
                ADMIN_CEKUSER: [
                    CallbackQueryHandler(admin_produk_detail, pattern="^admin_produk_detail\\|"),
                    CallbackQueryHandler(admin_edit_harga, pattern="^admin_edit_harga\\|"),
                    CallbackQueryHandler(admin_edit_deskripsi, pattern="^admin_edit_deskripsi\\|"),
                    CallbackQueryHandler(admin_cekuser_detail_callback, pattern="^admin_cekuser_detail\\|")
                ],
                ADMIN_EDIT_HARGA: [MessageHandler(Filters.text & ~Filters.command, admin_edit_harga_step)],
                ADMIN_EDIT_DESKRIPSI: [MessageHandler(Filters.text & ~Filters.command, admin_edit_deskripsi_step)],
                INPUT_KODE_UNIK: [
                    MessageHandler(Filters.text & ~Filters.command, input_kode_unik_step),
                    MessageHandler(Filters.text & ~Filters.command, admin_generate_kode_step)
                ],
            },
            fallbacks=[
                CommandHandler('start', start),
                CommandHandler('menu', menu_command),
                CallbackQueryHandler(main_menu_callback, pattern="^main_menu$")
            ],
            allow_reentry=True,
        )
        dp.add_handler(conv_handler)
        print("✅ ConversationHandler lengkap ditambahkan")

        # === Inline Callback Handler for Top Up Approval ===
        dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern='^topup_approve|'))
        dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern='^topup_batal|'))

        # === Inline Callback Handler for Admin Top Up Panel ===
        dp.add_handler(CallbackQueryHandler(admin_topup_action, pattern="^admin_topup_action\\|"))
        dp.add_handler(CallbackQueryHandler(admin_topup_detail, pattern="^admin_topup_detail\\|"))
        dp.add_handler(CallbackQueryHandler(admin_topup_pending_menu, pattern="^admin_topup_pending$"))

        # === Callback Router Universal ===
        dp.add_handler(CallbackQueryHandler(callback_router))
        print("✅ Callback router universal ditambahkan")

        # === General Text Handler ===
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
        print("✅ General text handler ditambahkan")

        # === Error Handler ===
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
