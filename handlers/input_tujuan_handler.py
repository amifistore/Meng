from telegram import ParseMode
from markup import get_menu

INPUT_TUJUAN, KONFIRMASI = 1, 2

def input_tujuan_step(update, context):
    tujuan = update.message.text.strip()
    if not tujuan.isdigit() or len(tujuan) < 9 or len(tujuan) > 15:
        update.message.reply_text("❌ Format nomor tidak valid. Masukkan ulang (min 9 digit, max 15 digit):")
        return INPUT_TUJUAN
    
    context.user_data["tujuan"] = tujuan
    p = context.user_data.get("produk")
    update.message.reply_text(
        f"📋 Konfirmasi pesanan:\n\nProduk: <b>{p['kode']}</b> - {p['nama']}\nHarga: Rp {p['harga']:,}\nNomor: <b>{tujuan}</b>\n\nKetik 'YA' untuk konfirmasi atau 'BATAL' untuk membatalkan.",
        parse_mode=ParseMode.HTML
    )
    return KONFIRMASI
