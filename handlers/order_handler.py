from telegram import ParseMode
from telegram.ext import ConversationHandler
from markup import reply_main_menu
from provider import create_trx
from saldo import kurang_saldo_user
from riwayat import tambah_riwayat
import time

# IMPORT DARI FILE TERPUSAT
from handlers import KONFIRMASI

import logging
logger = logging.getLogger(__name__)

def handle_konfirmasi(update, context):
    logger.info("🎯 handle_konfirmasi DIPANGGIL")
    
    if update.callback_query:
        query = update.callback_query
        user = query.from_user
        query.answer()
        data = query.data
        
        logger.info(f"🔘 Callback confirmation: {data}")
        
        if data == "order_batal":
            logger.info("❌ User canceled order via button")
            context.user_data.clear()
            query.edit_message_text("❌ Order dibatalkan.", reply_markup=reply_main_menu(user.id))
            return ConversationHandler.END
            
        if data == "order_konfirmasi":
            # ... (rest of your existing code)
            pass
            
    else:
        # ... (rest of your existing code for text confirmation)
        pass
        
    return KONFIRMASI
