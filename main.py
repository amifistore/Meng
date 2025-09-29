#!/usr/bin/env python3
import sys
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from markup import reply_main_menu

def log_error(error_text):
    with open("error.log", "a", encoding='utf-8') as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_text}\n")

def main():
    print("=" * 60)
    print("🤖 BOT STARTING - FULL FEATURE VERSION")
    print("=" * 60)
    try:
        from config import TOKEN, ADMIN_IDS
        from telegram.ext import (
            Updater, CommandHandler, MessageHandler, Filters
        )
        from handlers.main_menu_handler import start, cancel, main_menu_callback, reply_menu_handler

        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher

        # Command handler
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", start))
        dp.add_handler(CommandHandler("menu", start))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reply_menu_handler))

        # Error handler
        def error_handler(update, context):
            try:
                error_msg = f"Error: {context.error}"
                logger.error(error_msg)
                log_error(error_msg)
                update.effective_message.reply_text(
                    "❌ Maaf, terjadi kesalahan sistem. Silakan coba lagi.",
                    reply_markup=reply_main_menu(is_admin=(update.effective_user and update.effective_user.id in ADMIN_IDS))
                )
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
        dp.add_error_handler(error_handler)

        updater.bot.delete_webhook()
        time.sleep(1)
        print("🔄 Memulai polling...")
        updater.start_polling(
            poll_interval=1.0,
            timeout=30,
            drop_pending_updates=True,
            allowed_updates=['message']
        )
        print("=" * 60)
        print("🎉 BOT BERHASIL DIJALANKAN!")
        print("=" * 60)
        updater.idle()
    except Exception as e:
        logger.error(f"❌ Gagal menjalankan: {e}")
        log_error(f"❌ Gagal menjalankan: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
