from telegram import ParseMode
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import re
import logging
from markup import reply_main_menu
from produk import get_produk_list
from saldo import get_saldo_user

# Setup logger
logger = logging.getLogger(__name__)

CHOOSING_PRODUK, INPUT_TUJUAN = 0, 1

def produk_pilih_callback(update, context):
    """Handle product selection callback"""
    if not update or not update.callback_query:
        logger.error("❌ Update or callback_query is None in produk_pilih_callback")
        return ConversationHandler.END
        
    query = update.callback_query
    user = query.from_user
    data = query.data
    query.answer()

    logger.info(f"🎯 produk_pilih_callback - User: {user.first_name}, Data: {data}")

    if data.startswith("produk_static|"):
        try:
            idx = int(data.split("|")[1])
            produk_list = get_produk_list()
            
            if idx < 0 or idx >= len(produk_list):
                query.edit_message_text("❌ Produk tidak valid.", reply_markup=reply_main_menu(user.id))
                return ConversationHandler.END

            p = produk_list[idx]
            context.user_data["produk"] = p
            saldo = get_saldo_user(user.id)
            
            if saldo < p['harga']:
                query.edit_message_text(
                    f"❌ Saldo kamu tidak cukup untuk order produk ini.\n"
                    f"Produk: <b>{p['nama']}</b>\nHarga: Rp {p['harga']:,}\n"
                    f"Saldo kamu: Rp {saldo:,}\n\n"
                    "Silakan top up dahulu sebelum order.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_main_menu(user.id)
                )
                return ConversationHandler.END

            # Clear previous user data
            context.user_data.pop('nomor_tujuan', None)
            
            query.edit_message_text(
                f"✅ <b>Produk yang dipilih:</b>\n"
                f"📦 <b>{p['kode']}</b> - {p['nama']}\n"
                f"💵 Harga: Rp {p['harga']:,}\n"
                f"📊 Stok: {p['kuota']}\n\n"
                "📱 <b>Silakan ketik nomor tujuan:</b>\n"
                "Contoh: <code>081234567890</code> atau <code>6281234567890</code>\n\n"
                "❌ Ketik /batal untuk membatalkan",
                parse_mode=ParseMode.HTML
            )
            return INPUT_TUJUAN

        except Exception as e:
            logger.error(f"💥 Error in produk_pilih_callback: {e}")
            query.edit_message_text(
                "❌ Terjadi kesalahan saat memilih produk.",
                reply_markup=reply_main_menu(user.id)
            )
            return ConversationHandler.END

    elif data == "back_main":
        query.edit_message_text("Kembali ke menu utama.", reply_markup=reply_main_menu(user.id))
        return ConversationHandler.END

    else:
        query.edit_message_text("❌ Callback tidak dikenali.", reply_markup=reply_main_menu(user.id))
        return ConversationHandler.END

def input_tujuan_callback(update, context):
    """Handle phone number input"""
    if not update or not update.message:
        logger.error("❌ Update or message is None in input_tujuan_callback")
        return ConversationHandler.END
        
    user = update.message.from_user
    nomor_tujuan = update.message.text.strip()
    
    logger.info(f"📱 input_tujuan_callback - User: {user.first_name}, Nomor: {nomor_tujuan}")

    # Check if user wants to cancel
    if nomor_tujuan.lower() in ['/batal', 'batal', 'cancel']:
        return batal_callback(update, context)

    # Validasi format nomor
    if not is_valid_phone_number(nomor_tujuan):
        update.message.reply_text(
            "❌ <b>Format nomor tidak valid!</b>\n\n"
            "📱 <b>Format yang diterima:</b>\n"
            "• <code>081234567890</code> (11-13 digit)\n"
            "• <code>6281234567890</code> (11-15 digit)\n\n"
            "🚫 <b>Yang tidak diterima:</b>\n"
            "• Nomor dengan spasi/tanda baca\n"
            "• Nomor terlalu pendek/panjang\n"
            "• Format +62 (gunakan 62 atau 08)\n\n"
            "🔄 <b>Silakan input ulang nomor tujuan:</b>\n"
            "Contoh: <code>081234567890</code>\n\n"
            "❌ Ketik /batal untuk membatalkan",
            parse_mode=ParseMode.HTML
        )
        return INPUT_TUJUAN

    # Simpan nomor tujuan
    context.user_data['nomor_tujuan'] = nomor_tujuan
    produk = context.user_data.get('produk', {})
    
    logger.info(f"✅ Nomor valid - User: {user.first_name}, Produk: {produk.get('kode', 'Unknown')}")

    # Lanjutkan ke proses pembayaran
    return process_payment(update, context)

