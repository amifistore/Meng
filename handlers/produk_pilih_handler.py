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

    print(f"🔍 Callback data received: {data}")  # Debug log

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
                f"✅ Produk yang dipilih:\n<b>{p['kode']}</b> - {p['nama']}\nHarga: Rp {p['harga']:,}\nStok: {p['kuota']}\n\nSilakan input nomor tujuan:\n\nKetik /batal untuk membatalkan.",
                parse_mode=ParseMode.HTML
            )
            return INPUT_TUJUAN
        except (ValueError, IndexError) as e:
            print(f"❌ Error memilih produk: {e}")
            query.edit_message_text("❌ Error memilih produk.", reply_markup=get_menu(user.id))
            return ConversationHandler.END

    elif data == "back_main":
        query.edit_message_text("Kembali ke menu utama.", reply_markup=get_menu(user.id))
        return ConversationHandler.END

    else:
        print(f"❌ Callback tidak dikenali: {data}")
        query.edit_message_text("❌ Menu tidak dikenal.", reply_markup=get_menu(user.id))
        return ConversationHandler.END
