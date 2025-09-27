from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    ConversationHandler
)
from handlers.main_menu_handler import main_menu_callback, start, cancel
from handlers.produk_pilih_handler import produk_pilih_callback

CHOOSING_PRODUK, INPUT_TUJUAN = range(2)

def main():
    import os
    TOKEN = os.environ.get("BOT_TOKEN") or "YOUR_BOT_TOKEN"

    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(main_menu_callback)],
        states={
            CHOOSING_PRODUK: [CallbackQueryHandler(produk_pilih_callback)],
            # tambahkan state lain jika perlu
        },
        fallbacks=[
            MessageHandler(Filters.regex('^(/batal|batal|cancel)$'), cancel),
            MessageHandler(Filters.command, cancel)
        ],
        allow_reentry=True
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(conv_handler)

    print("Bot is running ...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
