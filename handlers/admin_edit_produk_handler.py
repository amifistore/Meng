from telegram import ParseMode
from telegram.ext import ConversationHandler
from markup import get_menu
from produk import get_produk_by_kode, edit_produk, reset_produk_custom

ADMIN_EDIT = 4

def admin_edit_produk_step(update, context):
    # Aman akses user_data
    kode = context.user_data.get("edit_kode")
    field = context.user_data.get("edit_field")
    value = update.message.text.strip() if update.message and update.message.text else ""

    if not kode or not field:
        update.message.reply_text(
            "❌ Kueri tidak valid. Silakan ulangi.",
            reply_markup=get_menu(getattr(update.effective_user, 'id', None))
        )
        return ConversationHandler.END

    p = get_produk_by_kode(kode)
    if not p:
        update.message.reply_text(
            "❌ Produk tidak ditemukan.",
            reply_markup=get_menu(getattr(update.effective_user, 'id', None))
        )
        return ConversationHandler.END

    try:
        if field == "harga":
            try:
                harga = int(value.replace(".", "").replace(",", ""))
                if harga <= 0:
                    raise ValueError("Harga harus lebih dari 0.")
                old_harga = p.get("harga", 0)
                edit_produk(kode, harga=harga)
                p_new = get_produk_by_kode(kode)
                update.message.reply_text(
                    f"✅ <b>Harga produk berhasil diupdate!</b>\n\n"
                    f"Produk: <b>{kode}</b> - {p_new.get('nama','-')}\n"
                    f"Harga lama: <s>Rp {old_harga:,}</s>\n"
                    f"Harga baru: <b>Rp {p_new.get('harga',0):,}</b>\n"
                    f"Deskripsi: {p_new.get('deskripsi','')}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_menu(getattr(update.effective_user, 'id', None))
                )
            except Exception as e:
                update.message.reply_text(
                    f"❌ Format harga tidak valid: {str(e)}\nSilakan masukkan lagi:",
                    parse_mode=ParseMode.HTML
                )
                return ADMIN_EDIT

        elif field == "deskripsi":
            old_deskripsi = p.get("deskripsi","")
            edit_produk(kode, deskripsi=value)
            p_new = get_produk_by_kode(kode)
            update.message.reply_text(
                f"✅ <b>Deskripsi produk berhasil diupdate!</b>\n\n"
                f"Produk: <b>{kode}</b> - {p_new.get('nama','-')}\n"
                f"Deskripsi lama: <code>{old_deskripsi}</code>\n"
                f"Deskripsi baru: <b>{p_new.get('deskripsi','')}</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=get_menu(getattr(update.effective_user, 'id', None))
            )

        elif field == "resetcustom":
            ok = reset_produk_custom(kode)
            if ok:
                update.message.reply_text(
                    f"✅ Sukses reset custom produk <b>{kode}</b> ke default.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_menu(getattr(update.effective_user, 'id', None))
                )
            else:
                update.message.reply_text(
                    f"❌ Gagal reset custom produk <b>{kode}</b>.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_menu(getattr(update.effective_user, 'id', None))
                )

        else:
            update.message.reply_text(
                "❌ Field tidak dikenal.",
                reply_markup=get_menu(getattr(update.effective_user, 'id', None))
            )

    except Exception as e:
        update.message.reply_text(
            f"❌ <b>Gagal update produk!</b>\n"
            f"Produk: <b>{kode}</b> - {p.get('nama','-')}\n"
            f"Error: {str(e)}",
            parse_mode=ParseMode.HTML,
            reply_markup=get_menu(getattr(update.effective_user, 'id', None))
        )

    finally:
        context.user_data.pop("edit_kode", None)
        context.user_data.pop("edit_field", None)

    return ConversationHandler.END
