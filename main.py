#!/usr/bin/env python3
import sys
import time
import logging
import sqlite3
import os

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

def safe_int_convert(value):
    """Convert value to integer safely"""
    try:
        if isinstance(value, str):
            cleaned = ''.join(c for c in value if c.isdigit() or c == '-')
            return int(cleaned) if cleaned else 0
        elif isinstance(value, (int, float)):
            return int(value)
        else:
            return 0
    except (ValueError, TypeError):
        return 0

def init_all_databases():
    """Initialize semua database dengan struktur yang benar"""
    print("🔄 Initializing all databases...")
    try:
        # Clear Python cache
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(".pyc"):
                    os.remove(os.path.join(root, file))
            for dir in dirs:
                if dir == "__pycache__":
                    os.rmdir(os.path.join(root, dir))
        
        # Import modules untuk trigger auto-init
        import saldo
        import riwayat  
        import topup
        
        # Force re-initialization
        saldo.init_db_saldo()
        riwayat.init_db_riwayat()
        topup.init_db_topup()
        
        print("✅ All databases initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize databases: {e}")
        return False

def setup_test_data():
    """Setup data testing"""
    try:
        from saldo import tambah_saldo_user, get_saldo_user
        
        # Setup test user (ganti dengan user ID Telegram Anda)
        TEST_USER_ID = 123456789  # <- GANTI INI!
        
        # Cek apakah user sudah ada
        saldo_user = get_saldo_user(TEST_USER_ID)
        if saldo_user == 0:
            # Tambah saldo untuk testing
            success = tambah_saldo_user(TEST_USER_ID, 100000, "initial", "Saldo awal testing")
            if success:
                print(f"✅ Saldo 100.000 ditambahkan ke user {TEST_USER_ID}")
            else:
                print(f"❌ Gagal tambah saldo ke user {TEST_USER_ID}")
        else:
            print(f"✅ User {TEST_USER_ID} sudah ada dengan saldo: {saldo_user:,}")
            
    except Exception as e:
        print(f"⚠️ Setup test data: {e}")

def check_database_tables():
    """Cek struktur tabel database"""
    print("🔍 Checking database tables...")
    try:
        conn = sqlite3.connect("db_bot.db")
        cur = conn.cursor()
        
        # Cek semua tabel
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        
        required_tables = ['saldo', 'riwayat_saldo', 'riwayat_order', 'riwayat', 'topup']
        existing_tables = [table[0] for table in tables]
        
        print("📊 Tables found:")
        for table in existing_tables:
            print(f"   ✅ {table}")
        
        # Cek kolom untuk setiap tabel
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

def check_handler_files():
    """Cek semua file handler yang diperlukan"""
    print("🔍 Checking handler files...")
    
    required_handlers = [
        'main_menu_handler.py',
        'produk_pilih_handler.py', 
        'produk_daftar_handler.py',
        'input_tujuan_handler.py',
        'konfirmasi_handler.py',
        'riwayat_handler.py',
        'saldo_handler.py',
        'status_handler.py',
        'stock_handler.py'
    ]
    
    optional_handlers = [
        'topup_handler.py',
        'admin_produk_handler.py',
        'admin_edit_produk_handler.py'
    ]
    
    handlers_dir = "handlers"
    
    print("📁 Required handlers:")
    for handler in required_handlers:
        handler_path = os.path.join(handlers_dir, handler)
        if os.path.exists(handler_path):
            print(f"   ✅ {handler}")
        else:
            print(f"   ❌ {handler} - MISSING")
    
    print("📁 Optional handlers:")
    for handler in optional_handlers:
        handler_path = os.path.join(handlers_dir, handler)
        if os.path.exists(handler_path):
            print(f"   ✅ {handler}")
        else:
            print(f"   ⚠️ {handler} - Not available")
    
    return True

