#!/usr/bin/env python3
import sys
import time
import logging
import sqlite3
import os
import shutil

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from markup import main_menu_markup, reply_main_menu

def log_error(error_text):
    with open("error.log", "a", encoding='utf-8') as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_text}\n")

def init_all_databases():
    print("🔄 Inisialisasi semua database...")
    try:
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(".pyc"):
                    os.remove(os.path.join(root, file))
            for dir in dirs:
                if dir == "__pycache__":
                    shutil.rmtree(os.path.join(root, dir), ignore_errors=True)
        import saldo
        import riwayat
        import topup
        saldo.init_db_saldo()
        riwayat.init_db_riwayat()
        topup.init_db_topup()
        print("✅ Semua database berhasil diinisialisasi")
        return True
    except Exception as e:
        logger.error(f"❌ Gagal inisialisasi database: {e}")
        return False

def setup_test_data():
    try:
        from saldo import tambah_saldo_user, get_saldo_user
        TEST_USER_ID = 123456789  # <-- GANTI KE ID TELEGRAM ANDA
        saldo_user = get_saldo_user(TEST_USER_ID)
        if saldo_user == 0:
            success = tambah_saldo_user(TEST_USER_ID, 100000, "initial", "Saldo awal testing")
            if success:
                print(f"✅ Saldo 100.000 ditambahkan ke user {TEST_USER_ID}")
            else:
                print(f"❌ Gagal tambah saldo ke user {TEST_USER_ID}")
        else:
            print(f"✅ User {TEST_USER_ID} sudah ada dengan saldo: {saldo_user:,}")
    except Exception as e:
        print(f"⚠️ Setup test data: {e}")

def check_handler_files():
    print("🔍 Cek file handler...")
    required_handlers = [
        'main_menu_handler.py',
        'produk_pilih_handler.py',
        'produk_daftar_handler.py',
        'input_tujuan_handler.py',
        'konfirmasi_handler.py',
        'riwayat_handler.py',
        'saldo_handler.py',
        'status_handler.py',
        'stock_handler.py',
        'topup_handler.py'
    ]
    handlers_dir = "handlers"
    for handler in required_handlers:
        handler_path = os.path.join(handlers_dir, handler)
        if not os.path.exists(handler_path):
            print(f"   ❌ {handler} - TIDAK ADA")
    print("✅ Handler file check selesai")

