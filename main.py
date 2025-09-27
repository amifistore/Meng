from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    ConversationHandler, 
    filters
)
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
    from telegram import Bot
    TOKEN = os.environ.get("BOT_TOKEN") or "YOUR_BOT_TOKEN"
    application = Application.builder().token(TOKEN).build()

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(main_menu_callback)],
        states={
            CHOOSING_PRODUK: [CallbackQueryHandler(produk_pilih_callback)],
            INPUT_TUJUAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_tujuan_step)],
            KONFIRMASI: [MessageHandler(filters.TEXT & ~filters.COMMAND, konfirmasi_step)],
            TOPUP_NOMINAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, topup_nominal_step)],
            ADMIN_EDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_edit_produk_step)],
        },
        fallbacks=[
            MessageHandler(filters.Regex('^(/batal|batal|BATAL|cancel)$'), cancel),
            MessageHandler(filters.COMMAND, cancel)
        ],
        allow_reentry=True
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
