from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from markup import reply_main_menu, produk_inline_keyboard
from produk import get_produk_list
from saldo import get_saldo_user

CHOOSING_PRODUK, INPUT_TUJUAN = 0, 1

def produk_pilih_callback(update, context):
    query = update.callback_query
    user = query.from_user
    data = query.data

    try:
        query.answer()
    except Exception:
        pass

    # User klik tombol "Order Produk" di menu utama, atau callback "beli_produk"
    if data == "beli_produk":
        produk_list = get_produk_list()
        query.edit_message_text(
            "🛒 Pilih produk yang ingin dibeli:",
            reply_markup=produk_inline_keyboard(produk_list)
        )
        context.user_data.clear()
        return CHOOSING_PRODUK

    # User memilih produk, callback: produk_static|index
    if data.startswith("produk_static|"):
        try:
            idx = int(data.split("|")[1])
            produk_list = get_produk_list()
            if idx < 0 or idx >= len(produk_list):
                query.edit_message_text("❌ Produk tidak valid.", reply_markup=reply_main_menu(user.id))
                return ConversationHandler.END

            p = produk_list[idx]
            context.user_data["produk"] = p

            saldo = get_saldo_user(user.id)
            if saldo < p['harga']:
                query.edit_message_text(
                    f"❌ Saldo kamu tidak cukup untuk order produk ini.\n"
                    f"Produk: <b>{p['nama']}</b>\nHarga: Rp {p['harga']:,}\n"
                    f"Saldo kamu: Rp {saldo:,}\n\n"
                    "Silakan top up dahulu sebelum order.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_main_menu(user.id)
                )
                return ConversationHandler.END

            query.edit_message_text(
                f"✅ Produk yang dipilih:\n"
                f"<b>{p['kode']}</b> - {p['nama']}\n"
                f"Harga: Rp {p['harga']:,}\nStok: {p['kuota']}\n\n"
                "Silakan input nomor tujuan:\n\nKetik /batal untuk membatalkan.",
                parse_mode=ParseMode.HTML
            )
            return INPUT_TUJUAN
        except (ValueError, IndexError) as e:
            query.edit_message_text("❌ Error memilih produk.", reply_markup=reply_main_menu(user.id))
            return ConversationHandler.END

    elif data == "back_main":
        query.edit_message_text("Kembali ke menu utama.", reply_markup=reply_main_menu(user.id))
        return ConversationHandler.END

    else:
        query.edit_message_text("❌ Callback tidak dikenali.", reply_markup=reply_main_menu(user.id))
        return ConversationHandler.END
