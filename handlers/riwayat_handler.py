from telegram import ParseMode
from utils import load_riwayat
from markup import get_menu

def riwayat_callback(update, context):
    """Callback untuk tombol Riwayat transaksi user di menu utama"""
    user = update.callback_query.from_user
    update.callback_query.answer()
    riwayat_data = load_riwayat(user.id)
    if not riwayat_data:
        msg = "📄 *Riwayat Transaksi Kosong*\n\nBelum ada transaksi yang dilakukan."
    else:
        msg = "📄 *Riwayat Transaksi Terakhir*\n\n"
        for i, trx in enumerate(reversed(riwayat_data[-5:]), 1):
            status = "✅" if trx.get('status') == 'success' else "❌"
            msg += f"{i}. {status} {trx.get('ref_id', 'N/A')} - {trx.get('produk', 'N/A')}\n"
            msg += f"   📱 {trx.get('tujuan', 'N/A')} | 💰 Rp {trx.get('harga', 0):,}\n"
            msg += f"   🕒 {trx.get('tanggal', 'N/A')}\n\n"
    update.callback_query.edit_message_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_menu(user.id)
    )

def semua_riwayat_callback(update, context):
    """Callback untuk tombol Semua Riwayat (admin) di menu admin"""
    from markup import is_admin
    user = update.callback_query.from_user
    update.callback_query.answer()
    if not is_admin(user.id):
        update.callback_query.edit_message_text(
            "❌ Akses ditolak.",
            reply_markup=get_menu(user.id)
        )
        return
    all_riwayat = load_riwayat()
    if not all_riwayat:
        msg = "📄 *Semua Riwayat Kosong*\n\nBelum ada transaksi dari semua user."
    else:
        msg = "📄 *Semua Riwayat Transaksi*\n\n"
        total = 0
        for user_id, transactions in all_riwayat.items():
            msg += f"👤 User `{user_id}`:\n"
            for trx in transactions[-3:]:
                status = "✅" if trx.get('status') == 'success' else "❌"
                msg += f"   {status} {trx.get('ref_id', 'N/A')} - {trx.get('produk', 'N/A')}\n"
                total += trx.get('harga', 0)
            msg += "\n"
        msg += f"💰 *Total Transaksi: Rp {total:,}*"
    update.callback_query.edit_message_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_menu(user.id)
    )

# Untuk command atau penggunaan lain (optional)
def riwayat_user(update, context):
    """Bisa dipanggil via command (misal /riwayat) atau callback"""
    user = update.effective_user
    riwayat_data = load_riwayat(user.id)
    if not riwayat_data:
        msg = "📄 *Riwayat Transaksi Kosong*\n\nBelum ada transaksi yang dilakukan."
    else:
        msg = "📄 *Riwayat Transaksi Terakhir*\n\n"
        for i, trx in enumerate(reversed(riwayat_data[-5:]), 1):
            status = "✅" if trx.get('status') == 'success' else "❌"
            msg += f"{i}. {status} {trx.get('ref_id', 'N/A')} - {trx.get('produk', 'N/A')}\n"
            msg += f"   📱 {trx.get('tujuan', 'N/A')} | 💰 Rp {trx.get('harga', 0):,}\n"
            msg += f"   🕒 {trx.get('tanggal', 'N/A')}\n\n"
    update.message.reply_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_menu(user.id)
    )