def main():
    print("=" * 60)
    print("🤖 BOT STARTING - FULL FEATURE VERSION")
    print("=" * 60)
    
    try:
        # Load configuration
        from config import TOKEN, ADMIN_IDS
        print(f"✅ Token loaded: {TOKEN[:10]}...")
        print(f"✅ Admin IDs: {ADMIN_IDS}")
        
        # Import Telegram
        from telegram.ext import (
            Updater, CommandHandler, CallbackQueryHandler, 
            MessageHandler, Filters, ConversationHandler
        )
        
        # Initialize semua database
        if not init_all_databases():
            print("❌ Database initialization failed")
            return
        
        # Check database structure
        check_database_tables()
        
        # Check handler files
        check_handler_files()
        
        # Setup test data
        setup_test_data()
        
        # Import semua handlers
        print("🔄 Loading all handlers...")
        
        # ========== IMPORT HANDLERS ==========
        
        # Main menu handler
        from handlers.main_menu_handler import (
            start, cancel, main_menu_callback,
            CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI
        )
        print("✅ Main menu handler loaded")
        
        # Product handlers
        from handlers.produk_pilih_handler import produk_pilih_callback
        from handlers.produk_daftar_handler import lihat_produk_callback
        print("✅ Product handlers loaded")
        
        # Order handlers
        from handlers.input_tujuan_handler import input_tujuan_step
        from handlers.konfirmasi_handler import handle_konfirmasi
        print("✅ Order handlers loaded")
        
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
        
        # History handlers
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
        
        # Create updater and dispatcher
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        print("✅ Updater created")
        
        # ==================== CONVERSATION HANDLERS ====================
        
        print("🔄 Setting up conversation handlers...")
        
        # === Order Produk Conversation ===
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

        # === Top Up Conversation (jika tersedia) ===
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

        # === Status Conversation ===
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

        # === Admin Edit Produk Conversation (jika tersedia) ===
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
        
        # Main menu callbacks
        dp.add_handler(CallbackQueryHandler(start, pattern='^start$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^main_menu$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^back_main$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^back_admin$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^back_menu$'))
        
        # Product callbacks
        dp.add_handler(CallbackQueryHandler(lihat_produk_callback, pattern='^lihat_produk$'))
        dp.add_handler(CallbackQueryHandler(produk_pilih_callback, pattern='^beli_produk$'))
        dp.add_handler(CallbackQueryHandler(produk_pilih_callback, pattern='^produk_static\\|'))
        dp.add_handler(CallbackQueryHandler(produk_pilih_callback, pattern='^produk\\|'))
        
        # History callbacks
        dp.add_handler(CallbackQueryHandler(riwayat_callback, pattern='^riwayat$'))
        dp.add_handler(CallbackQueryHandler(semua_riwayat_callback, pattern='^semua_riwayat$'))
        
        # Stock callbacks
        dp.add_handler(CallbackQueryHandler(stock_akrab_callback, pattern='^stock_akrab$'))
        dp.add_handler(CallbackQueryHandler(stock_akrab_callback, pattern='^stock$'))
        
        # Saldo callbacks
        dp.add_handler(CallbackQueryHandler(lihat_saldo_callback, pattern='^lihat_saldo$'))
        dp.add_handler(CallbackQueryHandler(tambah_saldo_callback, pattern='^tambah_saldo$'))
        
        # Admin callbacks (jika tersedia)
        if ADMIN_AVAILABLE:
            dp.add_handler(CallbackQueryHandler(admin_edit_produk_callback, pattern='^admin_edit_produk\\|'))
            dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^manajemen_produk$'))
        
        # Topup admin callbacks (jika tersedia)
        if TOPUP_AVAILABLE:
            dp.add_handler(CallbackQueryHandler(admin_topup_list_callback, pattern='^riwayat_topup_admin$'))
            dp.add_handler(CallbackQueryHandler(admin_topup_detail_callback, pattern='^admin_topup_detail\\|'))
            dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern='^topup_approve\\|'))
            dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern='^topup_batal\\|'))
        
        # Status callbacks
        dp.add_handler(CallbackQueryHandler(cek_status_callback, pattern='^cek_status$'))
        
        print("✅ Callback query handlers setup complete")
        
        # ==================== MESSAGE HANDLERS ====================
        
        print("🔄 Setting up message handlers...")
        
        # Command handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", start))
        dp.add_handler(CommandHandler("menu", start))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))
        
        # Feature commands
        dp.add_handler(CommandHandler("order", start))
        dp.add_handler(CommandHandler("topup", start))
        dp.add_handler(CommandHandler("status", start))
        dp.add_handler(CommandHandler("saldo", start))
        dp.add_handler(CommandHandler("riwayat", start))
        dp.add_handler(CommandHandler("stock", start))
        
        # Admin commands
        dp.add_handler(CommandHandler("admin", start))
        
        # Fallback text handler
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
        
        # Clean previous webhook
        try:
            updater.bot.delete_webhook()
            time.sleep(1)
            print("✅ Webhook cleaned")
        except Exception as e:
            print(f"ℹ️ No webhook to clean: {e}")
        
        # Get bot info
        bot_info = updater.bot.get_me()
        
        print("🔄 Starting polling...")
        updater.start_polling(
            poll_interval=1.0,
            timeout=30,
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        
        # Success message
        print("=" * 60)
        print("🎉 BOT STARTED SUCCESSFULLY!")
        print("=" * 60)
        print(f"🤖 Bot Info:")
        print(f"   📛 Name: {bot_info.first_name}")
        print(f"   👤 Username: @{bot_info.username}")
        print(f"   🆔 ID: {bot_info.id}")
        print()
        print("📋 Available Features:")
        print("   ✅ Order Products")
        print("   ✅ Topup Balance") 
        print("   ✅ Check Status")
        print("   ✅ View History")
        print("   ✅ Stock Check")
        print("   ✅ Balance Management")
        if ADMIN_AVAILABLE:
            print("   ✅ Admin Panel")
        if TOPUP_AVAILABLE:
            print("   ✅ Topup System")
        print("   ✅ Error Handling")
        print()
        print("📍 Press Ctrl+C to stop the bot")
        print("=" * 60)
        
        # Keep bot running
        updater.idle()

    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user")
        print("👋 Goodbye!")
        sys.exit(0)
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        print(f"💡 Critical error: {e}")
        print("🔧 Please check if all required files exist:")
        print("   - config.py with TOKEN and ADMIN_IDS")
        print("   - All handler files in handlers/ folder")
        print("   - Required modules: python-telegram-bot, requests")
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
