from telegram import Update
from telegram.ext import CallbackContext
from markup import get_menu

def cek_status_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    query.edit_message_text(
        "🔎 Silakan kirim kode/ID transaksi (refid) yang ingin dicek statusnya.",
        reply_markup=get_menu(user_id)
    )
