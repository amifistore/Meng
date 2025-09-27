from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from markup import get_menu, produk_inline_keyboard, admin_edit_produk_keyboard, is_admin
from produk import get_produk_list, get_produk_by_kode, reset_produk_custom
from provider import cek_stock_akrab
from utils import format_stock_akrab, get_all_saldo

def start(update, context):
    user = update.effective_user
    update.message.reply_text(
        f"Halo <b>{user.first_name}</b>!\nGunakan menu di bawah.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_menu(user.id)
    )

def cancel(update, context):
    user = update.effective_user
    context.user_data.clear()
    update.message.reply_text(
        "Operasi dibatalkan.",
        reply_markup=get_menu(user.id)
    )
    return ConversationHandler.END

def main_menu_callback(update, context):
    query = update.callback_query
    user = query.from_user
    data = query.data

    print(f"🔍 [MAIN_MENU] Callback received: '{data}'")

    try:
        query.answer()
    except Exception:
        pass

    # **FIXED: Skip produk_static callbacks - mereka ditangani oleh handler lain**
    if data.startswith("produk_static|"):
        print(f"ℹ️ [MAIN_MENU] Skipping produk_static callback: {data}")
        return ConversationHandler.END

    # Handle back buttons first
    if data in ["back_main", "back_admin"]:
        query.edit_message_text("Kembali ke menu utama.", reply_markup=get_menu(user.id))
        return ConversationHandler.END

    # Main menu handlers
    if data == 'lihat_produk':
        produk_list = get_produk_list()
        msg = "<b>📦 Daftar Produk:</b>\n\n"
        for p in produk_list:
            status = "✅" if p.get("kuota", 0) > 0 else "❌"
            msg += f"{status} <code>{p['kode']}</code> | {p['nama']} | <b>Rp {p['harga']:,}</b> | Stok: {p['kuota']}\n"
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
        return ConversationHandler.END

    elif data == 'beli_produk':
        query.edit_message_text(
            "🛒 Pilih produk yang ingin dibeli:", 
            reply_markup=produk_inline_keyboard()
        )
        context.user_data.clear()
        return CHOOSING_PRODUK

    # ... (rest of the function remains the same)

# Define states
CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, TOPUP_NOMINAL, ADMIN_EDIT = range(5)
