from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from markup import get_menu, produk_inline_keyboard, admin_edit_produk_keyboard, is_admin
from produk import get_produk_list, get_produk_by_kode
from provider import cek_stock_akrab
from utils import get_user_saldo, set_user_saldo, format_stock_akrab
from handlers.riwayat_handler import riwayat_user, semua_riwayat

CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, TOPUP_NOMINAL, ADMIN_EDIT = range(5)

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

    try:
        query.answer()
    except Exception:
        pass

    if data == 'lihat_produk':
        produk_list = get_produk_list()
        msg = "<b>Daftar Produk:</b>\n"
        for p in produk_list:
            msg += f"<code>{p['kode']}</code> | {p['nama']} | <b>Rp {p['harga']:,}</b> | Kuota: {p['kuota']}\n"
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
        return ConversationHandler.END

    elif data == 'beli_produk':
        query.edit_message_text(
            "Pilih produk yang ingin dibeli:",
            reply_markup=produk_inline_keyboard()
        )
        context.user_data.clear()
        return CHOOSING_PRODUK  # <--- FIX! Harus ke state produk!

    elif data == 'topup':
        query.edit_message_text(
            "Masukkan nominal Top Up saldo yang diinginkan (minimal 10.000):\n\nKetik /batal untuk membatalkan.",
            parse_mode=ParseMode.HTML
        )
        return TOPUP_NOMINAL

    elif data == 'cek_status':
        query.edit_message_text(
            "Kirim format: <code>CEK|refid</code>\nContoh: <code>CEK|TRX123456</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_menu(user.id)
        )
        return ConversationHandler.END

    elif data == 'riwayat':
        riwayat_user(query, context)
        return ConversationHandler.END

    elif data == 'stock_akrab':
        try:
            raw = cek_stock_akrab()
            msg = format_stock_akrab(raw)
            if isinstance(msg, str) and msg.strip().lower().startswith("<html"):
                msg = "❌ Provider membalas data tidak valid."
            query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
        except Exception as e:
            query.edit_message_text(f"❌ Error cek stock: {str(e)}", parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
        return ConversationHandler.END

    elif data == 'semua_riwayat' and is_admin(user.id):
        semua_riwayat(query, context)
        return ConversationHandler.END

    elif data == 'lihat_saldo' and is_admin(user.id):
        from utils import get_all_saldo
        all_saldo = get_all_saldo()
        msg = "<b>Saldo semua user:</b>\n"
        for uid, s in all_saldo.items():
            msg += f"User <code>{uid}</code>: <b>Rp {s:,}</b>\n"
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
        return ConversationHandler.END

    elif data == 'tambah_saldo' and is_admin(user.id):
        query.edit_message_text("Kirim format: <code>TAMBAH|user_id|jumlah</code>", parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
        return ConversationHandler.END

    elif data == 'manajemen_produk' and is_admin(user.id):
        produk_list = get_produk_list()
        msg = "<b>Manajemen Produk:</b>\n"
        keyboard = []
        for p in produk_list:
            keyboard.append([InlineKeyboardButton(f"{p['kode']} | {p['nama']}", callback_data=f"admin_edit_produk|{p['kode']}")])
        keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_admin")])
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

    elif data.startswith("admin_edit_produk|") and is_admin(user.id):
        kode = data.split("|")[1]
        p = get_produk_by_kode(kode)
        if not p:
            query.edit_message_text("Produk tidak ditemukan.", reply_markup=get_menu(user.id))
            return ConversationHandler.END
        msg = (f"<b>Edit Produk {p['kode']}:</b>\n"
               f"Nama: {p['nama']}\nHarga: Rp {p['harga']:,}\nKuota: {p['kuota']}\nDeskripsi: {p['deskripsi']}\n\n"
               "Pilih aksi edit di bawah:")
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=admin_edit_produk_keyboard(kode))
        context.user_data["edit_kode"] = kode
        return ADMIN_EDIT

    elif data.startswith("editharga|") and is_admin(user.id):
        kode = data.split("|")[1]
        context.user_data["edit_kode"] = kode
        context.user_data["edit_field"] = "harga"
        query.edit_message_text(
            f"Masukkan harga baru untuk produk <b>{kode}</b> (angka):\n\nKetik /batal untuk membatalkan.",
            parse_mode=ParseMode.HTML
        )
        return ADMIN_EDIT

    elif data.startswith("editdeskripsi|") and is_admin(user.id):
        kode = data.split("|")[1]
        context.user_data["edit_kode"] = kode
        context.user_data["edit_field"] = "deskripsi"
        query.edit_message_text(
            f"Masukkan deskripsi baru untuk produk <b>{kode}</b>:\n\nKetik /batal untuk membatalkan.",
            parse_mode=ParseMode.HTML
        )
        return ADMIN_EDIT

    elif data.startswith("resetcustom|") and is_admin(user.id):
        from produk import reset_produk_custom
        kode = data.split("|")[1]
        ok = reset_produk_custom(kode)
        if ok:
            query.edit_message_text(f"✅ Sukses reset custom produk <b>{kode}</b> ke default.", parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
        else:
            query.edit_message_text(f"❌ Gagal reset custom produk <b>{kode}</b>.", parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
        return ConversationHandler.END

    elif data == "back_admin":
        query.edit_message_text("Kembali ke menu admin.", reply_markup=get_menu(user.id))
        return ConversationHandler.END

    elif data == "back_main":
        query.edit_message_text("Kembali ke menu utama.", reply_markup=get_menu(user.id))
        return ConversationHandler.END

    else:
        query.edit_message_text(f"Menu tidak dikenal. Callback: <code>{data}</code>", parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
        return ConversationHandler.END
