from markup import produk_inline_keyboard
from produk import get_produk_list
import logging

logger = logging.getLogger(__name__)

def lihat_produk_callback(update, context):
    try:
        user = update.message.from_user
        logger.info(f"User {user.first_name} (ID: {user.id}) memilih Order Produk")
        
        # Clear previous data
        context.user_data.clear()
        
        # Get product list
        produk_list = get_produk_list()
        logger.info(f"Retrieved {len(produk_list)} products")
        
        if not produk_list:
            update.message.reply_text(
                "❌ Maaf, saat ini tidak ada produk yang tersedia.\n"
                "Silakan coba lagi beberapa saat atau hubungi admin."
            )
            return
        
        # Debug: Check if products have proper structure
        for i, produk in enumerate(produk_list[:2]):
            logger.info(f"Sample product {i}: {produk.get('kode')} - {produk.get('nama')} - Kuota: {produk.get('kuota', 'N/A')}")
        
        update.message.reply_text(
            "🛒 <b>PILIH PRODUK</b>\n\n"
            "Silakan pilih produk yang ingin dibeli:\n"
            "ℹ️ Stok ditampilkan dalam tanda kurung",
            parse_mode='HTML',
            reply_markup=produk_inline_keyboard(produk_list)
        )
        logger.info("Successfully sent product list to user")
        
    except Exception as e:
        logger.error(f"Error in lihat_produk_callback: {e}")
        update.message.reply_text(
            "❌ Terjadi kesalahan saat menampilkan produk.\n"
            "Silakan coba lagi atau hubungi admin."
        )
