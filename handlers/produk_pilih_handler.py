from telegram import ParseMode
from telegram.ext import ConversationHandler
from markup import get_menu
from produk import get_produk_list
from utils import get_user_saldo

CHOOSING_PRODUK, INPUT_TUJUAN = 0, 1

def produk_pilih_callback(update, context):
    query = update.callback_query
    user = query.from_user
    data = query.data

    try:
        query.answer()
    except Exception:
        pass

    if data.startswith("produk_static|"):
        try:
            idx = int(data.split("|")[1])
            produk_list = get_produk_list()
            if idx < 0 or idx >= len(produk_list):
                query.edit_message_text("❌ Produk tidak valid.", reply_markup=get_menu(user.id))
                return ConversationHandler.END

            p = produk_list[idx]
            context.user_data["produk"] = p

            saldo = get_user_saldo(user.id)
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
                f"✅ Produk yang dipilih:\n<b>{p['kode']}</b> - {p['nama']}\n"
                f"Harga: Rp {p['harga']:,}\nKuota: {p.get('kuota', p.get('sisa_slot', 0))}\n\n"
                "Silakan input nomor tujuan:\n\nKetik /batal untuk membatalkan.",
                parse_mode=ParseMode.HTML
            )
            return INPUT_TUJUAN
        except Exception as e:
            query.edit_message_text(f"❌ Error memilih produk: {e}", reply_markup=get_menu(user.id))
            return ConversationHandler.END

    else:
        query.edit_message_text(
            f"Menu tidak dikenal. Callback: <code>{data}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_menu(user.id)
        )
        return ConversationHandler.END