def is_valid_phone_number(nomor):
    """Validasi format nomor telepon Indonesia"""
    try:
        # Hapus spasi dan karakter khusus
        nomor_clean = re.sub(r'[^\d]', '', nomor)
        
        # Validasi panjang nomor (10-15 digit)
        if len(nomor_clean) < 10 or len(nomor_clean) > 15:
            return False
        
        # Validasi prefix nomor Indonesia
        valid_prefixes = ['08', '628', '62', '8']
        if not any(nomor_clean.startswith(prefix) for prefix in valid_prefixes):
            return False
        
        # Validasi hanya angka
        if not nomor_clean.isdigit():
            return False
            
        return True
    except Exception as e:
        logger.error(f"💥 Error in phone validation: {e}")
        return False

def process_payment(update, context):
    """Process payment after valid phone number"""
    try:
        user = update.message.from_user
        produk = context.user_data.get('produk', {})
        nomor_tujuan = context.user_data.get('nomor_tujuan', '')
        
        if not produk:
            update.message.reply_text(
                "❌ Data produk tidak ditemukan. Silakan mulai ulang.",
                reply_markup=reply_main_menu(user.id)
            )
            return ConversationHandler.END

        # Format nomor untuk display
        nomor_display = format_phone_number(nomor_tujuan)
        
        update.message.reply_text(
            f"✅ <b>Order Berhasil Diproses!</b>\n\n"
            f"📦 <b>Produk:</b> {produk.get('nama', 'Unknown')}\n"
            f"📱 <b>Nomor Tujuan:</b> <code>{nomor_display}</code>\n"
            f"💵 <b>Harga:</b> Rp {produk.get('harga', 0):,}\n\n"
            "💰 <b>Silakan lanjutkan pembayaran:</b>\n"
            "1. Scan QRIS yang tersedia\n"
            "2. Bayar sesuai nominal\n"
            "3. Tunggu konfirmasi otomatis\n\n"
            "⏰ <i>QRIS aktif selama 15 menit</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_main_menu(user.id)
        )
        
        # TODO: Implement QRIS generation and payment processing here
        # generate_qris(produk['harga'])
        # save_order_to_database(user.id, produk, nomor_tujuan)
        
        # Clear user data setelah sukses
        context.user_data.clear()
        
        logger.info(f"✅ Payment process started - User: {user.first_name}, Product: {produk.get('kode')}")
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"💥 Error in process_payment: {e}")
        update.message.reply_text(
            "❌ Terjadi kesalahan saat memproses pembayaran. Silakan coba lagi.",
            reply_markup=reply_main_menu(user.id)
        )
        return ConversationHandler.END

def format_phone_number(nomor):
    """Format phone number for display"""
    nomor_clean = re.sub(r'[^\d]', '', nomor)
    
    if nomor_clean.startswith('62'):
        return f"62{nomor_clean[2:]}"
    elif nomor_clean.startswith('0'):
        return f"62{nomor_clean[1:]}"
    elif nomor_clean.startswith('8'):
        return f"62{nomor_clean}"
    else:
        return nomor_clean

def batal_callback(update, context):
    """Handler untuk cancel command"""
    user = update.message.from_user if update.message else update.callback_query.from_user
    
    context.user_data.clear()
    
    if update.message:
        update.message.reply_text(
            "❌ <b>Transaksi dibatalkan.</b>\n\nKembali ke menu utama.",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_main_menu(user.id)
        )
    else:
        update.callback_query.edit_message_text(
            "❌ <b>Transaksi dibatalkan.</b>\n\nKembali ke menu utama.",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_main_menu(user.id)
        )
    
    logger.info(f"❌ Transaction cancelled - User: {user.first_name}")
    return ConversationHandler.END

def start_callback(update, context):
    """Start command handler"""
    user = update.message.from_user
    context.user_data.clear()
    
    update.message.reply_text(
        "Selamat datang! Silakan pilih menu di bawah:",
        reply_markup=reply_main_menu(user.id)
    )
    return ConversationHandler.END

# Conversation Handler
def get_order_conversation_handler():
    """Return the conversation handler for order process"""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(produk_pilih_callback, pattern='^produk_static\|')
        ],
        states={
            INPUT_TUJUAN: [
                MessageHandler(Filters.text & ~Filters.command, input_tujuan_callback),
                CommandHandler('batal', batal_callback)
            ]
        },
        fallbacks=[
            CommandHandler('batal', batal_callback),
            CommandHandler('start', start_callback),
            MessageHandler(Filters.command, batal_callback)
        ],
        allow_reentry=True,
        name="order_conversation",
        persistent=False
    )
