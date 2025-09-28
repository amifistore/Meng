from telegram import ParseMode
from saldo import get_riwayat_saldo, get_all_user_ids
from topup import get_riwayat_topup_user
from markup import get_menu, is_admin

def riwayat_callback(update, context):
    """Callback untuk tombol Riwayat transaksi user di menu utama"""
    user = update.callback_query.from_user
    update.callback_query.answer()
    riwayat_data = get_riwayat_saldo(user.id)
    topup_data = get_riwayat_topup_user(user.id)
    msg = ""
    if not riwayat_data and not topup_data:
        msg = "📄 *Riwayat Transaksi Kosong*\n\nBelum ada transaksi yang dilakukan."
    else:
        msg = "📄 *Riwayat Saldo & Topup Terakhir*\n\n"
        # Saldo/Order
        if riwayat_data:
            msg += "*Saldo/Order Terakhir:*\n"
            for i, trx in enumerate(reversed(riwayat_data[-5:]), 1):
                status = "✅" if trx[2] > 0 else "❌"
                tipe = trx[1]
                nominal = trx[2]
                ket = trx[3]
                waktu = trx[0]
                msg += f"{i}. {status} {tipe} {nominal:+,}\n"
                msg += f"   🕒 {waktu}\n   {ket}\n\n"
        # Topup
        if topup_data:
            msg += "*Topup Terakhir:*\n"
            for i, tup in enumerate(topup_data[:5], 1):
                msg += f"{i}. ID: `{tup[0]}` | Rp {tup[1]:,} | Status: {tup[2]} | {tup[3]}\n"
    info_text, markup = get_menu(user.id)
    update.callback_query.edit_message_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

def semua_riwayat_callback(update, context):
    """Callback untuk tombol Semua Riwayat (admin) di menu admin"""
    user = update.callback_query.from_user
    update.callback_query.answer()
    if not is_admin(user.id):
        info_text, markup = get_menu(user.id)
        update.callback_query.edit_message_text(
            "❌ Akses ditolak.",
            reply_markup=markup
        )
        return
    # FIX: Remove admin_mode keyword, use user_id=None and set limit
    all_riwayat = get_riwayat_saldo(None, limit=50)
    # Ambil semua topup dari semua user
    user_map = {}
    total = 0
    if all_riwayat:
        for row in all_riwayat:
            waktu, user_id, tipe, nominal, ket = row
            if user_id not in user_map:
                user_map[user_id] = {"order": [], "topup": []}
            user_map[user_id]["order"].append((waktu, tipe, nominal, ket))
            total += nominal if nominal > 0 else 0
    for uid in get_all_user_ids():
        tups = get_riwayat_topup_user(uid)
        if tups:
            if uid not in user_map:
                user_map[uid] = {"order": [], "topup": []}
            user_map[uid]["topup"].extend(tups)
    if not user_map:
        msg = "📄 *Semua Riwayat Kosong*\n\nBelum ada transaksi dari semua user."
    else:
        msg = "📄 *Semua Riwayat Transaksi*\n\n"
        for user_id, transaksi in user_map.items():
            msg += f"👤 User `{user_id}`:\n"
            for trx in transaksi["order"][-3:]:
                status = "✅" if trx[2] > 0 else "❌"
                msg += f"   {status} {trx[1]} {trx[2]:+,}\n   🕒 {trx[0]}\n   {trx[3]}\n"
            for tup in transaksi["topup"][:2]:
                msg += f"   💸 Topup ID: `{tup[0]}` | Rp {tup[1]:,} | Status: {tup[2]} | {tup[3]}\n"
            msg += "\n"
        msg += f"💰 *Total Transaksi: Rp {total:,}*"
    info_text, markup = get_menu(user.id)
    update.callback_query.edit_message_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

def riwayat_user(update, context):
    """Bisa dipanggil via command (misal /riwayat) atau callback"""
    user = update.effective_user
    riwayat_data = get_riwayat_saldo(user.id)
    topup_data = get_riwayat_topup_user(user.id)
    msg = ""
    if not riwayat_data and not topup_data:
        msg = "📄 *Riwayat Transaksi Kosong*\n\nBelum ada transaksi yang dilakukan."
    else:
        msg = "📄 *Riwayat Saldo & Topup Terakhir*\n\n"
        if riwayat_data:
            msg += "*Saldo/Order Terakhir:*\n"
            for i, trx in enumerate(reversed(riwayat_data[-5:]), 1):
                status = "✅" if trx[2] > 0 else "❌"
                tipe = trx[1]
                nominal = trx[2]
                ket = trx[3]
                waktu = trx[0]
                msg += f"{i}. {status} {tipe} {nominal:+,}\n"
                msg += f"   🕒 {waktu}\n   {ket}\n\n"
        if topup_data:
            msg += "*Topup Terakhir:*\n"
            for i, tup in enumerate(topup_data[:5], 1):
                msg += f"{i}. ID: `{tup[0]}` | Rp {tup[1]:,} | Status: {tup[2]} | {tup[3]}\n"
    info_text, markup = get_menu(user.id)
    update.message.reply_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )
