from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from markup import reply_main_menu, admin_panel_keyboard

def admin_panel_callback(update, context):
    user = update.effective_user
    msg = (
        "🛠 <b>Admin Panel</b>\n\n"
        "Silakan pilih fitur admin di bawah:"
    )
    # Gunakan message jika tersedia, fallback ke edit_message_text jika callback
    if getattr(update, 'message', None):
        update.message.reply_text(
            msg,
            parse_mode=ParseMode.HTML,
            reply_markup=admin_panel_keyboard()
        )
    else:
        update.callback_query.edit_message_text(
            msg,
            parse_mode=ParseMode.HTML,
            reply_markup=admin_panel_keyboard()
        )
