import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def handle_all_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle semua callback query dari button produk"""
    try:
        query = update.callback_query
        await query.answer()  # Important: jawab callback dulu
        
        user_id = query.from_user.id
        callback_data = query.data
        
        logger.info(f"📲 CALLBACK RECEIVED from {user_id}: {callback_data}")
        
        # Handle berbagai jenis callback
        if callback_data.startswith('produk_'):
            # Handle pemilihan produk biasa
            product_id = callback_data.replace('produk_', '')
            logger.info(f"🎯 Product selected: {product_id} by user {user_id}")
            
            await query.edit_message_text(
                f"✅ Produk dipilih: {product_id}\n"
                f"Silakan lanjutkan dengan mengirim nomor tujuan...\n\n"
                f"Ketik /cancel untuk membatalkan"
            )
            
        elif callback_data == 'back_main':
            # Handle kembali ke menu utama
            from handlers.main_menu_handler import start
            await start(update, context)
            
        elif callback_data.startswith('order_'):
            # Handle konfirmasi order
            logger.info(f"🔄 Order action: {callback_data}")
            # Tambahkan logic order di sini
            
        else:
            logger.warning(f"🤖 Unknown callback: {callback_data}")
            await query.edit_message_text("❌ Perintah tidak dikenali")
            
    except Exception as e:
        logger.error(f"💥 Error in callback handler: {e}")
        if update.callback_query:
            await update.callback_query.answer("Error processing request", show_alert=True)
