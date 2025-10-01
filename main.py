#!/usr/bin/env python3
import sys
import time
import logging

from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
)

from config import TOKEN, ADMIN_IDS
from markup import reply_main_menu
from handlers.main_menu_handler import start, cancel, reply_menu_handler
from handlers.produk_daftar_handler import lihat_produk_callback
from handlers.produk_pilih_handler import produk_pilih_callback, CHOOSING_PRODUK, INPUT_TUJUAN
from handlers.input_tujuan_handler import handle_input_tujuan, KONFIRMASI
from handlers.order_handler import handle_konfirmasi
from handlers.stock_handler import stock_akrab_callback
from handlers.topup_handler import topup_callback, topup_nominal_step, TOPUP_NOMINAL, admin_topup_callback, admin_topup_list_callback, admin_topup_detail_callback
from handlers.riwayat_handler import riwayat_callback, semua_riwayat_callback
from handlers.saldo_handler import lihat_saldo_callback
from handlers.status_handler import cek_status_callback
from handlers.callback_handler import handle_all_callbacks
from handlers.admin_edit_handler import admin_edit_produk_callback, admin_edit_harga_prompt, admin_edit_deskripsi_prompt, admin_edit_produk_step, ADMIN_EDIT

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
    with open("error.log", "a", encoding='utf-8') as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_text}\n")

def main():
    print("=" * 60)
    print("🤖 BOT STARTING - FULL FEATURE VERSION")
    print("=" * 60)
    try:
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher

        # ==================== GLOBAL CALLBACK HANDLER ====================
        # HARUS DITAMBAHKAN PERTAMA untuk menangani semua callback
        dp.add_handler(CallbackQueryHandler(handle_all_callbacks))

        # ==================== CONVERSATION HANDLER UNTUK ORDER PRODUK ====================
        order_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(Filters.regex("^(🛒 Order Produk)$"), lihat_produk_callback)],
            states={
                CHOOSING_PRODUK: [
                    CallbackQueryHandler(produk_pilih_callback, pattern="^produk_static\\|"),
                    CallbackQueryHandler(produk_pilih_callback, pattern="^back_main$")
                ],
                INPUT_TUJUAN: [MessageHandler(Filters.text & ~Filters.command, handle_input_tujuan)],
                KONFIRMASI: [
                    CallbackQueryHandler(handle_konfirmasi, pattern="^(order_konfirmasi|order_batal)$"),
                    MessageHandler(Filters.text & ~Filters.command, handle_konfirmasi)
                ]
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            allow_reentry=True,
        )
        dp.add_handler(order_conv_handler)

        # ==================== CONVERSATION HANDLER UNTUK TOPUP ====================
        topup_conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(Filters.regex("^(💳 Top Up Saldo)$"), topup_callback),
                CallbackQueryHandler(topup_callback, pattern="^topup_start$")
            ],
            states={
                TOPUP_NOMINAL: [MessageHandler(Filters.text & ~Filters.command, topup_nominal_step)]
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            allow_reentry=True,
        )
        dp.add_handler(topup_conv_handler)

        # ==================== CONVERSATION HANDLER UNTUK ADMIN EDIT PRODUK ====================
        admin_edit_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(admin_edit_produk_callback, pattern="^admin_edit_produk\\|")],
            states={
                ADMIN_EDIT: [MessageHandler(Filters.text & ~Filters.command, admin_edit_produk_step)]
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            allow_reentry=True,
        )
        dp.add_handler(admin_edit_conv_handler)

        # ==================== BASIC COMMAND HANDLERS ====================
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", start))
        dp.add_handler(CommandHandler("menu", start))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))

        # ==================== MESSAGE HANDLERS UNTUK MENU ====================
        dp.add_handler(MessageHandler(Filters.regex("^(📦 Cek Stok)$"), stock_akrab_callback))
        dp.add_handler(MessageHandler(Filters.regex("^(📋 Riwayat Transaksi)$"), riwayat_callback))
        dp.add_handler(MessageHandler(Filters.regex("^(💰 Lihat Saldo)$"), lihat_saldo_callback))
        dp.add_handler(MessageHandler(Filters.regex("^(🔍 Cek Status)$"), cek_status_callback))
        dp.add_handler(MessageHandler(Filters.regex("^(❓ Bantuan)$"), start))

        # ==================== ADMIN HANDLERS ====================
        # Handler untuk admin topup management
        dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern="^topup_(approve|batal)\\|"))
        dp.add_handler(CallbackQueryHandler(admin_topup_list_callback, pattern="^riwayat_topup_admin$"))
        dp.add_handler(CallbackQueryHandler(admin_topup_detail_callback, pattern="^admin_topup_detail\\|"))
        
        # Handler untuk admin edit produk prompts
        dp.add_handler(CallbackQueryHandler(admin_edit_harga_prompt, pattern="^edit_harga\\|"))
        dp.add_handler(CallbackQueryHandler(admin_edit_deskripsi_prompt, pattern="^edit_deskripsi\\|"))
        
        # Handler untuk semua riwayat admin
        dp.add_handler(CallbackQueryHandler(semua_riwayat_callback, pattern="^semua_riwayat$"))

        # ==================== FALLBACK HANDLER ====================
        # Handler untuk menangani semua text message yang tidak tertangani
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reply_menu_handler))

        # ==================== ERROR HANDLER ====================
        def error_handler(update, context):
            try:
                error_msg = f"Error: {context.error}"
                logger.error(error_msg)
                log_error(error_msg)
                
                # Cek apakah update ada dan bisa reply
                if update and update.effective_message:
                    is_admin = update.effective_user and update.effective_user.id in ADMIN_IDS
                    update.effective_message.reply_text(
                        "❌ Maaf, terjadi kesalahan sistem. Silakan coba lagi.",
                        reply_markup=reply_main_menu(is_admin=is_admin)
                    )
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
        
        dp.add_error_handler(error_handler)

        # ==================== START BOT ====================
        updater.bot.delete_webhook()
        time.sleep(1)
        
        print("🔄 Memulai polling...")
        print("📋 Fitur yang aktif:")
        print("   ✅ Order Produk (Conversation)")
        print("   ✅ Top Up Saldo (Conversation)") 
        print("   ✅ Cek Stok")
        print("   ✅ Riwayat Transaksi")
        print("   ✅ Lihat Saldo")
        print("   ✅ Cek Status")
        print("   ✅ Admin Panel")
        print("   ✅ Callback Handler Global")
        
        updater.start_polling(
            poll_interval=1.0,
            timeout=30,
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query', 'inline_query']
        )
        
        print("=" * 60)
        print("🎉 BOT BERHASIL DIJALANKAN!")
        print("🤖 Bot sedang berjalan...")
        print("⏹️  Tekan Ctrl+C untuk menghentikan bot")
        print("=" * 60)
        
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Gagal menjalankan bot: {e}")
        log_error(f"❌ Gagal menjalankan bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
