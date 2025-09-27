import json
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

def load_token_from_config():
    with open("config.json", "r") as f:
        data = json.load(f)
        return data["TOKEN"]

def main():
    TOKEN = load_token_from_config()

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
