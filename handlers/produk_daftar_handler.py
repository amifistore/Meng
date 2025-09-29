from markup import produk_inline_keyboard
from produk import get_produk_list

def lihat_produk_callback(update, context):
    produk_list = get_produk_list()
    update.message.reply_text(
        "🛒 Pilih produk yang ingin dibeli:",
        reply_markup=produk_inline_keyboard(produk_list)
    )
