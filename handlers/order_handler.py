from telegram import ParseMode
from telegram.ext import ConversationHandler
from markup import get_menu
from provider import create_trx
from utils import get_user_saldo, kurangi_saldo_user, tambah_riwayat
import random
import time

# States
INPUT_TUJUAN, KONFIRMASI = range(2)

def handle_input_tujuan(update, context):
    user = update.message.from_user
    text = update.message.text.strip()
    
    # Cancel command
    if text == '/batal':
        context.user_data.clear()
        update.message.reply_text("❌ Order dibatalkan.", reply_markup=get_menu(user.id))
        return ConversationHandler.END
    
    # Validate phone number
    if not text.isdigit() or len(text) < 10:
        update.message.reply_text(
            "❌ Format nomor tidak valid! Harus angka minimal 10 digit.\n"
            "Contoh: 081234567890\n\n"
            "Silakan input ulang atau ketik /batal untuk membatalkan."
        )
        return INPUT_TUJUAN
    
    # Get product from context
    produk = context.user_data.get("produk")
    if not produk:
        update.message.reply_text("❌ Sesi expired. Silakan mulai order lagi.", reply_markup=get_menu(user.id))
        return ConversationHandler.END
    
    # Check saldo
    saldo = get_user_saldo(user.id)
    if saldo < produk['harga']:
        update.message.reply_text(
            f"❌ Saldo tidak cukup!\n"
            f"Produk: {produk['nama']} - Rp {produk['harga']:,}\n"
            f"Saldo kamu: Rp {saldo:,}\n\n"
            "Silakan top up terlebih dahulu.",
            reply_markup=get_menu(user.id)
        )
        return ConversationHandler.END
    
    # Save destination
    context.user_data["tujuan"] = text
    context.user_data["ref_id"] = f"TRX{random.randint(100000, 999999)}"
    
    # Confirmation message
    update.message.reply_text(
        f"📋 **KONFIRMASI ORDER**\n\n"
        f"🆔 Ref ID: `{context.user_data['ref_id']}`\n"
        f"📦 Produk: {produk['nama']}\n"
        f"💰 Harga: Rp {produk['harga']:,}\n"
        f"📱 Tujuan: {text}\n\n"
        f"✅ Ketik **YA** untuk konfirmasi\n"
        f"❌ Ketik **BATAL** untuk membatalkan",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_menu(user.id)
    )
    
    return KONFIRMASI

def handle_konfirmasi(update, context):
    user = update.message.from_user
    text = update.message.text.strip().upper()
    
    if text == 'BATAL':
        context.user_data.clear()
        update.message.reply_text("❌ Order dibatalkan.", reply_markup=get_menu(user.id))
        return ConversationHandler.END
    
    if text != 'YA':
        update.message.reply_text(
            "❌ Konfirmasi tidak valid!\n"
            "Ketik **YA** untuk konfirmasi atau **BATAL** untuk membatalkan.",
            parse_mode=ParseMode.MARKDOWN
        )
        return KONFIRMASI
    
    # Process order
    produk = context.user_data.get("produk")
    tujuan = context.user_data.get("tujuan")
    ref_id = context.user_data.get("ref_id")
    
    if not all([produk, tujuan, ref_id]):
        update.message.reply_text("❌ Data order tidak lengkap. Silakan mulai lagi.", reply_markup=get_menu(user.id))
        return ConversationHandler.END
    
    # Send processing message
    processing_msg = update.message.reply_text("🔄 Memproses order... Silakan tunggu.")
    
    try:
        # Create transaction via provider
        result = create_trx(produk['kode'], tujuan, ref_id)
        
        # Process provider response
        if result.get('status') == 'success':
            # Deduct balance
            kurangi_saldo_user(user.id, produk['harga'])
            
            # Save transaction history
            transaksi = {
                "ref_id": ref_id,
                "produk": produk['nama'],
                "kode": produk['kode'],
                "harga": produk['harga'],
                "tujuan": tujuan,
                "status": "success",
                "tanggal": time.strftime("%Y-%m-%d %H:%M:%S"),
                "sn" : result.get('sn', ''),
                "response": result
            }
            tambah_riwayat(user.id, transaksi)
            
            # Success message
            processing_msg.edit_text(
                f"✅ **ORDER BERHASIL**\n\n"
                f"🆔 Ref ID: `{ref_id}`\n"
                f"📦 Produk: {produk['nama']}\n"
                f"💰 Harga: Rp {produk['harga']:,}\n"
                f"📱 Tujuan: {tujuan}\n"
                f"🎫 SN: {result.get('sn', 'N/A')}\n\n"
                f"💾 Status: {result.get('message', 'Success')}",
                parse_mode=ParseMode.MARKDOWN
            )
            
        else:
            # Failed transaction
            error_msg = result.get('message', 'Unknown error')
            processing_msg.edit_text(
                f"❌ **ORDER GAGAL**\n\n"
                f"🆔 Ref ID: `{ref_id}`\n"
                f"📦 Produk: {produk['nama']}\n"
                f"💬 Error: {error_msg}\n\n"
                f"Silakan coba lagi atau hubungi admin.",
                parse_mode=ParseMode.MARKDOWN
            )
            
    except Exception as e:
        processing_msg.edit_text(
            f"❌ **ERROR SYSTEM**\n\n"
            f"Terjadi error saat memproses: {str(e)}\n"
            f"Silakan hubungi admin."
        )
    
    finally:
        context.user_data.clear()
        return ConversationHandler.END