def main():
    print("=" * 60)
    print("🤖 BOT STARTING - FULL FEATURE VERSION")
    print("=" * 60)
    try:
        from config import TOKEN, ADMIN_IDS
        print(f"✅ Token loaded: {TOKEN[:10]}...")
        print(f"✅ Admin IDs: {ADMIN_IDS}")
        from telegram.ext import (
            Updater, CommandHandler, CallbackQueryHandler,
            MessageHandler, Filters, ConversationHandler
        )
        if not init_all_databases():
            print("❌ Inisialisasi database gagal")
            return
        check_handler_files()
        setup_test_data()
        print("🔄 Load semua handler...")

        # Import all handlers
        from handlers.main_menu_handler import (
            start, cancel, main_menu_callback, reply_menu_handler,
            CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI
        )
        from handlers.produk_pilih_handler import produk_pilih_callback
        from handlers.produk_daftar_handler import lihat_produk_callback
        from handlers.input_tujuan_handler import input_tujuan_step
        from handlers.konfirmasi_handler import handle_konfirmasi
        from handlers.topup_handler import topup_callback, topup_nominal_step
        from handlers.riwayat_handler import riwayat_callback, semua_riwayat_callback
        from handlers.stock_handler import stock_akrab_callback
        from handlers.saldo_handler import lihat_saldo_callback, tambah_saldo_callback
        from handlers.status_handler import cek_status_callback, input_refid_step, INPUT_REFID

        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher

        # ConversationHandler untuk order produk
        order_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(produk_pilih_callback, pattern='^beli_produk$'),
                CommandHandler('order', start)
            ],
            states={
                CHOOSING_PRODUK: [
                    CallbackQueryHandler(produk_pilih_callback, pattern='^produk_static\\|'),
                    CallbackQueryHandler(produk_pilih_callback, pattern='^produk\\|')
                ],
                INPUT_TUJUAN: [
                    MessageHandler(Filters.text & ~Filters.command, input_tujuan_step)
                ],
                KONFIRMASI: [
                    CallbackQueryHandler(handle_konfirmasi, pattern='^(konfirmasi_order|batal_order|order_konfirmasi|order_batal)$'),
                    MessageHandler(Filters.text & ~Filters.command, handle_konfirmasi)
                ]
            },
            fallbacks=[
                CommandHandler('cancel', cancel),
                CommandHandler('batal', cancel),
                CommandHandler('start', start)
            ],
            allow_reentry=True,
            name="order_conversation"
        )
        dp.add_handler(order_conv_handler)

        # ConversationHandler untuk topup (jika perlu)
        topup_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(topup_callback, pattern='^topup$'),
                CommandHandler('topup', start)
            ],
            states={
                # Tambah state lain jika ada
            },
            fallbacks=[
                CommandHandler('cancel', cancel),
                CommandHandler('batal', cancel),
                CommandHandler('start', start)
            ],
            allow_reentry=True,
            name="topup_conversation"
        )
        dp.add_handler(topup_conv_handler)

        # ConversationHandler untuk cek status
        status_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(cek_status_callback, pattern='^cek_status$'),
                CommandHandler('status', start)
            ],
            states={
                INPUT_REFID: [
                    MessageHandler(Filters.text & ~Filters.command, input_refid_step)
                ],
            },
            fallbacks=[
                CommandHandler('cancel', cancel),
                CommandHandler('batal', cancel),
                CommandHandler('start', start)
            ],
            allow_reentry=True,
            name="status_conversation"
        )
        dp.add_handler(status_conv_handler)

        # Callback menu utama dan semua fitur
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^main_menu$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^back_main$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^back_admin$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^back_menu$'))
        dp.add_handler(CallbackQueryHandler(lihat_produk_callback, pattern='^lihat_produk$'))
        dp.add_handler(CallbackQueryHandler(produk_pilih_callback, pattern='^beli_produk$'))
        dp.add_handler(CallbackQueryHandler(produk_pilih_callback, pattern='^produk_static\\|'))
        dp.add_handler(CallbackQueryHandler(produk_pilih_callback, pattern='^produk\\|'))
        dp.add_handler(CallbackQueryHandler(riwayat_callback, pattern='^riwayat$'))
        dp.add_handler(CallbackQueryHandler(semua_riwayat_callback, pattern='^semua_riwayat$'))
        dp.add_handler(CallbackQueryHandler(stock_akrab_callback, pattern='^stock_akrab$'))
        dp.add_handler(CallbackQueryHandler(stock_akrab_callback, pattern='^stock$'))
        dp.add_handler(CallbackQueryHandler(lihat_saldo_callback, pattern='^lihat_saldo$'))
        dp.add_handler(CallbackQueryHandler(tambah_saldo_callback, pattern='^tambah_saldo$'))
        dp.add_handler(CallbackQueryHandler(cek_status_callback, pattern='^cek_status$'))

        # Command handler
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", start))
        dp.add_handler(CommandHandler("menu", start))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))
        dp.add_handler(CommandHandler("order", start))
        dp.add_handler(CommandHandler("topup", start))
        dp.add_handler(CommandHandler("status", start))
        dp.add_handler(CommandHandler("saldo", start))
        dp.add_handler(CommandHandler("riwayat", start))
        dp.add_handler(CommandHandler("stock", start))
        dp.add_handler(CommandHandler("admin", start))

        # Message handler utama: gunakan reply_menu_handler AGAR SEMUA MENU REPLY BERFUNGSI!
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reply_menu_handler))

        # Error handler
        def error_handler(update, context):
            try:
                error_msg = f"Error: {context.error}"
                logger.error(error_msg)
                log_error(error_msg)
                if update and update.effective_message:
                    update.effective_message.reply_text(
                        "❌ Maaf, terjadi kesalahan sistem. Silakan coba lagi.",
                        reply_markup=main_menu_markup(is_admin=(update.effective_user and update.effective_user.id in ADMIN_IDS))
                    )
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
        dp.add_error_handler(error_handler)

        # Start bot
        updater.bot.delete_webhook()
        time.sleep(1)
        bot_info = updater.bot.get_me()
        print("🔄 Memulai polling...")
        updater.start_polling(
            poll_interval=1.0,
            timeout=30,
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        print("=" * 60)
        print("🎉 BOT BERHASIL DIJALANKAN!")
        print("=" * 60)
        print(f"🤖 Info Bot:")
        print(f"   📛 Nama: {bot_info.first_name}")
        print(f"   👤 Username: @{bot_info.username}")
        print(f"   🆔 ID: {bot_info.id}")
        print()
        print("📋 Fitur yang tersedia:")
        print("   ✅ Order Produk")
        print("   ✅ Topup Saldo")
        print("   ✅ Cek Status")
        print("   ✅ Lihat Riwayat")
        print("   ✅ Cek Stok")
        print("   ✅ Manajemen Saldo")
        print("   ✅ Error Handling")
        print()
        print("📍 Tekan Ctrl+C untuk stop bot")
        print("=" * 60)
        updater.idle()
    except KeyboardInterrupt:
        print("\n\n🛑 Bot dihentikan oleh user")
        print("👋 Sampai jumpa!")
        sys.exit(0)
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        print(f"💡 Critical error: {e}")
        print("🔧 Pastikan semua file berikut tersedia:")
        print("   - config.py dengan TOKEN dan ADMIN_IDS")
        print("   - Semua file handler di folder handlers/")
        print("   - Modul python-telegram-bot, requests")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Gagal menjalankan: {e}")
        log_error(f"❌ Gagal menjalankan: {e}")
        print(f"💡 Error detail: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
