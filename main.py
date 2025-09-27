import logging
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    ConversationHandler
)
# Import semua handler dari main_menu_handler
from handlers.main_menu_handler import (
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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # Ganti dengan token bot kamu!
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(main_menu_callback)
        ],
        states={
            CHOOSING_PRODUK: [CallbackQueryHandler(choose_produk_callback)],
            INPUT_TUJUAN: [MessageHandler(Filters.text & ~Filters.command, input_tujuan_callback)],
            KONFIRMASI: [MessageHandler(Filters.text & ~Filters.command, konfirmasi_callback)],
            TOPUP_NOMINAL: [MessageHandler(Filters.text & ~Filters.command, topup_nominal_callback)],
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

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
