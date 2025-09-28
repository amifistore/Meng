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
    # Handler untuk inline keyboard
    if update.callback_query:
        query = update.callback_query
        user = query.from_user
        query.answer()
        data = query.data
        
        if data == "order_batal":
            context.user_data.clear()
            info_text, markup = get_menu(user.id)
            query.edit_message_text("❌ Order dibatalkan.", reply_markup=markup)
            logger.info(f"User {user.id} membatalkan order via button")
            return ConversationHandler.END
            
        if data == "order_konfirmasi":
            return process_order_confirmation(query, context, user)
            
        # Fallback untuk data tidak dikenali
        info_text, markup = get_menu(user.id)
        query.edit_message_text("❌ Pilihan tidak valid.", reply_markup=markup)
        return ConversationHandler.END
        
    else:
        # Handler untuk text input (fallback)
        return handle_text_confirmation(update, context)

def process_order_confirmation(query, context, user):
    """Process order confirmation dari inline button"""
    produk = context.user_data.get("produk")
    tujuan = context.user_data.get("tujuan")
    ref_id = context.user_data.get("ref_id")
    
    # Validasi data lengkap
    if not all([produk, tujuan, ref_id]):
        info_text, markup = get_menu(user.id)
        query.edit_message_text("❌ Data order tidak lengkap. Silakan mulai lagi.", reply_markup=markup)
        return ConversationHandler.END
    
    # Update pesan ke status processing
    msg_proc = query.edit_message_text(
        "🔄 <b>MEMPROSES ORDER...</b>\n\n"
        "Silakan tunggu, order Anda sedang diproses...",
        parse_mode=ParseMode.HTML
    )
    
    try:
        logger.info(f"Memproses order user {user.id}: {produk['kode']} -> {tujuan} (ref: {ref_id})")
        
        # Panggil provider API
        result = create_trx(produk['kode'], tujuan, ref_id)
        
        # Log response provider
        logger.info(f"Response provider untuk {ref_id}: {result}")
        
        # Tampilkan raw response ke user (untuk debugging)
        raw_resp_text = str(result)
        query.bot.send_message(
            chat_id=user.id,
            text=f"🔎 <b>DETAIL RESPONSE:</b>\n<code>{raw_resp_text}</code>",
            parse_mode=ParseMode.HTML
        )
        
        # Process provider response
        return process_provider_response(result, msg_proc, user, produk, tujuan, ref_id, context)
        
    except Exception as e:
        logger.error(f"Error processing order {ref_id}: {str(e)}")
        return handle_order_error(msg_proc, str(e), context)

def handle_text_confirmation(update, context):
    """Handle konfirmasi via text input (fallback)"""
    user = update.message.from_user
    text = update.message.text.strip().upper()
    
    if text == 'BATAL':
        context.user_data.clear()
        info_text, markup = get_menu(user.id)
        update.message.reply_text("❌ Order dibatalkan.", reply_markup=markup)
        return ConversationHandler.END
        
    if text == 'YA' or text == 'Y':
        produk = context.user_data.get("produk")
        tujuan = context.user_data.get("tujuan")
        ref_id = context.user_data.get("ref_id")
        
        if not all([produk, tujuan, ref_id]):
            info_text, markup = get_menu(user.id)
            update.message.reply_text("❌ Data order tidak lengkap. Silakan mulai lagi.", reply_markup=markup)
            return ConversationHandler.END
            
        processing_msg = update.message.reply_text("🔄 Memproses order... Silakan tunggu.")
        
        try:
            logger.info(f"Memproses order text user {user.id}: {produk['kode']} -> {tujuan}")
            result = create_trx(produk['kode'], tujuan, ref_id)
            
            # Tampilkan raw response
            raw_resp_text = str(result)
            update.message.reply_text(
                f"🔎 <b>DETAIL RESPONSE:</b>\n<code>{raw_resp_text}</code>",
                parse_mode=ParseMode.HTML
            )
            
            # Process response
            return process_provider_response_text(result, processing_msg, user, produk, tujuan, ref_id, context)
            
        except Exception as e:
            logger.error(f"Error processing text order {ref_id}: {str(e)}")
            processing_msg.edit_text(
                f"❌ <b>ERROR SYSTEM</b>\n\n"
                f"Terjadi error: <code>{str(e)}</code>\n"
                f"Silakan hubungi admin.",
                parse_mode=ParseMode.HTML
            )
            context.user_data.clear()
            return ConversationHandler.END
            
    else:
        update.message.reply_text(
            "❌ Konfirmasi tidak valid!\n"
            "Ketik YA untuk konfirmasi atau BATAL untuk membatalkan."
        )
        return KONFIRMASI

