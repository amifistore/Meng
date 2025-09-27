from telegram import ParseMode
from telegram.ext import ConversationHandler
from markup import get_menu, produk_inline_keyboard

CHOOSING_PRODUK, INPUT_TUJUAN = range(2)

def start(update, context):
    user = update.effective_user
    update.message.reply_text(
        f"Halo <b>{user.first_name}</b>!\nGunakan menu di bawah.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_menu(user.id)
    )

def cancel(update, context):
    context.user_data.clear()
    update.message.reply_text(
        "Operasi dibatalkan.",
        reply_markup=get_menu(update.effective_user.id)
    )
    return ConversationHandler.END

def main_menu_callback(update, context):
    query = update.callback_query
    data = query.data

    try:
        query.answer()
    except Exception:
        pass

    if data == 'beli_produk':
        query.edit_message_text(
            "Pilih produk yang ingin dibeli:",
            reply_markup=produk_inline_keyboard()
        )
        context.user_data.clear()
        return CHOOSING_PRODUK  # INI FIXNYA! HARUS RETURN STATE PRODUK!

    else:
        query.edit_message_text(
            f"Menu tidak dikenal. Callback: <code>{data}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_menu(query.from_user.id)
        )
        return ConversationHandler.END
