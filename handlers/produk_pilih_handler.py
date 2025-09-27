from telegram import ParseMode
from telegram.ext import ConversationHandler
from markup import get_menu
from produk import get_produk_by_kode, edit_produk

ADMIN_EDIT = 4

def admin_edit_produk_step(update, context):
    kode = context.user_data.get("edit_kode")
    field = context.user_data.get("edit_field")
    value = update.message.text.strip()
    
    if not kode or not field:
        update.message.reply_text(
            "❌ Kueri tidak valid. Silakan ulangi.",
            reply_markup=get_menu(update.effective_user.id)
        )
        return ADMIN_EDIT

    p = get_produk_by_kode(kode)
    if not p:
        update.message.reply_text(
            "❌ Produk tidak ditemukan.",
            reply_markup=get_menu(update.effective_user.id)
        )
        return ADMIN_EDIT

    try:
        if field == "harga":
            try:
                # Bersihkan format harga (hilangkan . dan ,)
                harga = int(value.replace(".", "").replace(",", ""))
                if harga <= 0:
                    raise ValueError("Harga harus lebih dari 0.")
                old_harga = p["harga"]
                edit_produk(kode, harga=harga)
                p_new = get_produk_by_kode(kode)
                update.message.reply_text(
                    f"✅ <b>Harga produk berhasil diupdate!</b>\n\n"
                    f"Produk: <b>{kode}</b> - {p_new['nama']}\n"
                    f"Harga lama: <s>Rp {old_harga:,}</s>\n"
                    f"Harga baru: <b>Rp {p_new['harga']:,}</b>\n"
                    f"Deskripsi: {p_new['deskripsi']}",
                    parse_mode="HTML",
                    reply_markup=get_menu(update.effective_user.id)
                )
            except ValueError as e:
                update.message.reply_text(
                    f"❌ Format harga tidak valid: {str(e)}\nSilakan masukkan lagi:",
                    parse_mode="HTML"
                )
                return ADMIN_EDIT
        
        elif field == "deskripsi":
            old_deskripsi = p["deskripsi"]
            edit_produk(kode, deskripsi=value)
            p_new = get_produk_by_kode(kode)
            update.message.reply_text(
                f"✅ <b>Deskripsi produk berhasil diupdate!</b>\n\n"
                f"Produk: <b>{kode}</b> - {p_new['nama']}\n"
                f"Deskripsi lama: <code>{old_deskripsi}</code>\n"
                f"Deskripsi baru: <b>{p_new['deskripsi']}</b>",
                parse_mode="HTML",
                reply_markup=get_menu(update.effective_user.id)
            )
        else:
            update.message.reply_text(
                "❌ Field tidak dikenal.",
                reply_markup=get_menu(update.effective_user.id)
            )
            return ADMIN_EDIT
    
    except Exception as e:
        update.message.reply_text(
            f"❌ <b>Gagal update produk!</b>\n"
            f"Produk: <b>{kode}</b> - {p['nama']}\n"
            f"Error: {str(e)}",
            parse_mode="HTML",
            reply_markup=get_menu(update.effective_user.id)
        )
        return ADMIN_EDIT
    
    finally:
        # Hapus sesi edit agar tidak nyangkut di user_data
        context.user_data.pop("edit_kode", None)
        context.user_data.pop("edit_field", None)
    
    return ConversationHandler.END
