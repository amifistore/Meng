from telegram import ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    ConversationHandler
)

# Import handler dari file lain atau definisikan langsung di sini
from handlers.main_menu_handler import start, cancel, main_menu_callback
from handlers.produk_pilih_handler import produk_pilih_callback
from handlers.input_tujuan_handler import input_tujuan_step
from handlers.konfirmasi_handler import konfirmasi_step
from handlers.topup_handler import topup_nominal_step
from handlers.admin_edit_produk_handler import admin_edit_produk_step
from handlers.text_handler import handle_text

CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, TOPUP_NOMINAL, ADMIN_EDIT = range(5)

def main():
    import os

    # Ganti dengan token bot kamu
    TOKEN = os.environ.get("BOT_TOKEN") or "YOUR_BOT_TOKEN"

    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(main_menu_callback)],
        states={
            CHOOSING_PRODUK: [CallbackQueryHandler(produk_pilih_callback)],
            INPUT_TUJUAN: [MessageHandler(Filters.text & ~Filters.command, input_tujuan_step)],
            KONFIRMASI: [MessageHandler(Filters.text & ~Filters.command, konfirmasi_step)],
            TOPUP_NOMINAL: [MessageHandler(Filters.text & ~Filters.command, topup_nominal_step)],
            ADMIN_EDIT: [MessageHandler(Filters.text & ~Filters.command, admin_edit_produk_step)],
        },
        fallbacks=[
            MessageHandler(Filters.regex('^(/batal|batal|BATAL|cancel)$'), cancel),
            MessageHandler(Filters.command, cancel)
        ],
        allow_reentry=True
    )

    # Command /start
    dp.add_handler(CommandHandler("start", start))
    # Conversation (all menu via inline button)
    dp.add_handler(conv_handler)
    # Handle text bebas di luar conversation
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    print("Bot is running ...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
