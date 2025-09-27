from telegram import ParseMode
from markup import get_menu, produk_inline_keyboard
from produk import get_produk_list

CHOOSING_PRODUK, INPUT_TUJUAN = 0, 1

def produk_pilih_callback(update, context):
    query = update.callback_query
    user = query.from_user
    data = query.data
    query.answer()
    
    if data.startswith("produk_static|"):
        try:
            idx = int(data.split("|")[1])
            produk_list = get_produk_list()
            if idx < 0 or idx >= len(produk_list):
                query.edit_message_text("❌ Produk tidak valid.", reply_markup=get_menu(user.id))
                return ConversationHandler.END
            
            p = produk_list[idx]
            context.user_data["produk"] = p
            query.edit_message_text(
                f"✅ Produk yang dipilih:\n<b>{p['kode']}</b> - {p['nama']}\nHarga: Rp {p['harga']:,}\nKuota: {p['kuota']}\n\nSilakan input nomor tujuan:\n\nKetik /batal untuk membatalkan.",
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
        query.edit_message_text("Menu tidak dikenal.", reply_markup=get_menu(user.id))
        return ConversationHandler.END
