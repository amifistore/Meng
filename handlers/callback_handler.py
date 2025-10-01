import logging
from telegram import Update
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)

def handle_all_callbacks(update, context):
    """Handle semua callback query dari button produk"""
    try:
        # Pastikan update dan callback_query ada
        if not update or not update.callback_query:
            logger.error("❌ Update or callback_query is None")
            return
        
        query = update.callback_query
        user = query.from_user
        callback_data = query.data
        
        logger.info(f"📲 CALLBACK RECEIVED from {user.id}: {callback_data}")
        
        # Jawab callback dulu
        query.answer()
        
        # Handle berbagai jenis callback
        if callback_data.startswith('produk_'):
            # Handle pemilihan produk dari topup_handler
            product_id = callback_data.replace('produk_', '')
            logger.info(f"🎯 Product selected from topup: {product_id} by user {user.id}")
            
            # Simpan data produk ke context
            context.user_data['selected_product'] = product_id
            
            query.edit_message_text(
                f"✅ Produk dipilih: {product_id}\n\n"
                f"Silakan ketik nomor tujuan:\n"
                f"Contoh: 081234567890\n\n"
                f"Ketik /cancel untuk membatalkan"
            )
            
        elif callback_data.startswith('produk_static|'):
            # Handle pemilihan produk dari conversation handler
            product_data = callback_data.replace('produk_static|', '')
            logger.info(f"🎯 Product selected from conversation: {product_data} by user {user.id}")
            
            # Forward ke produk_pilih_handler
            from handlers.produk_pilih_handler import produk_pilih_callback
            return produk_pilih_callback(update, context)
            
        elif callback_data == 'back_main':
            # Handle kembali ke menu utama
            from handlers.main_menu_handler import start
            return start(update, context)
            
        elif callback_data in ['order_konfirmasi', 'order_batal']:
            # Handle konfirmasi order - forward ke order_handler
            from handlers.order_handler import handle_konfirmasi
            return handle_konfirmasi(update, context)
            
        elif callback_data.startswith('topup_'):
            # Handle topup callbacks - forward ke topup_handler
            from handlers.topup_handler import admin_topup_callback
            return admin_topup_callback(update, context)
            
        elif callback_data.startswith('admin_'):
            # Handle admin callbacks
            if callback_data.startswith('admin_edit_produk|'):
                from handlers.admin_edit_handler import admin_edit_produk_callback
                return admin_edit_produk_callback(update, context)
            elif callback_data.startswith('edit_'):
                from handlers.admin_edit_handler import admin_edit_harga_prompt, admin_edit_deskripsi_prompt
                if 'harga' in callback_data:
                    return admin_edit_harga_prompt(update, context)
                elif 'deskripsi' in callback_data:
                    return admin_edit_deskripsi_prompt(update, context)
            
        elif callback_data == 'riwayat_topup_admin' or callback_data.startswith('admin_topup_detail'):
            # Handle admin topup list
            from handlers.topup_handler import admin_topup_list_callback, admin_topup_detail_callback
            if callback_data == 'riwayat_topup_admin':
                return admin_topup_list_callback(update, context)
            else:
                return admin_topup_detail_callback(update, context)
                
        elif callback_data == 'semua_riwayat':
            # Handle semua riwayat admin
            from handlers.riwayat_handler import semua_riwayat_callback
            return semua_riwayat_callback(update, context)
            
        else:
            logger.warning(f"🤖 Unknown callback: {callback_data}")
            query.edit_message_text("❌ Perintah tidak dikenali")
            
    except Exception as e:
        logger.error(f"💥 Error in callback handler: {e}")
        if update and update.callback_query:
            update.callback_query.answer("Error processing request", show_alert=True)
