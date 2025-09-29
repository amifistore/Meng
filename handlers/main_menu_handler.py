from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from markup import get_menu, produk_inline_keyboard, admin_edit_produk_keyboard
from produk import get_produk_list, get_produk_by_kode, reset_produk_custom
from provider import cek_stock_akrab
from utils import format_stock_akrab, get_all_saldo
from config import ADMIN_IDS
from riwayat import get_user_riwayat
from saldo import tambah_saldo_user, kurang_saldo_user, get_saldo_user

# Define states
CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, TOPUP_NOMINAL, ADMIN_EDIT, TOPUP_CONFIRM = range(6)

def is_admin(user_id):
    """Cek apakah user adalah admin"""
    return user_id in ADMIN_IDS

def start(update, context):
    user = update.effective_user
    info_text, markup = get_menu(is_admin(user.id))
    update.message.reply_text(
        info_text,
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )

def cancel(update, context):
    user = update.effective_user
    context.user_data.clear()
    info_text, markup = get_menu(is_admin(user.id))
    update.message.reply_text(
        "Operasi dibatalkan.",
        reply_markup=markup
    )
    return ConversationHandler.END

def main_menu_callback(update, context):
    query = update.callback_query
    user = query.from_user
    data = query.data

    print(f"🔍 [MAIN_MENU] Callback received: '{data}'")

    try:
        query.answer()
    except Exception:
        pass

    # Skip produk_static callbacks - mereka ditangani oleh handler lain
    if data.startswith("produk_static|"):
        print(f"ℹ️ [MAIN_MENU] Skipping produk_static callback: {data}")
        return ConversationHandler.END

    # Handle back buttons first
    if data in ["back_main", "back_admin"]:
        info_text, markup = get_menu(is_admin(user.id))
        query.edit_message_text("Kembali ke menu utama.", reply_markup=markup)
        return ConversationHandler.END

    # 1. Daftar Produk
    if data == 'lihat_produk':
        produk_list = get_produk_list()
        msg = "<b>📦 Daftar Produk:</b>\n\n"
        for p in produk_list:
            status = "✅" if p.get("kuota", 0) > 0 else "❌"
            msg += f"{status} <code>{p['kode']}</code> | {p['nama']} | <b>Rp {p['harga']:,}</b> | Stok: {p['kuota']}\n"
        info_text, markup = get_menu(is_admin(user.id))
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)
        return ConversationHandler.END

    # 2. Beli Produk
    elif data == 'beli_produk':
        produk_list = get_produk_list()
        query.edit_message_text(
            "🛒 Pilih produk yang ingin dibeli:", 
            reply_markup=produk_inline_keyboard(produk_list)
        )
        context.user_data.clear()
        return CHOOSING_PRODUK

    # 3. Cek Stok
    elif data == 'stock_akrab':
        stock_data = cek_stock_akrab()
        msg = format_stock_akrab(stock_data)
        info_text, markup = get_menu(is_admin(user.id))
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)
        return ConversationHandler.END

    # 4. Cek Saldo
    elif data == 'lihat_saldo':
        saldo = get_saldo_user(user.id)
        info_text, markup = get_menu(is_admin(user.id))
        query.edit_message_text(f"💰 Saldo kamu: <b>Rp {saldo:,}</b>", parse_mode=ParseMode.HTML, reply_markup=markup)
        return ConversationHandler.END

    # 5. Topup Saldo
    elif data == 'topup':
        query.edit_message_text(
            "💳 Pilih nominal topup:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("50.000", callback_data="topup_nominal|50000"),
                 InlineKeyboardButton("100.000", callback_data="topup_nominal|100000")],
                [InlineKeyboardButton("200.000", callback_data="topup_nominal|200000"),
                 InlineKeyboardButton("500.000", callback_data="topup_nominal|500000")],
                [InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")]
            ])
        )
        return TOPUP_NOMINAL

    elif data.startswith("topup_nominal|"):
        nominal = int(data.split("|")[1])
        context.user_data["topup_nominal"] = nominal
        query.edit_message_text(
            f"Konfirmasi topup sebesar <b>Rp {nominal:,}</b>?",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Konfirmasi", callback_data="topup_konfirm"),
                 InlineKeyboardButton("❌ Batalkan", callback_data="back_menu")]
            ])
        )
        return TOPUP_CONFIRM

    elif data == "topup_konfirm":
        nominal = context.user_data.get("topup_nominal", 0)
        if nominal > 0:
            # Simulasi langsung tambah saldo (replace dengan proses topup riil jika perlu)
            tambah_saldo_user(user.id, nominal, "topup", "Topup via bot")
            info_text, markup = get_menu(is_admin(user.id))
            query.edit_message_text(
                f"✅ Topup <b>Rp {nominal:,}</b> berhasil ditambahkan ke saldo Anda.",
                parse_mode=ParseMode.HTML,
                reply_markup=markup
            )
        else:
            query.edit_message_text("❌ Nominal topup tidak valid.", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")]]
            ))
        context.user_data.pop("topup_nominal", None)
        return ConversationHandler.END

    # 6. Riwayat Transaksi
    elif data == 'riwayat':
        riwayat = get_user_riwayat(user.id)
        msg = "<b>📋 Riwayat Transaksi:</b>\n\n"
        if not riwayat:
            msg += "Belum ada riwayat transaksi."
        else:
            for r in riwayat:
                msg += (f"🆔 <code>{r.get('ref_id','-')}</code> | "
                        f"{r.get('kode','-')} | {r.get('tujuan','-')} | "
                        f"{r.get('harga',0):,} | {r.get('tanggal','-')} | "
                        f"Status: {r.get('status','-')}\n")
        info_text, markup = get_menu(is_admin(user.id))
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)
        return ConversationHandler.END

    # 7. Cek Status Transaksi (dummy, sesuaikan dengan handler status riil)
    elif data == 'cek_status':
        query.edit_message_text(
            "🔍 Untuk cek status transaksi, silakan masukkan Ref ID pada menu status.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")]
            ]),
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

    # 8. Manajemen Produk Admin
    elif data == 'manajemen_produk' and is_admin(user.id):
        produk_list = get_produk_list()
        msg = "<b>📝 Manajemen Produk</b>\n\nPilih produk untuk edit:"
        keyboard = []
        for p in produk_list:
            keyboard.append([InlineKeyboardButton(f"{p['nama']} ({p['kode']})", callback_data=f"admin_edit_produk|{p['kode']}")])
        keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_admin")])
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        return ADMIN_EDIT

    elif data.startswith("admin_edit_produk|") and is_admin(user.id):
        _, kode = data.split("|")
        produk = get_produk_by_kode(kode)
        if not produk:
            info_text, markup = get_menu(is_admin(user.id))
            query.edit_message_text("❌ Produk tidak ditemukan.", reply_markup=markup)
            return ConversationHandler.END
        msg = (f"<b>🛠 Edit Produk</b>\n\nKode: <code>{kode}</code>\nNama: <b>{produk['nama']}</b>\n"
               f"Harga: <b>Rp {produk['harga']:,}</b>\nStok: {produk['kuota']}")
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=admin_edit_produk_keyboard(kode))
        return ADMIN_EDIT

    elif data.startswith("resetcustom|") and is_admin(user.id):
        _, kode = data.split("|")
        reset_produk_custom(kode)
        info_text, markup = get_menu(is_admin(user.id))
        query.edit_message_text(f"✅ Custom produk <code>{kode}</code> berhasil direset.", parse_mode=ParseMode.HTML, reply_markup=markup)
        return ConversationHandler.END

    # 9. Tambah Saldo User (admin)
    elif data == "tambah_saldo" and is_admin(user.id):
        # Dummy: balas info dan instruksi
        query.edit_message_text(
            "Masukkan user ID dan nominal saldo yang ingin ditambahkan via command /tambahsaldo <user_id> <nominal>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Kembali", callback_data="back_admin")]
            ]),
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

    # 10. Help/Bantuan
    elif data == "help":
        msg = (
            "<b>❓ Bantuan</b>\n\n"
            "Menu dan fitur:\n"
            "• Order Produk\n"
            "• Topup Saldo\n"
            "• Cek Status\n"
            "• Lihat Riwayat\n"
            "• Cek Stok\n"
            "• Manajemen Saldo (Admin)\n"
            "• Admin Panel\n\n"
            "Hubungi admin jika ada kendala."
        )
        info_text, markup = get_menu(is_admin(user.id))
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)
        return ConversationHandler.END

    # Default: kembali ke menu utama
    info_text, markup = get_menu(is_admin(user.id))
    query.edit_message_text("Kembali ke menu utama.", reply_markup=markup)
    return ConversationHandler.END
