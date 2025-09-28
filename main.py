#!/usr/bin/env python3
import sys
import time
import logging
import sqlite3

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
    try:
        import saldo
        import riwayat  
        import topup
        print("✅ All databases initialized automatically")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize databases: {e}")
        return False

def setup_test_data():
    """Setup data testing"""
    try:
        from saldo import tambah_saldo_user, get_saldo_user
        TEST_USER_ID = 123456789  # <- GANTI INI!
        saldo = get_saldo_user(TEST_USER_ID)
        if saldo == 0:
            success = tambah_saldo_user(TEST_USER_ID, 100000, "initial", "Saldo awal testing")
            if success:
                print(f"✅ Saldo 100.000 ditambahkan ke user {TEST_USER_ID}")
            else:
                print(f"❌ Gagal tambah saldo ke user {TEST_USER_ID}")
        else:
            print(f"✅ User {TEST_USER_ID} sudah ada dengan saldo: {saldo:,}")
    except Exception as e:
        print(f"⚠️ Setup test data skipped: {e}")

def check_database_tables():
    """Cek struktur tabel database"""
    print("🔍 Checking database tables...")
    try:
        conn = sqlite3.connect("db_bot.db")
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        required_tables = ['saldo', 'riwayat_saldo', 'riwayat_order', 'riwayat', 'topup']
        existing_tables = [table[0] for table in tables]
        print("📊 Tables found:")
        for table in existing_tables:
            print(f"   ✅ {table}")
        for table in required_tables:
            if table in existing_tables:
                cur.execute(f"PRAGMA table_info({table})")
                columns = cur.fetchall()
                print(f"   📋 {table}: {len(columns)} columns")
            else:
                print(f"   ❌ {table}: MISSING")
        conn.close()
        print("✅ Database check completed")
        return True
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

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
            print("❌ Database initialization failed")
            return
        check_database_tables()
        setup_test_data()
        print("🔄 Loading all handlers...")
        # ======== IMPORT HANDLERS =========
        from handlers.main_menu_handler import (
            start, cancel, main_menu_callback,
            CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI
        )
        from handlers.produk_pilih_handler import produk_pilih_callback
        from handlers.produk_daftar_handler import lihat_produk_callback
        from handlers.input_tujuan_handler import input_tujuan_step
        from handlers.konfirmasi_handler import handle_konfirmasi
        # Topup handlers (opsional)
        try:
            from handlers.topup_handler import (
                topup_callback, topup_nominal_step, TOPUP_NOMINAL, 
                admin_topup_callback, admin_topup_list_callback, admin_topup_detail_callback
            )
            TOPUP_AVAILABLE = True
            print("✅ Topup handler loaded")
        except ImportError as e:
            TOPUP_AVAILABLE = False
            print(f"⚠️ Topup handler not available: {e}")
        # History handlers -- FIX: pakai riwayat_handler, bukan rivayat_handler
        try:
            from handlers.riwayat_handler import riwayat_callback, semua_riwayat_callback
            print("✅ Riwayat handler loaded")
        except ImportError as e:
            print(f"❌ Riwayat handler failed: {e}")
            return
        # Stock handlers
        try:
            from handlers.stock_handler import stock_akrab_callback
            print("✅ Stock handler loaded")
        except ImportError as e:
            print(f"⚠️ Stock handler not available: {e}")
        # Saldo handlers
        try:
            from handlers.saldo_handler import lihat_saldo_callback, tambah_saldo_callback
            print("✅ Saldo handler loaded")
        except ImportError as e:
            print(f"❌ Saldo handler failed: {e}")
            return
        # Admin product handlers (opsional)
        try:
            from handlers.admin_produk_handler import (
                admin_edit_produk_callback, admin_edit_harga_prompt,
                admin_edit_deskripsi_prompt, admin_edit_produk_step
            )
            ADMIN_AVAILABLE = True
            print("✅ Admin handler loaded")
        except ImportError as e:
            ADMIN_AVAILABLE = False
            print(f"⚠️ Admin handler not available: {e}")
        # Status handlers
        try:
            from handlers.status_handler import cek_status_callback, input_refid_step, INPUT_REFID
            print("✅ Status handler loaded")
        except ImportError as e:
            print(f"❌ Status handler failed: {e}")
            return
        print("✅ All handlers loaded successfully")
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        print("✅ Updater created")
        # ==================== CONVERSATION HANDLERS ====================
        print("🔄 Setting up conversation handlers...")
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
        print("✅ Order conversation handler setup")
        if TOPUP_AVAILABLE:
            topup_conv_handler = ConversationHandler(
                entry_points=[
                    CallbackQueryHandler(topup_callback, pattern='^topup$'),
                    CommandHandler('topup', start)
                ],
                states={
                    TOPUP_NOMINAL: [
                        MessageHandler(Filters.text & ~Filters.command, topup_nominal_step)
                    ],
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
            print("✅ Topup conversation handler setup")
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
        print("✅ Status conversation handler setup")
        if ADMIN_AVAILABLE:
            admin_edit_conv_handler = ConversationHandler(
                entry_points=[
                    CallbackQueryHandler(admin_edit_harga_prompt, pattern='^editharga\\|'),
                    CallbackQueryHandler(admin_edit_deskripsi_prompt, pattern='^editdeskripsi\\|'),
                ],
                states={
                    4: [MessageHandler(Filters.text & ~Filters.command, admin_edit_produk_step)],
                },
                fallbacks=[
                    CommandHandler('cancel', cancel),
                    CommandHandler('batal', cancel)
                ],
                allow_reentry=True,
                name="admin_edit_conversation"
            )
            dp.add_handler(admin_edit_conv_handler)
            print("✅ Admin edit conversation handler setup")
        # ==================== CALLBACK QUERY HANDLERS ====================
        print("🔄 Setting up callback query handlers...")
        dp.add_handler(CallbackQueryHandler(start, pattern='^start$'))
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
        if ADMIN_AVAILABLE:
            dp.add_handler(CallbackQueryHandler(admin_edit_produk_callback, pattern='^admin_edit_produk\\|'))
            dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^manajemen_produk$'))
        if TOPUP_AVAILABLE:
            dp.add_handler(CallbackQueryHandler(admin_topup_list_callback, pattern='^riwayat_topup_admin$'))
            dp.add_handler(CallbackQueryHandler(admin_topup_detail_callback, pattern='^admin_topup_detail\\|'))
            dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern='^topup_approve\\|'))
            dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern='^topup_batal\\|'))
        dp.add_handler(CallbackQueryHandler(cek_status_callback, pattern='^cek_status$'))
        print("✅ Callback query handlers setup complete")
        # ==================== MESSAGE HANDLERS ====================
        print("🔄 Setting up message handlers...")
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", start))
        dp.add_handler(CommandHandler("menu", start))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))
        dp.add_handler(CommandHandler("admin", start))
        dp.add_handler(MessageHandler(
            Filters.text & ~Filters.command, 
            start
        ))
        print("✅ Message handlers setup complete")
        # ==================== ERROR HANDLER ====================
        def error_handler(update, context):
            """Global error handler"""
            try:
                error_msg = f"Error: {context.error}"
                logger.error(error_msg)
                log_error(error_msg)
                if update and update.effective_message:
                    update.effective_message.reply_text(
                        "❌ Maaf, terjadi kesalahan sistem. Silakan coba lagi."
                    )
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
        dp.add_error_handler(error_handler)
        print("✅ Error handler setup complete")
        # ==================== START BOT ====================
        print("🔄 Final preparations...")
        try:
            updater.bot.delete_webhook()
            time.sleep(1)
            print("✅ Webhook cleaned")
        except Exception as e:
            print(f"ℹ️ No webhook to clean: {e}")
        bot_info = updater.bot.get_me()
        print("🔄 Starting polling...")
        updater.start_polling(
            poll_interval=1.0,
            timeout=30,
            drop_pending_updates=True
        )
        print("=" * 60)
        print("🎉 BOT STARTED SUCCESSFULLY!")
        print("=" * 60)
        print(f"🤖 Bot: @{bot_info.username}")
        print(f"📛 Name: {bot_info.first_name}")
        print("📍 Press Ctrl+C to stop")
        print("=" * 60)
        updater.idle()
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user")
        print("👋 Goodbye!")
        sys.exit(0)
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        print(f"💡 Critical error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Failed to start: {e}")
        log_error(f"❌ Failed to start: {e}")
        print(f"💡 Error details: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
