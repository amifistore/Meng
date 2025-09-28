from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from markup import get_menu
from provider import create_trx
from saldo import get_saldo_user, kurang_saldo_user
from riwayat import tambah_riwayat
import uuid
import time
import logging

# Setup logging
logger = logging.getLogger(__name__)

# States
INPUT_TUJUAN, KONFIRMASI = range(2)

def handle_input_tujuan(update, context):
    """Handle input nomor tujuan dari user"""
    user = update.message.from_user
    text = update.message.text.strip()
    
    # Cancel command
    if text == '/batal':
        context.user_data.clear()
        info_text, markup = get_menu(user.id)
        update.message.reply_text("❌ Order dibatalkan.", reply_markup=markup)
        logger.info(f"User {user.id} membatalkan order")
        return ConversationHandler.END
    
    # Validate phone number
    if not text.isdigit() or len(text) < 10 or len(text) > 15:
        update.message.reply_text(
            "❌ Format nomor tidak valid! Harus angka minimal 10 digit dan maksimal 15 digit.\n"
            "Contoh: 081234567890\n\n"
            "Silakan input ulang atau ketik /batal untuk membatalkan."
        )
        return INPUT_TUJUAN
    
    # Get product from context
    produk = context.user_data.get("produk")
    if not produk:
        info_text, markup = get_menu(user.id)
        update.message.reply_text("❌ Sesi expired. Silakan mulai order lagi.", reply_markup=markup)
        return ConversationHandler.END
    
    # Check saldo
    saldo = get_saldo_user(user.id)
    print(f"[DEBUG] Saldo user {user.id}: {saldo}, Harga produk: {produk['harga']}")
    
    if saldo < produk['harga']:
        info_text, markup = get_menu(user.id)
        update.message.reply_text(
            f"❌ Saldo tidak cukup!\n"
            f"Produk: {produk['nama']} - Rp {produk['harga']:,}\n"
            f"Saldo kamu: Rp {saldo:,}\n\n"
            "Silakan top up terlebih dahulu.",
            reply_markup=markup
        )
        return ConversationHandler.END
    
    # Save destination and generate ref_id
    context.user_data["tujuan"] = text
    context.user_data["ref_id"] = str(uuid.uuid4())

    # Konfirmasi order dengan inline keyboard
    keyboard = [
        [InlineKeyboardButton("✅ Konfirmasi Order", callback_data="order_konfirmasi")],
        [InlineKeyboardButton("❌ Batalkan", callback_data="order_batal")]
    ]
    
    update.message.reply_text(
        f"📋 <b>KONFIRMASI ORDER</b>\n\n"
        f"🆔 Ref ID: <code>{context.user_data['ref_id']}</code>\n"
        f"📦 Produk: <b>{produk['nama']}</b>\n"
        f"💰 Harga: <b>Rp {produk['harga']:,}</b>\n"
        f"📱 Tujuan: <b>{text}</b>\n\n"
        f"Saldo setelah order: <b>Rp {saldo - produk['harga']:,}</b>\n\n"
        f"Klik <b>Konfirmasi Order</b> untuk melanjutkan.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    logger.info(f"User {user.id} konfirmasi order {produk['kode']} ke {text}")
    return KONFIRMASI

def handle_konfirmasi(update, context):
    """Handle konfirmasi order dari user"""
    if update.callback_query:
        query = update.callback_query
        user = query.from_user
        query.answer()
        data = query.data
        
        if data == "order_batal":
            context.user_data.clear()
            info_text, markup = get_menu(user.id)
            query.edit_message_text("❌ Order dibatalkan.", reply_markup=markup)
            return ConversationHandler.END
            
        if data == "order_konfirmasi":
            produk = context.user_data.get("produk")
            tujuan = context.user_data.get("tujuan")
            ref_id = context.user_data.get("ref_id")
            
            if not all([produk, tujuan, ref_id]):
                info_text, markup = get_menu(user.id)
                query.edit_message_text("❌ Data order tidak lengkap. Silakan mulai lagi.", reply_markup=markup)
                return ConversationHandler.END
            
            msg_proc = query.edit_message_text("🔄 Memproses order... Silakan tunggu.")
            
            try:
                print(f"[DEBUG] Memulai order: user={user.id}, produk={produk['kode']}, tujuan={tujuan}, ref_id={ref_id}")
                
                # Panggil provider
                result = create_trx(produk['kode'], tujuan, ref_id)
                print(f"[DEBUG] Response provider: {result}")
                
                # Tampilkan raw response
                raw_resp_text = str(result)
                query.bot.send_message(
                    chat_id=user.id,
                    text=f"🔎 <b>RESPON PROVIDER:</b>\n<code>{raw_resp_text}</code>",
                    parse_mode=ParseMode.HTML
                )
                
                # Process response
                status = str(result.get('status', '')).lower()
                message = str(result.get('message', '')).lower()
                status_code = result.get('status_code', None)
                sn = result.get('sn', 'N/A')

                # Deteksi status sukses
                is_success = False
                if status_code is not None and str(status_code) == '0':
                    is_success = True
                elif any(word in status for word in ['sukses', 'success', 'ok']):
                    is_success = True
                elif any(word in message for word in ['sukses', 'success']):
                    is_success = True
                
                print(f"[DEBUG] Status deteksi: is_success={is_success}, status={status}, message={message}, status_code={status_code}")
                
                if is_success:
                    # ORDER SUKSES - POTONG SALDO
                    print(f"[DEBUG] Order sukses, memotong saldo user {user.id} sebesar {produk['harga']}")
                    
                    success_saldo = kurang_saldo_user(user.id, produk['harga'], "order", f"Order {produk['kode']} ke {tujuan}")
                    print(f"[DEBUG] Hasil potong saldo: {success_saldo}")
                    
                    if not success_saldo:
                        msg_proc.edit_text(
                            f"❌ <b>GAGAL POTONG SALDO</b>\n\n"
                            f"Order berhasil di provider tapi gagal memotong saldo.\n"
                            f"Silakan hubungi admin untuk refund.",
                            parse_mode=ParseMode.HTML
                        )
                        context.user_data.clear()
                        return ConversationHandler.END
                    
                    # TAMBAH RIWAYAT
                    transaksi = {
                        "ref_id": ref_id,
                        "kode": produk['kode'],
                        "tujuan": tujuan,
                        "harga": produk['harga'],
                        "tanggal": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "success",
                        "sn": sn,
                        "keterangan": result.get('message', 'Success'),
                        "raw_response": raw_resp_text
                    }
                    
                    print(f"[DEBUG] Menyimpan riwayat: {transaksi}")
                    success_riwayat = tambah_riwayat(user.id, transaksi)
                    print(f"[DEBUG] Hasil simpan riwayat: {success_riwayat}")
                    
                    # Cek saldo setelah
                    saldo_setelah = get_saldo_user(user.id)
                    print(f"[DEBUG] Saldo setelah order: {saldo_setelah}")
                    
                    msg_proc.edit_text(
                        f"✅ <b>ORDER BERHASIL!</b>\n\n"
                        f"🆔 Ref ID: <code>{ref_id}</code>\n"
                        f"📦 Produk: <b>{produk['nama']}</b>\n"
                        f"💰 Harga: <b>Rp {produk['harga']:,}</b>\n"
                        f"📱 Tujuan: <b>{tujuan}</b>\n"
                        f"🎫 SN: <code>{sn}</code>\n\n"
                        f"💾 Status: <b>{result.get('message', 'Success')}</b>\n"
                        f"💰 Saldo akhir: <b>Rp {saldo_setelah:,}</b>\n\n"
                        f"Terima kasih! 🛍️",
                        parse_mode=ParseMode.HTML
                    )
                    
                else:
                    # ORDER GAGAL
                    error_msg = result.get('message', 'Unknown error')
                    print(f"[DEBUG] Order gagal: {error_msg}")
                    
                    msg_proc.edit_text(
                        f"❌ <b>ORDER GAGAL</b>\n\n"
                        f"🆔 Ref ID: <code>{ref_id}</code>\n"
                        f"📦 Produk: <b>{produk['nama']}</b>\n"
                        f"📱 Tujuan: <b>{tujuan}</b>\n"
                        f"💬 Error: <b>{error_msg}</b>\n\n"
                        f"Saldo tidak dipotong. Silakan coba lagi.",
                        parse_mode=ParseMode.HTML
                    )
                    
            except Exception as e:
                print(f"[DEBUG] Exception selama order: {str(e)}")
                msg_proc.edit_text(
                    f"❌ <b>SYSTEM ERROR</b>\n\n"
                    f"Error: <code>{str(e)}</code>\n"
                    f"Silakan hubungi admin.",
                    parse_mode=ParseMode.HTML
                )
            
            finally:
                context.user_data.clear()
                return ConversationHandler.END
    
    return ConversationHandler.END
