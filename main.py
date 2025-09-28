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
    
    # Import modules untuk trigger auto-init
    import saldo
    import riwayat  
    import topup
    
    # Force re-initialization dengan struktur yang benar
    saldo.init_db_saldo()
    riwayat.init_db_riwayat()
    topup.init_db_topup()
    
    print("✅ All databases initialized")

def setup_test_data():
    """Setup data testing"""
    try:
        from saldo import tambah_saldo_user, get_saldo_user
        
        # Setup test user (ganti dengan user ID Telegram Anda)
        TEST_USER_ID = 123456789  # <- GANTI INI!
        
        # Cek apakah user sudah ada
        saldo = get_saldo_user(TEST_USER_ID)
        if saldo == 0:
            # Tambah saldo untuk testing
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
        init_all_databases()
        
        # Setup test data
        setup_test_data()
        
        # Check database structure
        check_database_tables()
        
        # Import semua handlers
        print("🔄 Loading all handlers...")
        
        # ========== IMPORT HANDLERS ==========
        
        # Main menu handler
        from handlers.main_menu_handler import (
            start, cancel, main_menu_callback,
            CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI
        )
        
        # Product handlers
        from handlers.produk_pilih_handler import produk_pilih_callback
        from handlers.produk_daftar_handler import lihat_produk_callback
        
        # Order handlers
        from handlers.input_tujuan_handler import input_tujuan_step
        from handlers.konfirmasi_handler import handle_konfirmasi
        
        # Topup handlers
        from handlers.topup_handler import (
            topup_callback, topup_nominal_step, TOPUP_NOMINAL, 
            admin_topup_callback, admin_topup_list_callback, admin_topup_detail_callback
        )
        
        # History handlers
        from handlers.rivayat_handler import riwayat_callback, semua_riwayat_callback
        
        # Stock handlers
        from handlers.stock_handler import stock_akrab_callback
        
        # Saldo handlers
        from handlers.saldo_handler import lihat_saldo_callback, tambah_saldo_callback
        
        # Admin product handlers
        from handlers.admin_produk_handler import (
            admin_edit_produk_callback, admin_edit_harga_prompt,
            admin_edit_deskripsi_prompt, admin_edit_produk_step
        )
        
        # Status handlers
        from handlers.status_handler import cek_status_callback, input_refid_step, INPUT_REFID
        
        # Debug handler (opsional)
        try:
            from handlers.debug_handler import debug_callback
            DEBUG_AVAILABLE = True
            print("✅ Debug handler loaded")
        except ImportError:
            DEBUG_AVAILABLE = False
            print("⚠️ Debug handler not available")
        
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
                CommandHandler('order', start),
                CommandHandler('buy', start)
            ],
            states={
                CHOOSING_PRODUK: [
                    CallbackQueryHandler(produk_pilih_callback, pattern='^produk_static\\|'),
                    CallbackQueryHandler(produk_pilih_callback, pattern='^produk\\|'),
                    CallbackQueryHandler(produk_pilih_callback, pattern='^category\\|')
                ],
                INPUT_TUJUAN: [
                    MessageHandler(Filters.text & ~Filters.command, input_tujuan_step),
                    CallbackQueryHandler(input_tujuan_step, pattern='^back_to_tujuan$')
                ],
                KONFIRMASI: [
                    CallbackQueryHandler(handle_konfirmasi, pattern='^(konfirmasi_order|batal_order|order_konfirmasi|order_batal|ya_order|tidak_order|confirm_order|cancel_order)$'),
                    MessageHandler(Filters.text & ~Filters.command, handle_konfirmasi)
                ]
            },
            fallbacks=[
                CommandHandler('cancel', cancel),
                CommandHandler('batal', cancel),
                CommandHandler('start', start),
                CommandHandler('menu', start)
            ],
            allow_reentry=True,
            name="order_conversation",
            persistent=True
        )
        dp.add_handler(order_conv_handler)
        print("✅ Order conversation handler setup")

        # === Top Up Conversation ===
        topup_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(topup_callback, pattern='^topup$'),
                CommandHandler('topup', start),
                CommandHandler('deposit', start)
            ],
            states={
                TOPUP_NOMINAL: [
                    MessageHandler(Filters.text & ~Filters.command, topup_nominal_step),
                    CallbackQueryHandler(topup_nominal_step, pattern='^back_to_nominal$')
                ],
            },
            fallbacks=[
                CommandHandler('cancel', cancel),
                CommandHandler('batal', cancel),
                CommandHandler('start', start),
                CommandHandler('menu', start)
            ],
            allow_reentry=True,
            name="topup_conversation",
            persistent=True
        )
        dp.add_handler(topup_conv_handler)
        print("✅ Topup conversation handler setup")

        # === Status Conversation ===
        status_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(cek_status_callback, pattern='^cek_status$'),
                CommandHandler('status', start),
                CommandHandler('check', start)
            ],
            states={
                INPUT_REFID: [
                    MessageHandler(Filters.text & ~Filters.command, input_refid_step),
                    CallbackQueryHandler(input_refid_step, pattern='^back_to_refid$')
                ],
            },
            fallbacks=[
                CommandHandler('cancel', cancel),
                CommandHandler('batal', cancel),
                CommandHandler('start', start),
                CommandHandler('menu', start)
            ],
            allow_reentry=True,
            name="status_conversation",
            persistent=True
        )
        dp.add_handler(status_conv_handler)
        print("✅ Status conversation handler setup")

        # === Admin Edit Produk Conversation ===
        admin_edit_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(admin_edit_harga_prompt, pattern='^editharga\\|'),
                CallbackQueryHandler(admin_edit_deskripsi_prompt, pattern='^editdeskripsi\\|'),
                CallbackQueryHandler(admin_edit_produk_callback, pattern='^edit_produk\\|')
            ],
            states={
                4: [
                    MessageHandler(Filters.text & ~Filters.command, admin_edit_produk_step),
                    CallbackQueryHandler(admin_edit_produk_step, pattern='^back_to_edit$')
                ],
            },
            fallbacks=[
                CommandHandler('cancel', cancel),
                CommandHandler('batal', cancel),
                CommandHandler('start', start),
                CommandHandler('admin', start)
            ],
            allow_reentry=True,
            name="admin_edit_conversation",
            persistent=True
        )
        dp.add_handler(admin_edit_conv_handler)
        print("✅ Admin edit conversation handler setup")
        
        # ==================== CALLBACK QUERY HANDLERS ====================
        
        print("🔄 Setting up callback query handlers...")
        
        # Main menu navigation
        dp.add_handler(CallbackQueryHandler(start, pattern='^start$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^main_menu$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^back_main$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^back_admin$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^back_menu$'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^home$'))
        
        # Product management
        dp.add_handler(CallbackQueryHandler(lihat_produk_callback, pattern='^lihat_produk$'))
        dp.add_handler(CallbackQueryHandler(produk_pilih_callback, pattern='^beli_produk$'))
        dp.add_handler(CallbackQueryHandler(produk_pilih_callback, pattern='^produk_static\\|'))
        dp.add_handler(CallbackQueryHandler(produk_pilih_callback, pattern='^produk\\|'))
        dp.add_handler(CallbackQueryHandler(produk_pilih_callback, pattern='^category\\|'))
        
        # History and records
        dp.add_handler(CallbackQueryHandler(riwayat_callback, pattern='^riwayat$'))
        dp.add_handler(CallbackQueryHandler(semua_riwayat_callback, pattern='^semua_riwayat$'))
        dp.add_handler(CallbackQueryHandler(riwayat_callback, pattern='^history$'))
        dp.add_handler(CallbackQueryHandler(semua_riwayat_callback, pattern='^all_history$'))
        
        # Stock information
        dp.add_handler(CallbackQueryHandler(stock_akrab_callback, pattern='^stock_akrab$'))
        dp.add_handler(CallbackQueryHandler(stock_akrab_callback, pattern='^stock$'))
        dp.add_handler(CallbackQueryHandler(stock_akrab_callback, pattern='^check_stock$'))
        
        # Balance management
        dp.add_handler(CallbackQueryHandler(lihat_saldo_callback, pattern='^lihat_saldo$'))
        dp.add_handler(CallbackQueryHandler(tambah_saldo_callback, pattern='^tambah_saldo$'))
        dp.add_handler(CallbackQueryHandler(lihat_saldo_callback, pattern='^balance$'))
        dp.add_handler(CallbackQueryHandler(tambah_saldo_callback, pattern='^add_balance$'))
        
        # Admin functions
        dp.add_handler(CallbackQueryHandler(admin_edit_produk_callback, pattern='^admin_edit_produk\\|'))
        dp.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^manajemen_produk$'))
        dp.add_handler(CallbackQueryHandler(admin_topup_list_callback, pattern='^riwayat_topup_admin$'))
        dp.add_handler(CallbackQueryHandler(admin_topup_detail_callback, pattern='^admin_topup_detail\\|'))
        
        # Topup management
        dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern='^topup_approve\\|'))
        dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern='^topup_batal\\|'))
        dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern='^topup_detail\\|'))
        dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern='^approve_topup\\|'))
        dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern='^reject_topup\\|'))
        
        # Status checking
        dp.add_handler(CallbackQueryHandler(cek_status_callback, pattern='^cek_status$'))
        dp.add_handler(CallbackQueryHandler(cek_status_callback, pattern='^check_status$'))
        
        # Debug functions (if available)
        if DEBUG_AVAILABLE:
            dp.add_handler(CallbackQueryHandler(debug_callback, pattern='^debug$'))
            dp.add_handler(CallbackQueryHandler(debug_callback, pattern='^test$'))
        
        print("✅ Callback query handlers setup complete")
        
        # ==================== MESSAGE HANDLERS ====================
        
        print("🔄 Setting up message handlers...")
        
        # Basic commands
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", start))
        dp.add_handler(CommandHandler("menu", start))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))
        
        # Feature commands
        dp.add_handler(CommandHandler("order", start))
        dp.add_handler(CommandHandler("buy", start))
        dp.add_handler(CommandHandler("topup", start))
        dp.add_handler(CommandHandler("deposit", start))
        dp.add_handler(CommandHandler("status", start))
        dp.add_handler(CommandHandler("check", start))
        dp.add_handler(CommandHandler("balance", start))
        dp.add_handler(CommandHandler("history", start))
        dp.add_handler(CommandHandler("stock", start))
        
        # Admin commands
        dp.add_handler(CommandHandler("admin", start))
        dp.add_handler(CommandHandler("manage", start))
        
        # Fallback handler - handle any text message with main menu
        dp.add_handler(MessageHandler(
            Filters.text & ~Filters.command, 
            start
        ))
        
        # Handle other message types
        dp.add_handler(MessageHandler(
            Filters.photo | Filters.document | Filters.video | Filters.audio,
            lambda update, context: update.message.reply_text(
                "🤖 Saya hanya menerima pesan teks. Gunakan menu di bawah untuk berinteraksi:",
                reply_markup=context.bot.send_message(update.effective_chat.id, "Pilih menu:").reply_markup
            )
        ))
        
        print("✅ Message handlers setup complete")
        
        # ==================== ERROR HANDLER ====================
        
        def error_handler(update, context):
            """Global error handler"""
            try:
                # Log the error
                error_msg = f"Error: {context.error}"
                logger.error(error_msg)
                log_error(error_msg)
                
                # Send user-friendly message
                if update and update.effective_message:
                    update.effective_message.reply_text(
                        "❌ Maaf, terjadi kesalahan sistem. "
                        "Silakan coba lagi atau hubungi admin jika masalah berlanjut.\n\n"
                        "⚠️ Error telah dilaporkan ke developer."
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
            time.sleep(2)
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
            allowed_updates=['message', 'callback_query', 'inline_query']
        )
        
        # Success message
        print("=" * 60)
        print("🎉 BOT STARTED SUCCESSFULLY!")
        print("=" * 60)
        print(f"🤖 Bot Info:")
        print(f"   📛 Name: {bot_info.first_name}")
        print(f"   👤 Username: @{bot_info.username}")
        print(f"   🆔 ID: {bot_info.id}")
        print(f"   👑 Admin IDs: {ADMIN_IDS}")
        print()
        print("📋 Available Features:")
        print("   ✅ Order Products")
        print("   ✅ Topup Balance") 
        print("   ✅ Check Status")
        print("   ✅ View History")
        print("   ✅ Stock Check")
        print("   ✅ Admin Panel")
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
        print("🔧 Please check:")
        print("   - config.py exists with TOKEN and ADMIN_IDS")
        print("   - All handler files exist in handlers/ folder")
        print("   - Required modules are installed")
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
