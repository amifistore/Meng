from telegram import ParseMode
from utils import load_riwayat
from markup import get_menu

def riwayat_user(update, context):
    if hasattr(update, 'callback_query'):
        query = update.callback_query
        user = query.from_user
        query.answer()
    else:
        user = update.effective_user
    
    riwayat_data = load_riwayat(user.id)
    
    if not riwayat_data:
        msg = "📄 **Riwayat Transaksi Kosong**\n\nBelum ada transaksi yang dilakukan."
    else:
        msg = "📄 **Riwayat Transaksi Terakhir**\n\n"
        for i, trx in enumerate(reversed(riwayat_data[-5:]), 1):
            status = "✅" if trx.get('status') == 'success' else "❌"
            msg += f"{i}. {status} {trx.get('ref_id', 'N/A')} - {trx.get('produk', 'N/A')}\n"
            msg += f"   📱 {trx.get('tujuan', 'N/A')} | 💰 Rp {trx.get('harga', 0):,}\n"
            msg += f"   🕒 {trx.get('tanggal', 'N/A')}\n\n"
    
    if hasattr(update, 'callback_query'):
        query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=get_menu(user.id))
    else:
        update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=get_menu(user.id))

def semua_riwayat(update, context):
    from utils import load_riwayat
    from markup import is_admin
    
    query = update.callback_query
    user = query.from_user
    query.answer()
    
    if not is_admin(user.id):
        query.edit_message_text("❌ Akses ditolak.", reply_markup=get_menu(user.id))
        return
    
    all_riwayat = load_riwayat()
    
    if not all_riwayat:
        msg = "📄 **Semua Riwayat Kosong**\n\nBelum ada transaksi dari semua user."
    else:
        msg = "📄 **Semua Riwayat Transaksi**\n\n"
        total = 0
        for user_id, transactions in all_riwayat.items():
            msg += f"👤 User {user_id}:\n"
            for trx in transactions[-3:]:
                status = "✅" if trx.get('status') == 'success' else "❌"
                msg += f"   {status} {trx.get('ref_id')} - {trx.get('produk')}\n"
                total += trx.get('harga', 0)
            msg += "\n"
        msg += f"💰 **Total Transaksi: Rp {total:,}**"
    
    query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=get_menu(user.id))
