from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from markup import main_menu_markup, get_menu, produk_inline_keyboard, admin_edit_produk_keyboard
from produk import get_produk_list, get_produk_by_kode, reset_produk_custom
from provider import cek_stock_akrab
from utils import format_stock_akrab
from config import ADMIN_IDS
from riwayat import get_user_riwayat
from saldo import tambah_saldo_user, get_saldo_user
import logging

logger = logging.getLogger(__name__)

# Define states
CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, TOPUP_NOMINAL, ADMIN_EDIT, TOPUP_CONFIRM = range(6)

def is_admin(user_id):
    """Cek apakah user adalah admin"""
    return user_id in ADMIN_IDS

def start(update, context):
    user = update.effective_user
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

    # Handle back buttons first
    if data in ["back_main", "back_menu"]:
        markup = main_menu_markup(is_admin(user.id))
        try:
            query.edit_message_text(
                "🏠 <b>Menu Utama</b>\nSilakan pilih menu berikut:",
                parse_mode=ParseMode.HTML,
                reply_markup=markup
            )
        except Exception as e:
            logger.warning(f"Error editing message: {e}")
            query.message.reply_text(
                "🏠 <b>Menu Utama</b>\nSilakan pilih menu berikut:",
                parse_mode=ParseMode.HTML,
                reply_markup=markup
            )
        return ConversationHandler.END

    elif data == "back_admin":
        if is_admin(user.id):
            markup = main_menu_markup(is_admin=True)
            query.edit_message_text(
                "🛠 <b>Admin Panel</b>\nSilakan pilih menu admin:",
                parse_mode=ParseMode.HTML,
                reply_markup=markup
            )
        else:
            markup = main_menu_markup(is_admin=False)
            query.edit_message_text(
                "Kembali ke menu utama.",
                reply_markup=markup
            )
        return ConversationHandler.END

    # 1. Order Produk
    if data == 'beli_produk':
        produk_list = get_produk_list()
        if not produk_list:
            query.edit_message_text(
                "❌ Tidak ada produk yang tersedia saat ini.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")]
                ])
            )
            return ConversationHandler.END
        
        keyboard = produk_inline_keyboard(produk_list)
        query.edit_message_text(
            "🛒 <b>Pilih Produk</b>\n\nSilakan pilih produk yang ingin dibeli:",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        context.user_data.clear()
        return CHOOSING_PRODUK

    # 2. Top Up Saldo
    elif data == 'topup':
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 50.000", callback_data="topup_nominal|50000"),
             InlineKeyboardButton("💰 100.000", callback_data="topup_nominal|100000")],
            [InlineKeyboardButton("💰 200.000", callback_data="topup_nominal|200000"),
             InlineKeyboardButton("💰 500.000", callback_data="topup_nominal|500000")],
            [InlineKeyboardButton("💳 Manual Transfer", callback_data="topup_manual")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")]
        ])
        query.edit_message_text(
            "💳 <b>Top Up Saldo</b>\n\nPilih nominal top up atau metode transfer:",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        return TOPUP_NOMINAL

    elif data.startswith("topup_nominal|"):
        try:
            nominal = int(data.split("|")[1])
            context.user_data["topup_nominal"] = nominal
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Konfirmasi Top Up", callback_data="topup_konfirm")],
                [InlineKeyboardButton("🔙 Ganti Nominal", callback_data="topup"),
                 InlineKeyboardButton("🏠 Menu Utama", callback_data="back_main")]
            ])
            
            query.edit_message_text(
                f"💳 <b>Konfirmasi Top Up</b>\n\n"
                f"Nominal: <b>Rp {nominal:,}</b>\n"
                f"Silakan konfirmasi untuk melanjutkan top up.",
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
                # Tambahkan saldo user
                tambah_saldo_user(user.id, nominal)
                
                # Dapatkan saldo terbaru
                saldo_sekarang = get_saldo_user(user.id)
                
                markup = main_menu_markup(is_admin(user.id))
                query.edit_message_text(
                    f"✅ <b>Top Up Berhasil!</b>\n\n"
                    f"Nominal: <b>Rp {nominal:,}</b>\n"
                    f"Saldo sekarang: <b>Rp {saldo_sekarang:,}</b>\n\n"
                    f"Terima kasih telah top up!",
                    parse_mode=ParseMode.HTML,
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"Error topup saldo: {e}")
                query.edit_message_text(
                    "❌ Gagal menambahkan saldo. Silakan hubungi admin.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Kembali", callback_data="topup")]
                    ])
                )
        else:
            query.edit_message_text("❌ Nominal topup tidak valid.")
        
        context.user_data.pop("topup_nominal", None)
        return ConversationHandler.END

    elif data == "topup_manual":
        query.edit_message_text(
            "💳 <b>Top Up Manual</b>\n\n"
            "Untuk top up manual, silakan transfer ke:\n\n"
            "📱 <b>Bank BCA</b>\n"
            "No. Rek: <code>1234567890</code>\n"
            "A/N: Nama Admin\n\n"
            "Setelah transfer, kirim bukti transfer ke admin untuk proses verifikasi.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Hubungi Admin", url="https://t.me/admin")],
                [InlineKeyboardButton("⬅️ Kembali", callback_data="topup")]
            ])
        )
        return ConversationHandler.END

    # 3. Cek Stok
    elif data == 'stock_akrab':
        query.edit_message_text("🔄 <b>Memuat data stok...</b>", parse_mode=ParseMode.HTML)
        
        try:
            stock_data = cek_stock_akrab()
            msg = format_stock_akrab(stock_data)
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh Stok", callback_data="stock_akrab")],
                [InlineKeyboardButton("⬅️ Menu Utama", callback_data="back_main")]
            ])
            
            query.edit_message_text(
                msg,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error cek stok: {e}")
            query.edit_message_text(
                "❌ <b>Gagal memuat data stok</b>\nSilakan coba lagi beberapa saat.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Coba Lagi", callback_data="stock_akrab")],
                    [InlineKeyboardButton("⬅️ Menu Utama", callback_data="back_main")]
                ])
            )
        return ConversationHandler.END

    # 4. Cek Saldo
    elif data == 'lihat_saldo':
        try:
            saldo = get_saldo_user(user.id)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Top Up Saldo", callback_data="topup")],
                [InlineKeyboardButton("📋 Riwayat Transaksi", callback_data="riwayat")],
                [InlineKeyboardButton("⬅️ Menu Utama", callback_data="back_main")]
            ])
            
            query.edit_message_text(
                f"💰 <b>Informasi Saldo</b>\n\n"
                f"Saldo Anda: <b>Rp {saldo:,}</b>\n\n"
                f"Lakukan top up jika saldo kurang.",
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error cek saldo: {e}")
            query.edit_message_text("❌ Gagal memuat saldo.")
        return ConversationHandler.END

    # 5. Riwayat Transaksi
    elif data == 'riwayat':
        try:
            riwayat = get_user_riwayat(user.id)
            msg = "<b>📋 Riwayat Transaksi</b>\n\n"
            
            if not riwayat:
                msg += "Belum ada riwayat transaksi."
            else:
                # Tampilkan 5 transaksi terakhir
                for r in riwayat[-5:]:
                    status_emoji = "✅" if r.get('status') == 'sukses' else "🔄" if r.get('status') == 'pending' else "❌"
                    msg += (f"{status_emoji} <code>{r.get('ref_id','-')}</code>\n"
                           f"📦 {r.get('kode','-')} | 📞 {r.get('tujuan','-')}\n"
                           f"💸 Rp {r.get('harga',0):,} | 📅 {r.get('tanggal','-')}\n"
                           f"Status: {r.get('status','-')}\n\n")
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="riwayat")],
                [InlineKeyboardButton("⬅️ Menu Utama", callback_data="back_main")]
            ])
            
            query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error memuat riwayat: {e}")
            query.edit_message_text("❌ Gagal memuat riwayat transaksi.")
        return ConversationHandler.END

    # 6. Cek Status Transaksi
    elif data == 'cek_status':
        query.edit_message_text(
            "🔍 <b>Cek Status Transaksi</b>\n\n"
            "Fitur ini sedang dalam pengembangan.\n"
            "Untuk cek status transaksi, silakan hubungi admin dengan menyertakan Ref ID transaksi Anda.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Hubungi Admin", url="https://t.me/admin")],
                [InlineKeyboardButton("⬅️ Menu Utama", callback_data="back_main")]
            ])
        )
        return ConversationHandler.END

    # 7. Bantuan
    elif data == "help":
        msg = (
            "❓ <b>Pusat Bantuan</b>\n\n"
            "📖 <b>Cara Penggunaan:</b>\n"
            "1. <b>Order Produk</b> - Pilih produk, masukkan nomor tujuan, konfirmasi\n"
            "2. <b>Top Up Saldo</b> - Pilih nominal, konfirmasi, saldo otomatis bertambah\n"
            "3. <b>Cek Stok</b> - Lihat ketersediaan produk\n"
            "4. <b>Riwayat</b> - Lihat history transaksi\n\n"
            "⚠️ <b>Jika mengalami kendala:</b>\n"
            "• Pastikan saldo mencukupi\n"
            "• Periksa nomor tujuan sudah benar\n"
            "• Screenshoot error dan hubungi admin\n\n"
            "📞 <b>Kontak Admin:</b> @admin"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Hubungi Admin", url="https://t.me/admin")],
            [InlineKeyboardButton("🛒 Order Produk", callback_data="beli_produk")],
            [InlineKeyboardButton("⬅️ Menu Utama", callback_data="back_main")]
        ])
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        return ConversationHandler.END

    # 8. Admin Panel
    elif data == "back_admin" and is_admin(user.id):
        # Tampilkan menu admin
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Kelola Produk", callback_data="manajemen_produk")],
            [InlineKeyboardButton("💰 Kelola Saldo", callback_data="kelola_saldo")],
            [InlineKeyboardButton("📊 Statistik", callback_data="statistik")],
            [InlineKeyboardButton("⬅️ Menu Utama", callback_data="back_main")]
        ])
        query.edit_message_text(
            "🛠 <b>Admin Panel</b>\n\nSilakan pilih menu admin:",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        return ADMIN_EDIT

    elif data == "manajemen_produk" and is_admin(user.id):
        produk_list = get_produk_list()
        msg = "<b>📝 Manajemen Produk</b>\n\nPilih produk untuk edit:\n\n"
        
        keyboard_buttons = []
        for p in produk_list:
            status = "✅" if p.get("kuota", 0) > 0 else "❌"
            kode_str = str(p['kode'])
            keyboard_buttons.append([InlineKeyboardButton(
                f"{status} {p['nama']} (Rp {p['harga']:,})", 
                callback_data=f"admin_edit_produk|{kode_str}"
            )])
        
        keyboard_buttons.append([InlineKeyboardButton("➕ Tambah Produk", callback_data="tambah_produk")])
        keyboard_buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_admin")])
        
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        return ADMIN_EDIT

    # Default handler - kembali ke menu utama
    markup = main_menu_markup(is_admin(user.id))
    query.edit_message_text(
        "🏠 <b>Menu Utama</b>\nSilakan pilih menu berikut:",
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )
    return ConversationHandler.END
