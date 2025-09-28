from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from markup import get_menu, produk_inline_keyboard, admin_edit_produk_keyboard, is_admin
from produk import get_produk_list, get_produk_by_kode, reset_produk_custom
from provider import cek_stock_akrab
from utils import format_stock_akrab, get_all_saldo

# Define states
CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, TOPUP_NOMINAL, ADMIN_EDIT = range(5)

def start(update, context):
    user = update.effective_user
    info_text, markup = get_menu(user.id)
    update.message.reply_text(
        info_text,
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )

def cancel(update, context):
    user = update.effective_user
    context.user_data.clear()
    info_text, markup = get_menu(user.id)
    update.message.reply_text(
        "Operasi dibatalkan.",
        reply_markup=markup
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
        info_text, markup = get_menu(user.id)
        query.edit_message_text("Kembali ke menu utama.", reply_markup=markup)
        return ConversationHandler.END

    # Main menu handlers
    if data == 'lihat_produk':
        produk_list = get_produk_list()
        msg = "<b>📦 Daftar Produk:</b>\n\n"
        for p in produk_list:
            status = "✅" if p.get("kuota", 0) > 0 else "❌"
            msg += f"{status} <code>{p['kode']}</code> | {p['nama']} | <b>Rp {p['harga']:,}</b> | Stok: {p['kuota']}\n"
        info_text, markup = get_menu(user.id)
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)
        return ConversationHandler.END

    elif data == 'beli_produk':
        query.edit_message_text(
            "🛒 Pilih produk yang ingin dibeli:", 
            reply_markup=produk_inline_keyboard()
        )
        context.user_data.clear()
        return CHOOSING_PRODUK

    elif data == 'stock_akrab':
        stock_data = cek_stock_akrab()
        msg = format_stock_akrab(stock_data)
        info_text, markup = get_menu(user.id)
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)
        return ConversationHandler.END

    elif data == 'lihat_saldo':
        saldo_dict = get_all_saldo()
        saldo = saldo_dict.get(user.id, 0)
        info_text, markup = get_menu(user.id)
        query.edit_message_text(f"💰 Saldo kamu: <b>Rp {saldo:,}</b>", parse_mode=ParseMode.HTML, reply_markup=markup)
        return ConversationHandler.END

    elif data == 'manajemen_produk' and is_admin(user.id):
        produk_list = get_produk_list()
        msg = "<b>📝 Manajemen Produk</b>\n\nPilih produk untuk edit:"
        keyboard = []
        for p in produk_list:
            keyboard.append([InlineKeyboardButton(f"{p['nama']} ({p['kode']})", callback_data=f"admin_edit_produk|{p['kode']}")])
        keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_admin")])
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        return ADMIN_EDIT

    elif data.startswith("admin_edit_produk|"):
        _, kode = data.split("|")
        produk = get_produk_by_kode(kode)
        if not produk:
            info_text, markup = get_menu(user.id)
            query.edit_message_text("❌ Produk tidak ditemukan.", reply_markup=markup)
            return ConversationHandler.END
        msg = f"<b>🛠 Edit Produk</b>\n\nKode: <code>{kode}</code>\nNama: <b>{produk['nama']}</b>\nHarga: <b>Rp {produk['harga']:,}</b>\nStok: {produk['kuota']}"
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=admin_edit_produk_keyboard(kode))
        return ADMIN_EDIT

    elif data.startswith("resetcustom|"):
        _, kode = data.split("|")
        reset_produk_custom(kode)
        info_text, markup = get_menu(user.id)
        query.edit_message_text(f"✅ Custom produk <code>{kode}</code> berhasil direset.", parse_mode=ParseMode.HTML, reply_markup=markup)
        return ConversationHandler.END

    # ... tambahkan elif handler lain sesuai kebutuhan menu kamu

    # Default: kembali ke menu utama
    info_text, markup = get_menu(user.id)
    query.edit_message_text("Kembali ke menu utama.", reply_markup=markup)
    return ConversationHandler.END
