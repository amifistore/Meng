from telegram import ParseMode
from saldo import get_riwayat_saldo
from markup import get_menu, is_admin

def riwayat_callback(update, context):
    """Callback untuk tombol Riwayat transaksi user di menu utama"""
    user = update.callback_query.from_user
    update.callback_query.answer()
    riwayat_data = get_riwayat_saldo(user.id)
    if not riwayat_data:
        msg = "📄 *Riwayat Transaksi Kosong*\n\nBelum ada transaksi yang dilakukan."
    else:
        msg = "📄 *Riwayat Saldo & Topup Terakhir*\n\n"
        for i, trx in enumerate(reversed(riwayat_data[-5:]), 1):
            status = "✅" if trx[2] > 0 else "❌"
            tipe = trx[1]
            nominal = trx[2]
            ket = trx[3]
            waktu = trx[0]
            msg += f"{i}. {status} {tipe} {nominal:+,}\n"
            msg += f"   🕒 {waktu}\n   {ket}\n\n"
    update.callback_query.edit_message_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_menu(user.id)
    )

def semua_riwayat_callback(update, context):
    """Callback untuk tombol Semua Riwayat (admin) di menu admin"""
    user = update.callback_query.from_user
    update.callback_query.answer()
    if not is_admin(user.id):
        update.callback_query.edit_message_text(
            "❌ Akses ditolak.",
            reply_markup=get_menu(user.id)
        )
        return
    # Ambil semua riwayat dari database
    from saldo import get_riwayat_saldo
    all_riwayat = get_riwayat_saldo(None, admin_mode=True)
    if not all_riwayat:
        msg = "📄 *Semua Riwayat Kosong*\n\nBelum ada transaksi dari semua user."
    else:
        msg = "📄 *Semua Riwayat Transaksi*\n\n"
        total = 0
        user_map = {}
        for row in all_riwayat:
            waktu, user_id, tipe, nominal, ket = row
            if user_id not in user_map: user_map[user_id] = []
            user_map[user_id].append((waktu, tipe, nominal, ket))
            total += nominal if nominal > 0 else 0
        for user_id, transactions in user_map.items():
            msg += f"👤 User `{user_id}`:\n"
            for trx in transactions[-3:]:
                status = "✅" if trx[2] > 0 else "❌"
                msg += f"   {status} {trx[1]} {trx[2]:+,}\n   🕒 {trx[0]}\n   {trx[3]}\n"
            msg += "\n"
        msg += f"💰 *Total Transaksi: Rp {total:,}*"
    update.callback_query.edit_message_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_menu(user.id)
    )

def riwayat_user(update, context):
    """Bisa dipanggil via command (misal /riwayat) atau callback"""
    user = update.effective_user
    riwayat_data = get_riwayat_saldo(user.id)
    if not riwayat_data:
        msg = "📄 *Riwayat Transaksi Kosong*\n\nBelum ada transaksi yang dilakukan."
    else:
        msg = "📄 *Riwayat Saldo & Topup Terakhir*\n\n"
        for i, trx in enumerate(reversed(riwayat_data[-5:]), 1):
            status = "✅" if trx[2] > 0 else "❌"
            tipe = trx[1]
            nominal = trx[2]
            ket = trx[3]
            waktu = trx[0]
            msg += f"{i}. {status} {tipe} {nominal:+,}\n"
            msg += f"   🕒 {waktu}\n   {ket}\n\n"
    update.message.reply_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_menu(user.id)
    )
