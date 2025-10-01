from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ConversationHandler
from markup import reply_main_menu, admin_edit_produk_keyboard
from produk import get_produk_by_kode, edit_produk, reset_produk_custom

ADMIN_EDIT = 4

async def admin_edit_produk_callback(update, context):  # ✅ TAMBAHKAN ASYNC
    query = update.callback_query
    user = query.from_user
    data = query.data
    if not data.startswith("admin_edit_produk|"):
        return ConversationHandler.END

    _, kode = data.split("|")
    produk = get_produk_by_kode(kode)
    if not produk:
        await query.edit_message_text("❌ Produk tidak ditemukan.", reply_markup=reply_main_menu(user.id))  # ✅ TAMBAHKAN AWAIT
        return ConversationHandler.END

    msg = (
        f"<b>🛠 Edit Produk</b>\n\n"
        f"Kode: <code>{kode}</code>\n"
        f"Nama: <b>{produk['nama']}</b>\n"
        f"Harga: <b>Rp {produk['harga']:,}</b>\n"
        f"Stok: {produk['kuota']}"
    )
    await query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=admin_edit_produk_keyboard(kode))  # ✅ TAMBAHKAN AWAIT
    return ADMIN_EDIT

async def admin_edit_harga_prompt(update, context):  # ✅ TAMBAHKAN ASYNC
    query = update.callback_query
    kode = query.data.split("|")[1]
    context.user_data["edit_kode"] = kode
    context.user_data["edit_field"] = "harga"
    await query.edit_message_text(f"Masukkan harga baru untuk <code>{kode}</code>:", parse_mode=ParseMode.HTML)  # ✅ TAMBAHKAN AWAIT
    return ADMIN_EDIT

async def admin_edit_deskripsi_prompt(update, context):  # ✅ TAMBAHKAN ASYNC
    query = update.callback_query
    kode = query.data.split("|")[1]
    context.user_data["edit_kode"] = kode
    context.user_data["edit_field"] = "deskripsi"
    await query.edit_message_text(f"Masukkan deskripsi baru untuk <code>{kode}</code>:", parse_mode=ParseMode.HTML)  # ✅ TAMBAHKAN AWAIT
    return ADMIN_EDIT

async def admin_edit_produk_step(update, context):  # ✅ TAMBAHKAN ASYNC
    kode = context.user_data.get("edit_kode")
    field = context.user_data.get("edit_field")
    value = update.message.text.strip() if update.message and update.message.text else ""

    if not kode or not field:
        await update.message.reply_text(  # ✅ TAMBAHKAN AWAIT
            "❌ Kueri tidak valid. Silakan ulangi.",
            reply_markup=reply_main_menu(getattr(update.effective_user, 'id', None))
        )
        return ConversationHandler.END

    p = get_produk_by_kode(kode)
    if not p:
        await update.message.reply_text(  # ✅ TAMBAHKAN AWAIT
            "❌ Produk tidak ditemukan.",
            reply_markup=reply_main_menu(getattr(update.effective_user, 'id', None))
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
                await update.message.reply_text(  # ✅ TAMBAHKAN AWAIT
                    f"✅ <b>Harga produk berhasil diupdate!</b>\n\n"
                    f"Produk: <b>{kode}</b> - {p_new.get('nama','-')}\n"
                    f"Harga lama: <s>Rp {old_harga:,}</s>\n"
                    f"Harga baru: <b>Rp {p_new.get('harga',0):,}</b>\n"
                    f"Deskripsi: {p_new.get('deskripsi','')}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_main_menu(getattr(update.effective_user, 'id', None))
                )
            except Exception as e:
                await update.message.reply_text(  # ✅ TAMBAHKAN AWAIT
                    f"❌ Format harga tidak valid: {str(e)}\nSilakan masukkan lagi:",
                    parse_mode=ParseMode.HTML
                )
                return ADMIN_EDIT

        elif field == "deskripsi":
            old_deskripsi = p.get("deskripsi","")
            edit_produk(kode, deskripsi=value)
            p_new = get_produk_by_kode(kode)
            await update.message.reply_text(  # ✅ TAMBAHKAN AWAIT
                f"✅ <b>Deskripsi produk berhasil diupdate!</b>\n\n"
                f"Produk: <b>{kode}</b> - {p_new.get('nama','-')}\n"
                f"Deskripsi lama: <code>{old_deskripsi}</code>\n"
                f"Deskripsi baru: <b>{p_new.get('deskripsi','')}</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=reply_main_menu(getattr(update.effective_user, 'id', None))
            )

        elif field == "resetcustom":
            ok = reset_produk_custom(kode)
            if ok:
                await update.message.reply_text(  # ✅ TAMBAHKAN AWAIT
                    f"✅ Sukses reset custom produk <b>{kode}</b> ke default.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_main_menu(getattr(update.effective_user, 'id', None))
                )
            else:
                await update.message.reply_text(  # ✅ TAMBAHKAN AWAIT
                    f"❌ Gagal reset custom produk <b>{kode}</b>.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_main_menu(getattr(update.effective_user, 'id', None))
                )

        else:
            await update.message.reply_text(  # ✅ TAMBAHKAN AWAIT
                "❌ Field tidak dikenal.",
                reply_markup=reply_main_menu(getattr(update.effective_user, 'id', None))
            )

    except Exception as e:
        await update.message.reply_text(  # ✅ TAMBAHKAN AWAIT
            f"❌ <b>Gagal update produk!</b>\n"
            f"Produk: <b>{kode}</b> - {p.get('nama','-')}\n"
            f"Error: {str(e)}",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_main_menu(getattr(update.effective_user, 'id', None))
        )

    finally:
        context.user_data.pop("edit_kode", None)
        context.user_data.pop("edit_field", None)

    return ConversationHandler.END
