from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from markup import main_menu_markup, get_menu  # Pastikan import main_menu_markup

def start(update, context):
    user = update.effective_user
    
    # Kirim BOTH: Reply Keyboard (bawah chat) DAN Inline Keyboard (dalam pesan)
    reply_markup = get_menu(is_admin(user.id))  # Untuk keyboard bawah
    inline_markup = main_menu_markup(is_admin(user.id))  # Untuk keyboard dalam pesan
    
    # Kirim pesan dengan inline keyboard
    update.message.reply_text(
        "🏠 <b>Menu Utama Bot</b>\n\n"
        "Silakan pilih menu di bawah ini:",
        parse_mode=ParseMode.HTML,
        reply_markup=inline_markup  # INI YANG PENTING!
    )
    
    # Juga set reply keyboard untuk kemudahan akses
    update.message.reply_text(
        "Atau gunakan menu cepat di bawah:",
        reply_markup=reply_markup
    )

def main_menu_callback(update, context):
    query = update.callback_query
    user = query.from_user
    data = query.data

    print(f"🔍 [MAIN_MENU] Callback received: '{data}'")

    try:
        query.answer()
    except Exception as e:
        print(f"Warning: {e}")

    # Handle semua callback data
    if data in ["back_main", "back_menu"]:
        # Kembali ke menu utama dengan INLINE keyboard
        markup = main_menu_markup(is_admin(user.id))
        query.edit_message_text(
            "🏠 <b>Menu Utama</b>\n\nSilakan pilih menu berikut:",
            parse_mode=ParseMode.HTML,
            reply_markup=markup
        )
        return ConversationHandler.END

    elif data == "back_admin":
        if is_admin(user.id):
            markup = main_menu_markup(is_admin=True)
            query.edit_message_text(
                "🛠 <b>Admin Panel</b>\n\nSilakan pilih menu admin:",
                parse_mode=ParseMode.HTML,
                reply_markup=markup
            )
        return ConversationHandler.END

    # ORDER PRODUK
    elif data == 'beli_produk':
        from produk import get_produk_list
        from markup import produk_inline_keyboard
        
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

    # TOP UP SALDO
    elif data == 'topup':
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 50.000", callback_data="topup_nominal|50000"),
             InlineKeyboardButton("💰 100.000", callback_data="topup_nominal|100000")],
            [InlineKeyboardButton("💰 200.000", callback_data="topup_nominal|200000"),
             InlineKeyboardButton("💰 500.000", callback_data="topup_nominal|500000")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")]
        ])
        query.edit_message_text(
            "💳 <b>Top Up Saldo</b>\n\nPilih nominal top up:",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        return TOPUP_NOMINAL

    # CEK STOK
    elif data == 'stock_akrab':
        from provider import cek_stock_akrab
        from utils import format_stock_akrab
        
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
            print(f"Error cek stok: {e}")
            query.edit_message_text(
                "❌ Gagal memuat data stok.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Coba Lagi", callback_data="stock_akrab")],
                    [InlineKeyboardButton("⬅️ Menu Utama", callback_data="back_main")]
                ])
            )
        return ConversationHandler.END

    # LIHAT SALDO
    elif data == 'lihat_saldo':
        from saldo import get_saldo_user
        
        try:
            saldo = get_saldo_user(user.id)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Top Up", callback_data="topup")],
                [InlineKeyboardButton("⬅️ Menu Utama", callback_data="back_main")]
            ])
            
            query.edit_message_text(
                f"💰 <b>Saldo Anda</b>\n\n"
                f"Saldo: <b>Rp {saldo:,}</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Error cek saldo: {e}")
            query.edit_message_text("❌ Gagal memuat saldo.")
        return ConversationHandler.END

    # RIWAYAT TRANSAKSI
    elif data == 'riwayat':
        from riwayat import get_user_riwayat
        
        try:
            riwayat = get_user_riwayat(user.id)
            msg = "<b>📋 Riwayat Transaksi</b>\n\n"
            
            if not riwayat:
                msg += "Belum ada riwayat transaksi."
            else:
                for r in riwayat[-5:]:  # 5 transaksi terakhir
                    status = r.get('status', 'unknown')
                    msg += f"📦 {r.get('kode','-')} | {r.get('tujuan','-')}\n"
                    msg += f"💸 Rp {r.get('harga',0):,} | {r.get('tanggal','-')}\n"
                    msg += f"Status: {status}\n\n"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="riwayat")],
                [InlineKeyboardButton("⬅️ Menu Utama", callback_data="back_main")]
            ])
            
            query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        except Exception as e:
            print(f"Error riwayat: {e}")
            query.edit_message_text("❌ Gagal memuat riwayat.")
        return ConversationHandler.END

    # BANTUAN
    elif data == "help":
        msg = (
            "❓ <b>Pusat Bantuan</b>\n\n"
            "📖 <b>Cara Penggunaan:</b>\n"
            "• <b>Order Produk</b> - Beli produk/voucher\n"
            "• <b>Top Up Saldo</b> - Isi saldo akun\n"
            "• <b>Cek Stok</b> - Lihat ketersediaan produk\n"
            "• <b>Riwayat</b> - Lihat history transaksi\n\n"
            "📞 <b>Kontak Admin:</b> @admin"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Order Produk", callback_data="beli_produk")],
            [InlineKeyboardButton("⬅️ Menu Utama", callback_data="back_main")]
        ])
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        return ConversationHandler.END

    # Default: kembali ke menu utama
    markup = main_menu_markup(is_admin(user.id))
    query.edit_message_text(
        "🏠 <b>Menu Utama</b>\n\nSilakan pilih menu berikut:",
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )
    return ConversationHandler.END
