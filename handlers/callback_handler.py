import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def handle_all_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle semua callback query dari button produk"""
    try:
        query = update.callback_query
        user_id = query.from_user.id
        callback_data = query.data
        
        logger.info(f"📲 CALLBACK RECEIVED from {user_id}: {callback_data}")
        
        # Jawab callback dulu - PENTING!
        await query.answer()
        
        # Handle berbagai jenis callback
        if callback_data.startswith('produk_'):
            # Handle pemilihan produk dari topup_handler
            product_id = callback_data.replace('produk_', '')
            logger.info(f"🎯 Product selected from topup: {product_id} by user {user_id}")
            
            # Simpan data produk ke context
            context.user_data['selected_product'] = product_id
            
            await query.edit_message_text(
                f"✅ Produk dipilih: {product_id}\n\n"
                f"Silakan ketik nomor tujuan:\n"
                f"Contoh: 081234567890\n\n"
                f"Ketik /cancel untuk membatalkan"
            )
            
        elif callback_data.startswith('produk_static|'):
            # Handle pemilihan produk dari conversation handler
            product_data = callback_data.replace('produk_static|', '')
            logger.info(f"🎯 Product selected from conversation: {product_data} by user {user_id}")
            
            # Simpan data produk
            context.user_data['selected_product'] = product_data
            
            await query.edit_message_text(
                f"✅ Produk dipilih!\n\n"
                f"Silakan ketik nomor tujuan:\n"
                f"Contoh: 081234567890\n\n"
                f"Ketik /cancel untuk membatalkan"
            )
            
        elif callback_data == 'back_main':
            # Handle kembali ke menu utama
            from handlers.main_menu_handler import start
            await start(update, context)
            
        elif callback_data in ['order_konfirmasi', 'order_batal']:
            # Handle konfirmasi order - forward ke order_handler
            from handlers.order_handler import handle_konfirmasi
            await handle_konfirmasi(update, context)
            
        else:
            logger.warning(f"🤖 Unknown callback: {callback_data}")
            await query.edit_message_text("❌ Perintah tidak dikenali")
            
    except Exception as e:
        logger.error(f"💥 Error in callback handler: {e}")
        if update.callback_query:
            await update.callback_query.answer("Error processing request", show_alert=True)
