from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from markup import get_menu

INPUT_TUJUAN, KONFIRMASI = 1, 2

def input_tujuan_step(update, context):
    tujuan = update.message.text.strip()
    # Validasi nomor tujuan: minimal 9 digit, maksimal 15 digit, hanya angka
    if not tujuan.isdigit() or len(tujuan) < 9 or len(tujuan) > 15:
        _, markup = get_menu(update.effective_user.id)
        update.message.reply_text(
            "❌ Format nomor tidak valid.\n"
            "Masukkan ulang nomor tujuan (min 9 digit, max 15 digit, angka saja):",
            reply_markup=markup
        )
        return INPUT_TUJUAN

    context.user_data["tujuan"] = tujuan
    p = context.user_data.get("produk")
    if not p:
        _, markup = get_menu(update.effective_user.id)
        update.message.reply_text(
            "❌ Produk tidak ditemukan dalam sesi.\nSilakan mulai ulang order.",
            reply_markup=markup
        )
        return ConversationHandler.END

    # Modern: Gunakan inline keyboard untuk konfirmasi
    keyboard = [
        [
            InlineKeyboardButton("✅ Konfirmasi", callback_data="konfirmasi_order"),
            InlineKeyboardButton("❌ Batal", callback_data="batal_order")
        ]
    ]

    update.message.reply_text(
        f"📋 <b>Konfirmasi Pesanan</b>\n\n"
        f"Produk: <b>{p['kode']}</b> - {p['nama']}\n"
        f"Harga: <b>Rp {p['harga']:,}</b>\n"
        f"Nomor: <b>{tujuan}</b>\n\n"
        "Klik <b>Konfirmasi</b> untuk melanjutkan atau <b>Batal</b> untuk membatalkan.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return KONFIRMASI

def handle_konfirmasi(update, context):
    # Handler untuk tombol inline dan fallback teks
    if update.callback_query:
        query = update.callback_query
        query.answer()
        data = query.data
        if data == "konfirmasi_order":
            query.edit_message_text("✅ Pesanan kamu berhasil dikonfirmasi dan sedang diproses.", parse_mode=ParseMode.HTML)
            # Proses order di sini (misal: request API, simpan DB, dsb)
            return ConversationHandler.END
        elif data == "batal_order":
            _, markup = get_menu(query.from_user.id)
            query.edit_message_text("❌ Pesanan dibatalkan.", reply_markup=markup)
            return ConversationHandler.END
        else:
            _, markup = get_menu(query.from_user.id)
            query.edit_message_text("❌ Pilihan tidak valid.", reply_markup=markup)
            return ConversationHandler.END
    else:
        # Fallback jika user kirim teks saat konfirmasi
        text = update.message.text.strip().lower()
        if text == "ya":
            update.message.reply_text("✅ Pesanan kamu berhasil dikonfirmasi dan sedang diproses.", parse_mode=ParseMode.HTML)
            # Proses order di sini
            return ConversationHandler.END
        elif text == "batal":
            _, markup = get_menu(update.effective_user.id)
            update.message.reply_text("❌ Pesanan dibatalkan.", reply_markup=markup)
            return ConversationHandler.END
        else:
            update.message.reply_text("❌ Jawaban tidak valid. Klik tombol Konfirmasi/Batal atau ketik 'YA'/'BATAL'.")
            return KONFIRMASI
