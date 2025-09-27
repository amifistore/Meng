from telegram.constants import ParseMode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from markup import get_menu, produk_inline_keyboard, admin_edit_produk_keyboard, is_admin
from produk import get_produk_list, get_produk_by_kode, reset_produk_custom
from provider import cek_stock_akrab
from utils import format_stock_akrab, get_all_saldo

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
    except Exception as e:
        print(f"Error answering callback: {e}")

    if data in ["back_main", "back_admin"]:
        query.edit_message_text("Kembali ke menu utama.", reply_markup=get_menu(user.id))
        return ConversationHandler.END

    if data == 'lihat_produk':
        produk_list = get_produk_list()
        if not produk_list:
            msg = "<b>📦 Daftar Produk:</b>\n\nTidak ada produk tersedia."
        else:
            msg = "<b>📦 Daftar Produk:</b>\n\n"
            for p in produk_list:
                status = "✅" if p.get("kuota", 0) > 0 else "❌"
                msg += f"{status} <code>{p['kode']}</code> | {p['nama']} | <b>Rp {p['harga']:,}</b> | Stok: {p['kuota']}\n"
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
        return ConversationHandler.END

    elif data == 'beli_produk':
        query.edit_message_text(
            "🛒 Pilih produk yang ingin dibeli:",
            reply_markup=produk_inline_keyboard()
        )
        context.user_data.clear()
        return CHOOSING_PRODUK

    elif data == 'topup':
        query.edit_message_text(
            "💸 Masukkan nominal Top Up saldo (minimal 10.000):\n\nKetik /batal untuk membatalkan.",
            parse_mode=ParseMode.HTML
        )
        return TOPUP_NOMINAL

    elif data == 'cek_status':
        query.edit_message_text(
            "🔍 Kirim format: <code>CEK|refid</code>\nContoh: <code>CEK|TRX123456</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_menu(user.id)
        )
        return ConversationHandler.END

    elif data == 'riwayat':
        try:
            from handlers.riwayat_handler import riwayat_user
            riwayat_user(update, context)
        except Exception as e:
            print(f"❌ Error in riwayat: {e}")
            query.edit_message_text("❌ Error memuat riwayat.", reply_markup=get_menu(user.id))
        return ConversationHandler.END

    elif data == 'stock_akrab':
        try:
            raw = cek_stock_akrab()
            msg = format_stock_akrab(raw)
            query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
        except Exception as e:
            query.edit_message_text(f"❌ Error cek stock: {str(e)}", reply_markup=get_menu(user.id))
        return ConversationHandler.END

    elif data == 'semua_riwayat':
        if is_admin(user.id):
            try:
                from handlers.riwayat_handler import semua_riwayat
                semua_riwayat(update, context)
            except Exception as e:
                query.edit_message_text("❌ Error memuat semua riwayat.", reply_markup=get_menu(user.id))
        else:
            query.edit_message_text("❌ Akses ditolak.", reply_markup=get_menu(user.id))
        return ConversationHandler.END

    elif data == 'lihat_saldo':
        if is_admin(user.id):
            all_saldo = get_all_saldo()
            msg = "<b>💰 Saldo Semua User:</b>\n\n"
            for uid, s in all_saldo.items():
                msg += f"👤 User <code>{uid}</code>: <b>Rp {s:,}</b>\n"
            query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
        else:
            query.edit_message_text("❌ Akses ditolak.", reply_markup=get_menu(user.id))
        return ConversationHandler.END

    elif data == 'tambah_saldo':
        if is_admin(user.id):
            query.edit_message_text("💰 Kirim format: <code>TAMBAH|user_id|jumlah</code>",
                                    parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
        else:
            query.edit_message_text("❌ Akses ditolak.", reply_markup=get_menu(user.id))
        return ConversationHandler.END

    elif data == 'manajemen_produk':
        if is_admin(user.id):
            produk_list = get_produk_list()
            msg = "<b>📝 Manajemen Produk:</b>\n\n"
            keyboard = []
            if produk_list:
                for p in produk_list:
                    keyboard.append([InlineKeyboardButton(f"✏️ {p['kode']} | {p['nama']}", callback_data=f"admin_edit_produk|{p['kode']}")])
            keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_admin")])
            query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            query.edit_message_text("❌ Akses ditolak.", reply_markup=get_menu(user.id))
        return ConversationHandler.END

    elif data.startswith("admin_edit_produk|"):
        if is_admin(user.id):
            kode = data.split("|")[1]
            p = get_produk_by_kode(kode)
            if not p:
                query.edit_message_text("❌ Produk tidak ditemukan.", reply_markup=get_menu(user.id))
                return ConversationHandler.END
            msg = (f"<b>✏️ Edit Produk {p['kode']}:</b>\n\n"
                   f"📦 Nama: {p['nama']}\n"
                   f"💰 Harga: Rp {p['harga']:,}\n"
                   f"📊 Stok: {p['kuota']}\n"
                   f"📝 Deskripsi: {p['deskripsi']}\n\n"
                   "Pilih aksi edit di bawah:")
            query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=admin_edit_produk_keyboard(kode))
            context.user_data["edit_kode"] = kode
            return ADMIN_EDIT
        else:
            query.edit_message_text("❌ Akses ditolak.", reply_markup=get_menu(user.id))
            return ConversationHandler.END

    elif data.startswith("editharga|"):
        if is_admin(user.id):
            kode = data.split("|")[1]
            context.user_data["edit_kode"] = kode
            context.user_data["edit_field"] = "harga"
            query.edit_message_text(
                f"💰 Masukkan harga baru untuk produk <b>{kode}</b> (angka):\n\nKetik /batal untuk membatalkan.",
                parse_mode=ParseMode.HTML
            )
            return ADMIN_EDIT
        else:
            query.edit_message_text("❌ Akses ditolak.", reply_markup=get_menu(user.id))
            return ConversationHandler.END

    elif data.startswith("editdeskripsi|"):
        if is_admin(user.id):
            kode = data.split("|")[1]
            context.user_data["edit_kode"] = kode
            context.user_data["edit_field"] = "deskripsi"
            query.edit_message_text(
                f"📝 Masukkan deskripsi baru untuk produk <b>{kode}</b>:\n\nKetik /batal untuk membatalkan.",
                parse_mode=ParseMode.HTML
            )
            return ADMIN_EDIT
        else:
            query.edit_message_text("❌ Akses ditolak.", reply_markup=get_menu(user.id))
            return ConversationHandler.END

    elif data.startswith("resetcustom|"):
        if is_admin(user.id):
            kode = data.split("|")[1]
            ok = reset_produk_custom(kode)
            if ok:
                query.edit_message_text(f"✅ Sukses reset custom produk <b>{kode}</b> ke default.", parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
            else:
                query.edit_message_text(f"❌ Gagal reset custom produk <b>{kode}</b>.", parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
            return ConversationHandler.END
        else:
            query.edit_message_text("❌ Akses ditolak.", reply_markup=get_menu(user.id))
            return ConversationHandler.END

    else:
        print(f"❌ [MAIN_MENU] Callback tidak dikenali: '{data}'")
        return ConversationHandler.END

# ----------- Tambahkan handler lain di bawah ini sesuai kebutuhan ------------ #

def choose_produk_callback(update, context):
    # Isi sesuai logic pilih produk
    pass

def input_tujuan_callback(update, context):
    # Isi sesuai logic input tujuan
    pass

def konfirmasi_callback(update, context):
    # Isi sesuai logic konfirmasi
    pass

def topup_nominal_callback(update, context):
    # Isi sesuai logic topup
    pass

def admin_edit_produk_callback(update, context):
    # Isi sesuai logic edit produk oleh admin
    pass