def process_provider_response(result, msg_proc, user, produk, tujuan, ref_id, context):
    """Process response dari provider untuk inline button"""
    # Validasi response structure
    if not result or not isinstance(result, dict):
        msg_proc.edit_text(
            "❌ <b>RESPONSE TIDAK VALID</b>\n\n"
            "Provider mengembalikan response yang tidak valid.\n"
            "Silakan hubungi admin.",
            parse_mode=ParseMode.HTML
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # Extract dan normalisasi data response
    status = str(result.get('status', '')).lower()
    message = str(result.get('message', '')).lower()
    status_code = result.get('status_code')
    sn = result.get('sn', 'N/A')
    
    # Deteksi status sukses/gagal
    is_success = detect_order_success(status, message, status_code)
    
    if is_success:
        # ORDER SUKSES
        return handle_successful_order(result, msg_proc, user, produk, tujuan, ref_id, sn, context)
    else:
        # ORDER GAGAL
        return handle_failed_order(result, msg_proc, user, produk, tujuan, ref_id, context)

def process_provider_response_text(result, processing_msg, user, produk, tujuan, ref_id, context):
    """Process response dari provider untuk text input"""
    # Validasi response structure
    if not result or not isinstance(result, dict):
        processing_msg.edit_text(
            "❌ <b>RESPONSE TIDAK VALID</b>\n\n"
            "Provider mengembalikan response yang tidak valid.\n"
            "Silakan hubungi admin.",
            parse_mode=ParseMode.HTML
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # Extract dan normalisasi data response
    status = str(result.get('status', '')).lower()
    message = str(result.get('message', '')).lower()
    status_code = result.get('status_code')
    sn = result.get('sn', 'N/A')
    
    # Deteksi status sukses/gagal
    is_success = detect_order_success(status, message, status_code)
    
    if is_success:
        # ORDER SUKSES
        return handle_successful_order_text(result, processing_msg, user, produk, tujuan, ref_id, sn, context)
    else:
        # ORDER GAGAL
        return handle_failed_order_text(result, processing_msg, user, produk, tujuan, ref_id, context)

def detect_order_success(status, message, status_code):
    """Deteksi apakah order sukses berdasarkan response provider"""
    # Priority 1: Check status_code
    if status_code is not None:
        return str(status_code) == '0'
    
    # Priority 2: Check status text
    if any(success_word in status for success_word in ['sukses', 'success', 'ok', 'berhasil']):
        return True
    if any(fail_word in status for fail_word in ['gagal', 'failed', 'error']):
        return False
    
    # Priority 3: Check message text
    if any(success_word in message for success_word in ['sukses', 'success', 'berhasil']):
        return True
    if any(fail_word in message for fail_word in ['gagal', 'failed', 'error']):
        return False
    
    # Default: assume failed for safety
    return False

def handle_successful_order(result, msg_proc, user, produk, tujuan, ref_id, sn, context):
    """Handle successful order untuk inline button"""
    try:
        # Potong saldo user
        if not kurang_saldo_user(user.id, produk['harga'], tipe="order", 
                               keterangan=f"Order {produk['kode']} ke {tujuan}"):
            msg_proc.edit_text(
                f"❌ <b>GAGAL POTONG SALDO</b>\n\n"
                f"Order berhasil di provider tapi gagal memotong saldo.\n"
                f"Silakan hubungi admin untuk refund.",
                parse_mode=ParseMode.HTML
            )
            context.user_data.clear()
            return ConversationHandler.END
        
        # Simpan riwayat transaksi
        transaksi = {
            "ref_id": ref_id,
            "kode": produk['kode'],
            "tujuan": tujuan,
            "harga": produk['harga'],
            "tanggal": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "success",
            "sn": sn,
            "keterangan": result.get('message', 'Success'),
            "raw_response": str(result)
        }
        
        tambah_riwayat(user.id, transaksi)
        logger.info(f"Order sukses dicatat: {ref_id}")
        
        # Kirim pesan sukses
        msg_proc.edit_text(
            f"✅ <b>ORDER BERHASIL!</b>\n\n"
            f"🆔 Ref ID: <code>{ref_id}</code>\n"
            f"📦 Produk: <b>{produk['nama']}</b>\n"
            f"💰 Harga: <b>Rp {produk['harga']:,}</b>\n"
            f"📱 Tujuan: <b>{tujuan}</b>\n"
            f"🎫 SN: <code>{sn}</code>\n\n"
            f"💾 Status: <b>{result.get('message', 'Success')}</b>\n\n"
            f"Terima kasih telah berbelanja! 🛍️",
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"Error handling successful order {ref_id}: {str(e)}")
        msg_proc.edit_text(
            f"⚠️ <b>ORDER BERHASIL TAPI ADA KENDALA SYSTEM</b>\n\n"
            f"Order di provider sukses tapi ada kendala system.\n"
            f"Ref ID: <code>{ref_id}</code>\n"
            f"Silakan hubungi admin dengan Ref ID di atas.",
            parse_mode=ParseMode.HTML
        )
    
    finally:
        context.user_data.clear()
        return ConversationHandler.END

def handle_successful_order_text(result, processing_msg, user, produk, tujuan, ref_id, sn, context):
    """Handle successful order untuk text input"""
    try:
        # Potong saldo user
        if not kurang_saldo_user(user.id, produk['harga'], tipe="order", 
                               keterangan=f"Order {produk['kode']} ke {tujuan}"):
            processing_msg.edit_text(
                f"❌ <b>GAGAL POTONG SALDO</b>\n\n"
                f"Order berhasil di provider tapi gagal memotong saldo.\n"
                f"Silakan hubungi admin untuk refund.",
                parse_mode=ParseMode.HTML
            )
            context.user_data.clear()
            return ConversationHandler.END
        
        # Simpan riwayat transaksi
        transaksi = {
            "ref_id": ref_id,
            "kode": produk['kode'],
            "tujuan": tujuan,
            "harga": produk['harga'],
            "tanggal": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "success",
            "sn": sn,
            "keterangan": result.get('message', 'Success'),
            "raw_response": str(result)
        }
        
        tambah_riwayat(user.id, transaksi)
        logger.info(f"Order sukses dicatat: {ref_id}")
        
        # Kirim pesan sukses
        processing_msg.edit_text(
            f"✅ <b>ORDER BERHASIL!</b>\n\n"
            f"🆔 Ref ID: <code>{ref_id}</code>\n"
            f"📦 Produk: <b>{produk['nama']}</b>\n"
            f"💰 Harga: <b>Rp {produk['harga']:,}</b>\n"
            f"📱 Tujuan: <b>{tujuan}</b>\n"
            f"🎫 SN: <code>{sn}</code>\n\n"
            f"💾 Status: <b>{result.get('message', 'Success')}</b>\n\n"
            f"Terima kasih telah berbelanja! 🛍️",
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"Error handling successful order text {ref_id}: {str(e)}")
        processing_msg.edit_text(
            f"⚠️ <b>ORDER BERHASIL TAPI ADA KENDALA SYSTEM</b>\n\n"
            f"Order di provider sukses tapi ada kendala system.\n"
            f"Ref ID: <code>{ref_id}</code>\n"
            f"Silakan hubungi admin dengan Ref ID di atas.",
            parse_mode=ParseMode.HTML
        )
    
    finally:
        context.user_data.clear()
        return ConversationHandler.END

def handle_failed_order(result, msg_proc, user, produk, tujuan, ref_id, context):
    """Handle failed order untuk inline button"""
    error_msg = result.get('message', 'Unknown error from provider')
    
    logger.warning(f"Order gagal {ref_id}: {error_msg}")
    
    msg_proc.edit_text(
        f"❌ <b>ORDER GAGAL</b>\n\n"
        f"🆔 Ref ID: <code>{ref_id}</code>\n"
        f"📦 Produk: <b>{produk['nama']}</b>\n"
        f"📱 Tujuan: <b>{tujuan}</b>\n"
        f"💬 Error: <b>{error_msg}</b>\n\n"
        f"Saldo tidak dipotong. Silakan coba lagi atau hubungi admin.",
        parse_mode=ParseMode.HTML
    )
    
    context.user_data.clear()
    return ConversationHandler.END

def handle_failed_order_text(result, processing_msg, user, produk, tujuan, ref_id, context):
    """Handle failed order untuk text input"""
    error_msg = result.get('message', 'Unknown error from provider')
    
    logger.warning(f"Order gagal text {ref_id}: {error_msg}")
    
    processing_msg.edit_text(
        f"❌ <b>ORDER GAGAL</b>\n\n"
        f"🆔 Ref ID: <code>{ref_id}</code>\n"
        f"📦 Produk: <b>{produk['nama']}</b>\n"
        f"📱 Tujuan: <b>{tujuan}</b>\n"
        f"💬 Error: <b>{error_msg}</b>\n\n"
        f"Saldo tidak dipotong. Silakan coba lagi atau hubungi admin.",
        parse_mode=ParseMode.HTML
    )
    
    context.user_data.clear()
    return ConversationHandler.END

def handle_order_error(msg_proc, error_message, context):
    """Handle system error selama proses order"""
    msg_proc.edit_text(
        f"❌ <b>SYSTEM ERROR</b>\n\n"
        f"Terjadi kendala system: <code>{error_message}</code>\n\n"
        f"Silakan hubungi admin untuk bantuan.",
        parse_mode=ParseMode.HTML
    )
    
    context.user_data.clear()
    return ConversationHandler.END

# Export conversation handler
def get_order_conversation_handler():
    """Return conversation handler untuk order"""
    from telegram.ext import MessageHandler, Filters, CallbackQueryHandler
    
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_konfirmasi, pattern='^order_')],
        states={
            INPUT_TUJUAN: [
                MessageHandler(Filters.text & ~Filters.command, handle_input_tujuan)
            ],
            KONFIRMASI: [
                CallbackQueryHandler(handle_konfirmasi, pattern='^order_'),
                MessageHandler(Filters.text & ~Filters.command, handle_konfirmasi)
            ]
        },
        fallbacks=[MessageHandler(Filters.command, handle_input_tujuan)],
        allow_reentry=True
    )
