import logging
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler
from config import TOKEN
from markup import get_menu
from handlers.main_menu_handler import main_menu_callback, start, cancel, CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, TOPUP_NOMINAL, ADMIN_EDIT
from handlers.produk_pilih_handler import produk_pilih_callback
from handlers.order_handler import handle_input_tujuan, handle_konfirmasi
from handlers.riwayat_handler import riwayat_user, semua_riwayat

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def error_handler(update, context):
    logger.error(f"Error: {context.error}", exc_info=context.error)
    if update and update.effective_user:
        update.effective_message.reply_text(
            "❌ Terjadi error sistem. Silakan coba lagi atau hubungi admin.",
            reply_markup=get_menu(update.effective_user.id)
        )

def main():
    # Create updater
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Conversation handler for product order
    order_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(produk_pilih_callback, pattern='^produk_static\|')],
        states={
            INPUT_TUJUAN: [MessageHandler(Filters.text & ~Filters.command, handle_input_tujuan)],
            KONFIRMASI: [MessageHandler(Filters.text & ~Filters.command, handle_konfirmasi)]
        },
        fallbacks=[CommandHandler('batal', cancel)],
        allow_reentry=True
    )
    
    # Main menu conversation handler
    main_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_PRODUK: [CallbackQueryHandler(main_menu_callback)],
            INPUT_TUJUAN: [MessageHandler(Filters.text & ~Filters.command, handle_input_tujuan)],
            KONFIRMASI: [MessageHandler(Filters.text & ~Filters.command, handle_konfirmasi)],
            TOPUP_NOMINAL: [MessageHandler(Filters.text & ~Filters.command, main_menu_callback)],
            ADMIN_EDIT: [MessageHandler(Filters.text & ~Filters.command, main_menu_callback)]
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('batal', cancel)]
    )
    
    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(main_menu_callback))
    dp.add_handler(order_conv_handler)
    dp.add_handler(main_conv_handler)
    
    # Error handler
    dp.add_error_handler(error_handler)
    
    # Start bot
    print("🤖 Bot started successfully!")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
