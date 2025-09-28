from telegram import ParseMode
from telegram.ext import ConversationHandler
from markup import get_menu, produk_inline_keyboard
from produk import get_produk_list
from saldo import get_saldo_user  # Gunakan saldo.py agar konsisten DB

CHOOSING_PRODUK, INPUT_TUJUAN = 0, 1

def produk_pilih_callback(update, context):
    query = update.callback_query
    user = query.from_user
    data = query.data

    try:
        query.answer()
    except Exception:
        pass

    # Handle 'beli_produk' callback
    if data == "beli_produk":
        # Tampilkan daftar produk untuk dipilih
        query.edit_message_text(
            "🛒 Pilih produk yang ingin dibeli:",
            reply_markup=produk_inline_keyboard()
        )
        context.user_data.clear()
        return CHOOSING_PRODUK

    if data.startswith("produk_static|"):
        try:
            idx = int(data.split("|")[1])
            produk_list = get_produk_list()
            if idx < 0 or idx >= len(produk_list):
                query.edit_message_text("❌ Produk tidak valid.", reply_markup=get_menu(user.id))
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
                    reply_markup=get_menu(user.id)
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
            query.edit_message_text("❌ Error memilih produk.", reply_markup=get_menu(user.id))
            return ConversationHandler.END

    elif data == "back_main":
        query.edit_message_text("Kembali ke menu utama.", reply_markup=get_menu(user.id))
        return ConversationHandler.END

    else:
        # Callback tidak dikenali
        return ConversationHandler.END
