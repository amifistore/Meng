from telegram import ParseMode
from markup import reply_main_menu
from config import ADMIN_IDS

def is_admin(user_id):
    return user_id in ADMIN_IDS

def start(update, context):
    user = update.effective_user
    update.message.reply_text(
        "Selamat datang! Silakan pilih menu:",
        parse_mode=ParseMode.HTML,
        reply_markup=reply_main_menu(is_admin(user.id))
    )

# ... fungsi lain seperti reply_menu_handler, cancel, dll ...

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

from markup import main_menu_markup, reply_main_menu

def log_error(error_text):
    with open("error.log", "a", encoding='utf-8') as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_text}\n")

def safe_int_convert(value):
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
        TEST_USER_ID = 123456789  # <- GANTI INI!
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

def check_database_tables():
    print("🔍 Cek tabel database...")
    try:
        conn = sqlite3.connect("db_bot.db")
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        required_tables = ['saldo', 'riwayat_saldo', 'riwayat_order', 'riwayat', 'topup']
        existing_tables = [table[0] for table in tables]
        print("📊 Tabel ditemukan:")
        for table in existing_tables:
            print(f"   ✅ {table}")
        for table in required_tables:
            if table in existing_tables:
                cur.execute(f"PRAGMA table_info({table})")
                columns = cur.fetchall()
                print(f"   📋 {table}: {len(columns)} kolom")
            else:
                print(f"   ❌ {table}: TIDAK ADA")
        conn.close()
        print("✅ Cek database selesai")
        return True
    except Exception as e:
        print(f"❌ Gagal cek database: {e}")
        return False

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
        'stock_handler.py'
    ]
    optional_handlers = [
        'topup_handler.py',
        'admin_produk_handler.py',
        'admin_edit_produk_handler.py'
    ]
    handlers_dir = "handlers"
    print("📁 Handler wajib:")
    for handler in required_handlers:
        handler_path = os.path.join(handlers_dir, handler)
        if os.path.exists(handler_path):
            print(f"   ✅ {handler}")
        else:
            print(f"   ❌ {handler} - TIDAK ADA")
    print("📁 Handler opsional:")
    for handler in optional_handlers:
        handler_path = os.path.join(handlers_dir, handler)
        if os.path.exists(handler_path):
            print(f"   ✅ {handler}")
        else:
            print(f"   ⚠️ {handler} - Tidak tersedia")
    return True

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
        check_database_tables()
        check_handler_files()
        setup_test_data()
        print("🔄 Load semua handler...")
        from handlers.main_menu_handler import (
            start, cancel, main_menu_callback, reply_menu_handler,
            CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI
        )
        print("✅ Main menu handler loaded")
        from handlers.produk_pilih_handler import produk_pilih_callback
        from handlers.produk_daftar_handler import lihat_produk_callback
        print("✅ Product handlers loaded")
        from handlers.input_tujuan_handler import input_tujuan_step
        from handlers.konfirmasi_handler import handle_konfirmasi
        print("✅ Order handlers loaded")
        try:
            from handlers.topup_handler import (
                topup_callback, topup_nominal_step, TOPUP_NOMINAL, 
                admin_topup_callback, admin_topup_list_callback, admin_topup_detail_callback
            )
            TOPUP_AVAILABLE = True
            print("✅ Topup handler loaded")
        except ImportError as e:
            TOPUP_AVAILABLE = False
            print(f"⚠️ Topup handler tidak tersedia: {e}")
        try:
            from handlers.riwayat_handler import riwayat_callback, semua_riwayat_callback
            print("✅ Riwayat handler loaded")
        except ImportError as e:
            print(f"❌ Riwayat handler gagal: {e}")
            return
        try:
            from handlers.stock_handler import stock_akrab_callback
            print("✅ Stock handler loaded")
        except ImportError as e:
            print(f"⚠️ Stock handler tidak tersedia: {e}")
        try:
            from handlers.saldo_handler import lihat_saldo_callback, tambah_saldo_callback
            print("✅ Saldo handler loaded")
        except ImportError as e:
            print(f"❌ Saldo handler gagal: {e}")
            return
        try:
            from handlers.admin_produk_handler import (
                admin_edit_produk_callback, admin_edit_harga_prompt,
                admin_edit_deskripsi_prompt, admin_edit_produk_step
            )
            ADMIN_AVAILABLE = True
            print("✅ Admin handler loaded")
        except ImportError as e:
            ADMIN_AVAILABLE = False
            print(f"⚠️ Admin handler tidak tersedia: {e}")
        try:
            from handlers.status_handler import cek_status_callback, input_refid_step, INPUT_REFID
            print("✅ Status handler loaded")
        except ImportError as e:
            print(f"❌ Status handler gagal: {e}")
            return
        print("✅ Semua handler berhasil di-load")
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        print("✅ Updater dibuat")

        # ==================== CONVERSATION HANDLERS ====================
        print("🔄 Setup conversation handlers...")

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
        print("🔄 Setup callback query handlers...")
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
        print("🔄 Setup message handlers...")
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
        # FIX: gunakan reply_menu_handler untuk pesan reply keyboard
        from handlers.main_menu_handler import reply_menu_handler
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reply_menu_handler))
        print("✅ Message handlers setup complete")

        # ==================== ERROR HANDLER ====================
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
        print("✅ Error handler setup complete")

        print("🔄 Final preparations...")
        try:
            updater.bot.delete_webhook()
            time.sleep(1)
            print("✅ Webhook dibersihkan")
        except Exception as e:
            print(f"ℹ️ Tidak ada webhook yang perlu dibersihkan: {e}")
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
        if ADMIN_AVAILABLE:
            print("   ✅ Admin Panel")
        if TOPUP_AVAILABLE:
            print("   ✅ Sistem Topup")
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
