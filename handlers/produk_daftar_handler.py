from telegram import Update
from telegram.ext import CallbackContext
from markup import produk_inline_keyboard, get_menu

def lihat_produk_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    query.edit_message_text(
        "📦 Berikut daftar produk yang tersedia:",
        reply_markup=produk_inline_keyboard()
    )
