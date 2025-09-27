import logging
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    ConversationHandler
)
from handlers import (
    start,
    cancel,
    main_menu_callback,
    choose_produk_callback,
    input_tujuan_callback,
    konfirmasi_callback,
    topup_nominal_callback,
    admin_edit_produk_callback,
)

# State definitions
CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, TOPUP_NOMINAL, ADMIN_EDIT = range(5)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # Ganti dengan token kamu
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Conversation handler for menu & transaksi
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(main_menu_callback)
        ],
        states={
            CHOOSING_PRODUK: [
                CallbackQueryHandler(choose_produk_callback)
            ],
            INPUT_TUJUAN: [
                MessageHandler(Filters.text & ~Filters.command, input_tujuan_callback)
            ],
            KONFIRMASI: [
                MessageHandler(Filters.text & ~Filters.command, konfirmasi_callback)
            ],
            TOPUP_NOMINAL: [
                MessageHandler(Filters.text & ~Filters.command, topup_nominal_callback)
            ],
            ADMIN_EDIT: [
                MessageHandler(Filters.text & ~Filters.command, admin_edit_produk_callback),
                CallbackQueryHandler(main_menu_callback)
            ],
        },
        fallbacks=[CommandHandler('batal', cancel)],
        allow_reentry=True,
        per_user=True
    )
    dp.add_handler(conv_handler)

    # Optional: Tambahkan handler lain jika perlu (misal help, info dsb)
    # dp.add_handler(CommandHandler('help', help_callback))

    # Start bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
