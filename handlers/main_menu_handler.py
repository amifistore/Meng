from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from markup import get_menu, produk_inline_keyboard, admin_edit_produk_keyboard
from produk import get_produk_list, get_produk_by_kode, reset_produk_custom
from provider import cek_stock_akrab
from utils import format_stock_akrab, get_all_saldo
from config import ADMIN_IDS
from riwayat import get_user_riwayat
from saldo import tambah_saldo_user, kurang_saldo_user, get_saldo_user
import logging

logger = logging.getLogger(__name__)

# Define states
CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, TOPUP_NOMINAL, ADMIN_EDIT, TOPUP_CONFIRM = range(6)

def is_admin(user_id):
    """Cek apakah user adalah admin"""
    return user_id in ADMIN_IDS

def start(update, context):
    user = update.effective_user
    # PERBAIKAN: Pastikan get_menu return markup yang benar
    markup = get_menu(is_admin(user.id))
    update.message.reply_text(
        "Selamat datang! Silakan pilih menu:",
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )

def cancel(update, context):
    user = update.effective_user
    context.user_data.clear()
    markup = get_menu(is_admin(user.id))
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
    except Exception as e:
        logger.warning(f"Error answering callback: {e}")

    # Skip produk_static callbacks - mereka ditangani oleh handler lain
    if data.startswith("produk_static|"):
        print(f"ℹ️ [MAIN_MENU] Skipping produk_static callback: {data}")
        return ConversationHandler.END

    # Handle back buttons first
    if data in ["back_main", "back_menu", "back_admin"]:
        markup = get_menu(is_admin(user.id))
        try:
            query.edit_message_text("Kembali ke menu utama.", reply_markup=markup)
        except Exception as e:
            logger.warning(f"Error editing message: {e}")
            query.message.reply_text("Kembali ke menu utama.", reply_markup=markup)
        return ConversationHandler.END

    # 1. Daftar Produk
    if data == 'lihat_produk':
        produk_list = get_produk_list()
        msg = "<b>📦 Daftar Produk:</b>\n\n"
        for p in produk_list:
            status = "✅" if p.get("kuota", 0) > 0 else "❌"
            msg += f"{status} <code>{p['kode']}</code> | {p['nama']} | <b>Rp {p['harga']:,}</b> | Stok: {p['kuota']}\n"
        markup = get_menu(is_admin(user.id))
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)
        return ConversationHandler.END

    # 2. Beli Produk
    elif data == 'beli_produk':
        produk_list = get_produk_list()
        # PERBAIKAN: Pastikan produk_inline_keyboard menerima data yang benar
        keyboard = produk_inline_keyboard(produk_list)
        query.edit_message_text(
            "🛒 Pilih produk yang ingin dibeli:", 
            reply_markup=keyboard
        )
        context.user_data.clear()
        return CHOOSING_PRODUK

    # 3. Cek Stok
    elif data == 'stock_akrab':
        stock_data = cek_stock_akrab()
        msg = format_stock_akrab(stock_data)
        markup = get_menu(is_admin(user.id))
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)
        return ConversationHandler.END

    # 4. Cek Saldo
    elif data == 'lihat_saldo':
        saldo = get_saldo_user(user.id)
        markup = get_menu(is_admin(user.id))
        query.edit_message_text(f"💰 Saldo kamu: <b>Rp {saldo:,}</b>", parse_mode=ParseMode.HTML, reply_markup=markup)
        return ConversationHandler.END

    # 5. Topup Saldo
    elif data == 'topup':
        # PERBAIKAN: Gunakan InlineKeyboardMarkup yang benar
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("50.000", callback_data="topup_nominal|50000"),
             InlineKeyboardButton("100.000", callback_data="topup_nominal|100000")],
            [InlineKeyboardButton("200.000", callback_data="topup_nominal|200000"),
             InlineKeyboardButton("500.000", callback_data="topup_nominal|500000")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")]
        ])
        query.edit_message_text(
            "💳 Pilih nominal topup:",
            reply_markup=keyboard
        )
        return TOPUP_NOMINAL

    elif data.startswith("topup_nominal|"):
        try:
            nominal = int(data.split("|")[1])
            context.user_data["topup_nominal"] = nominal
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Konfirmasi", callback_data="topup_konfirm"),
                 InlineKeyboardButton("❌ Batalkan", callback_data="back_menu")]
            ])
            query.edit_message_text(
                f"Konfirmasi topup sebesar <b>Rp {nominal:,}</b>?",
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            return TOPUP_CONFIRM
        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing topup nominal: {e}")
            query.edit_message_text("❌ Nominal topup tidak valid.")
            return ConversationHandler.END

    elif data == "topup_konfirm":
        nominal = context.user_data.get("topup_nominal", 0)
        if nominal > 0:
            try:
                # PERBAIKAN: Pastikan fungsi tambah_saldo_user ada dan berfungsi
                tambah_saldo_user(user.id, nominal)
                markup = get_menu(is_admin(user.id))
                query.edit_message_text(
                    f"✅ Topup <b>Rp {nominal:,}</b> berhasil ditambahkan ke saldo Anda.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"Error topup saldo: {e}")
                query.edit_message_text("❌ Gagal menambahkan saldo.")
        else:
            query.edit_message_text("❌ Nominal topup tidak valid.")
        
        context.user_data.pop("topup_nominal", None)
        return ConversationHandler.END

    # 6. Riwayat Transaksi
    elif data == 'riwayat':
        riwayat = get_user_riwayat(user.id)
        msg = "<b>📋 Riwayat Transaksi:</b>\n\n"
        if not riwayat:
            msg += "Belum ada riwayat transaksi."
        else:
            for r in riwayat[-10:]:  # Tampilkan 10 transaksi terakhir
                msg += (f"🆔 <code>{r.get('ref_id','-')}</code> | "
                        f"{r.get('kode','-')} | {r.get('tujuan','-')} | "
                        f"Rp {r.get('harga',0):,} | {r.get('tanggal','-')} | "
                        f"Status: {r.get('status','-')}\n")
        markup = get_menu(is_admin(user.id))
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)
        return ConversationHandler.END

    # 7. Cek Status Transaksi
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
        keyboard_buttons = []
        for p in produk_list:
            # PERBAIKAN: Pastikan kode produk string
            kode_str = str(p['kode'])
            keyboard_buttons.append([InlineKeyboardButton(
                f"{p['nama']} ({p['kode']})", 
                callback_data=f"admin_edit_produk|{kode_str}"
            )])
        keyboard_buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_admin")])
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        return ADMIN_EDIT

    elif data.startswith("admin_edit_produk|") and is_admin(user.id):
        try:
            _, kode = data.split("|")
            produk = get_produk_by_kode(kode)
            if not produk:
                markup = get_menu(is_admin(user.id))
                query.edit_message_text("❌ Produk tidak ditemukan.", reply_markup=markup)
                return ConversationHandler.END
            
            msg = (f"<b>🛠 Edit Produk</b>\n\n"
                   f"Kode: <code>{kode}</code>\n"
                   f"Nama: <b>{produk['nama']}</b>\n"
                   f"Harga: <b>Rp {produk['harga']:,}</b>\n"
                   f"Stok: {produk['kuota']}")
            
            # PERBAIKAN: Pastikan admin_edit_produk_keyboard menerima string
            keyboard = admin_edit_produk_keyboard(str(kode))
            query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            return ADMIN_EDIT
        except Exception as e:
            logger.error(f"Error editing product: {e}")
            return ConversationHandler.END

    elif data.startswith("resetcustom|") and is_admin(user.id):
        try:
            _, kode = data.split("|")
            reset_produk_custom(kode)
            markup = get_menu(is_admin(user.id))
            query.edit_message_text(
                f"✅ Custom produk <code>{kode}</code> berhasil direset.", 
                parse_mode=ParseMode.HTML, 
                reply_markup=markup
            )
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Error reset custom: {e}")
            return ConversationHandler.END

    # 9. Help/Bantuan
    elif data == "help":
        msg = (
            "<b>❓ Bantuan</b>\n\n"
            "Menu dan fitur:\n"
            "• 🛒 Order Produk - Beli produk/voucher\n"
            "• 💳 Topup Saldo - Isi saldo akun\n"
            "• 🔍 Cek Status - Cek status transaksi\n"
            "• 📋 Riwayat - Lihat riwayat transaksi\n"
            "• 📦 Cek Stok - Lihat stok produk\n"
            "• 💰 Lihat Saldo - Cek saldo akun\n\n"
            "Hubungi admin jika ada kendala."
        )
        markup = get_menu(is_admin(user.id))
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)
        return ConversationHandler.END

    # Default: kembali ke menu utama
    markup = get_menu(is_admin(user.id))
    query.edit_message_text("Kembali ke menu utama.", reply_markup=markup)
    return ConversationHandler.END

# Handler untuk state yang tidak ditangani di main_menu_callback
def handle_choosing_produk(update, context):
    """Handle state CHOOSING_PRODUK"""
    query = update.callback_query
    # Implementasi handler untuk memilih produk
    pass

def handle_input_tujuan(update, context):
    """Handle state INPUT_TUJUAN"""
    # Implementasi handler untuk input tujuan
    pass

def handle_konfirmasi(update, context):
    """Handle state KONFIRMASI"""
    # Implementasi handler untuk konfirmasi
    pass
