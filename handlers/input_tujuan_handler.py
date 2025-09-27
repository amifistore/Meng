from telegram import ParseMode
from markup import get_menu

INPUT_TUJUAN, KONFIRMASI = 1, 2

def input_tujuan_step(update, context):
    tujuan = update.message.text.strip()
    # Validasi nomor tujuan: minimal 9 digit, maksimal 15 digit, hanya angka
    if not tujuan.isdigit() or len(tujuan) < 9 or len(tujuan) > 15:
        update.message.reply_text(
            "❌ Format nomor tidak valid. Masukkan ulang nomor tujuan (min 9 digit, max 15 digit, angka saja):"
        )
        return INPUT_TUJUAN  # Tetap di state input tujuan

    context.user_data["tujuan"] = tujuan
    p = context.user_data.get("produk")
    if not p:
        update.message.reply_text(
            "❌ Produk tidak ditemukan dalam sesi. Silakan mulai ulang order.", 
            reply_markup=get_menu(update.effective_user.id)
        )
        return ConversationHandler.END

    update.message.reply_text(
        f"📋 Konfirmasi pesanan:\n\n"
        f"Produk: <b>{p['kode']}</b> - {p['nama']}\n"
        f"Harga: Rp {p['harga']:,}\n"
        f"Nomor: <b>{tujuan}</b>\n\n"
        "Ketik 'YA' untuk konfirmasi atau 'BATAL' untuk membatalkan.",
        parse_mode=ParseMode.HTML
    )
    return KONFIRMASI
