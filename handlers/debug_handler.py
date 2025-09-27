from telegram import ParseMode
from markup import get_menu

def debug_callback(update, context):
    query = update.callback_query
    user = query.from_user
    data = query.data
    
    print(f"🔍 [DEBUG] Callback data: '{data}'")
    print(f"🔍 [DEBUG] User ID: {user.id}")
    print(f"🔍 [DEBUG] User data: {context.user_data}")
    
    # Log semua pattern yang ada
    patterns = [
        'lihat_produk', 'beli_produk', 'topup', 'cek_status', 'riwayat', 'stock_akrab',
        'semua_riwayat', 'lihat_saldo', 'tambah_saldo', 'manajemen_produk',
        'admin_edit_produk', 'editharga', 'editdeskripsi', 'resetcustom',
        'back_main', 'back_admin', 'produk_static'
    ]
    
    query.answer(f"Debug: {data}")
    query.edit_message_text(
        f"🔍 **DEBUG INFO**\n\n"
        f"Callback: `{data}`\n"
        f"User ID: `{user.id}`\n"
        f"Patterns: {', '.join(patterns)}\n\n"
        f"Silakan screenshot ini untuk debug.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_menu(user.id)
    )
