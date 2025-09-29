from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ConversationHandler
import uuid
from markup import reply_main_menu
from saldo import get_saldo_user

INPUT_TUJUAN = 1
KONFIRMASI = 2

def handle_input_tujuan(update, context):
    user = update.message.from_user
    text = update.message.text.strip()
    if text == '/batal':
        context.user_data.clear()
        update.message.reply_text("❌ Order dibatalkan.", reply_markup=reply_main_menu(user.id))
        return ConversationHandler.END
    if not text.isdigit() or len(text) < 10 or len(text) > 15:
        update.message.reply_text(
            "❌ Format nomor tidak valid! Harus angka minimal 10 digit dan maksimal 15 digit.\n"
            "Contoh: 081234567890\n\n"
            "Silakan input ulang atau ketik /batal untuk membatalkan."
        )
        return INPUT_TUJUAN
    produk = context.user_data.get("produk")
    if not produk:
        update.message.reply_text("❌ Sesi expired. Silakan mulai order lagi.", reply_markup=reply_main_menu(user.id))
        return ConversationHandler.END

    # Cek saldo user
    saldo = get_saldo_user(user.id)
    if saldo < produk['harga']:
        update.message.reply_text(
            f"❌ Saldo tidak cukup!\n"
            f"Produk: {produk['nama']} - Rp {produk['harga']:,}\n"
            f"Saldo kamu: Rp {saldo:,}\n\n"
            "Silakan top up terlebih dahulu.",
            reply_markup=reply_main_menu(user.id)
        )
        return ConversationHandler.END

    # PATCH: Hilangkan cek kuota produk, agar order tetap bisa lanjut walau stok 0
    # kuota = produk.get('kuota', 0)
    # if kuota <= 0:
    #     update.message.reply_text(
    #         f"❌ Produk <b>{produk['nama']}</b> kuotanya sudah habis!\n"
    #         "Silakan pilih produk lain.",
    #         parse_mode=ParseMode.HTML,
    #         reply_markup=reply_main_menu(user.id)
    #     )
    #     return ConversationHandler.END

    context.user_data["tujuan"] = text
    context.user_data["ref_id"] = str(uuid.uuid4())
    keyboard = [
        [InlineKeyboardButton("✅ Konfirmasi", callback_data="order_konfirmasi"),
         InlineKeyboardButton("❌ Batal", callback_data="order_batal")]
    ]
    update.message.reply_text(
        f"📋 <b>KONFIRMASI ORDER</b>\n\n"
        f"🆔 Ref ID: <code>{context.user_data['ref_id']}</code>\n"
        f"📦 Produk: <b>{produk['nama']}</b>\n"
        f"💰 Harga: <b>Rp {produk['harga']:,}</b>\n"
        f"📱 Tujuan: <b>{text}</b>\n"
        f"Stok: <b>{produk.get('kuota', 0)}</b>\n\n"
        f"Klik <b>Konfirmasi</b> untuk melanjutkan atau <b>Batal</b> untuk membatalkan.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return KONFIRMASI
