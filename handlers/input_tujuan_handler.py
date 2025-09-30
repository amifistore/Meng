from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ConversationHandler
import uuid
from markup import reply_main_menu, konfirmasi_order_keyboard
from saldo import get_saldo_user
from config import ADMIN_IDS

# IMPORT DARI FILE TERPUSAT
from handlers import INPUT_TUJUAN, KONFIRMASI

import logging
logger = logging.getLogger(__name__)

def handle_input_tujuan(update, context):
    user = update.message.from_user
    text = update.message.text.strip()
    is_admin = user.id in ADMIN_IDS

    logger.info(f"🎯 handle_input_tujuan DIPANGGIL - User: {user.first_name}, Text: {text}")

    if text == '/batal':
        logger.info("❌ User membatalkan order")
        context.user_data.clear()
        update.message.reply_text("❌ Order dibatalkan.", reply_markup=reply_main_menu(is_admin=is_admin))
        return ConversationHandler.END
        
    if not text.isdigit() or len(text) < 10 or len(text) > 15:
        logger.warning(f"❌ Invalid phone number format: {text}")
        update.message.reply_text(
            "❌ Format nomor tidak valid! Harus angka minimal 10 digit dan maksimal 15 digit.\n"
            "Contoh: 081234567890\n\n"
            "Silakan input ulang atau ketik /batal untuk membatalkan."
        )
        return INPUT_TUJUAN
        
    produk = context.user_data.get("produk")
    if not produk:
        logger.error("❌ No product found in user_data - session expired")
        update.message.reply_text("❌ Sesi expired. Silakan mulai order lagi.", reply_markup=reply_main_menu(is_admin=is_admin))
        return ConversationHandler.END

    # Cek saldo user
    saldo = get_saldo_user(user.id)
    logger.info(f"💰 Final saldo check: {saldo} >= {produk['harga']}")
    
    if saldo < produk['harga']:
        logger.warning(f"❌ Insufficient balance in final check: {saldo} < {produk['harga']}")
        update.message.reply_text(
            f"❌ Saldo tidak cukup!\n"
            f"Produk: {produk['nama']} - Rp {produk['harga']:,}\n"
            f"Saldo kamu: Rp {saldo:,}\n\n"
            "Silakan top up terlebih dahulu.",
            reply_markup=reply_main_menu(is_admin=is_admin)
        )
        return ConversationHandler.END

    context.user_data["tujuan"] = text
    context.user_data["ref_id"] = str(uuid.uuid4())[:8].upper()
    
    logger.info(f"✅ Ready for confirmation - Ref: {context.user_data['ref_id']}, Tujuan: {text}")
    
    update.message.reply_text(
        f"📋 <b>KONFIRMASI ORDER</b>\n\n"
        f"🆔 Ref ID: <code>{context.user_data['ref_id']}</code>\n"
        f"📦 Produk: <b>{produk['nama']}</b>\n"
        f"💰 Harga: <b>Rp {produk['harga']:,}</b>\n"
        f"📱 Tujuan: <b>{text}</b>\n"
        f"📊 Stok: <b>{produk.get('kuota', 0)}</b>\n\n"
        f"Klik <b>Konfirmasi</b> untuk melanjutkan atau <b>Batal</b> untuk membatalkan.",
        parse_mode=ParseMode.HTML,
        reply_markup=konfirmasi_order_keyboard()
    )
    return KONFIRMASI
