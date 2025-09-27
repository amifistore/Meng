from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, Filters
from handlers.main_menu_handler import main_menu_callback, cancel
from handlers.produk_pilih_handler import produk_pilih_callback
from handlers.input_tujuan_handler import input_tujuan_step
from handlers.konfirmasi_handler import konfirmasi_step
from handlers.topup_handler import topup_nominal_step
from handlers.admin_edit_produk_handler import admin_edit_produk_step

CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, TOPUP_NOMINAL, ADMIN_EDIT = range(5)

def get_conversation_handler():
    return ConversationHandler(
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
