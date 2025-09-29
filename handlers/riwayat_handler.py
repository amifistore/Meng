from telegram import ParseMode
from saldo import get_riwayat_saldo, get_all_user_ids
from topup import get_riwayat_topup_user
from markup import get_menu
from config import ADMIN_IDS

def is_admin(user_id):
    return user_id in ADMIN_IDS

def riwayat_callback(update, context):
    user = update.callback_query.from_user
    update.callback_query.answer()
    riwayat_data = get_riwayat_saldo(user.id)
    topup_data = get_riwayat_topup_user(user.id)
    msg = ""
    if not riwayat_data and not topup_data:
        msg = "📄 *Riwayat Transaksi Kosong*\n\nBelum ada transaksi yang dilakukan."
    else:
        msg = "📄 *Riwayat Saldo & Topup Terakhir*\n\n"
        if riwayat_data:
            msg += "*Saldo/Order Terakhir:*\n"
            # riwayat_data adalah list of dict
            for i, trx in enumerate(reversed(riwayat_data[-5:]), 1):
                nominal_int = int(trx.get("perubahan", 0))
                status = "✅" if nominal_int > 0 else "❌"
                tipe = trx.get("tipe", "")
                ket = trx.get("keterangan", "")
                waktu = trx.get("tanggal", "")
                msg += f"{i}. {status} {tipe} {nominal_int:+,}\n"
                msg += f"   🕒 {waktu}\n   {ket}\n\n"
        if topup_data:
            msg += "*Topup Terakhir:*\n"
            # topup_data adalah list of dict
            for i, tup in enumerate(topup_data[:5], 1):
                topup_nominal = int(tup.get("nominal", 0))
                status = tup.get("status", "")
                tanggal = tup.get("tanggal", "")
                msg += f"{i}. ID: `{tup.get('id')}` | Rp {topup_nominal:,} | Status: {status} | {tanggal}\n"
    _, markup = get_menu(is_admin(user.id))
    update.callback_query.edit_message_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

def semua_riwayat_callback(update, context):
    user = update.callback_query.from_user
    update.callback_query.answer()
    if not is_admin(user.id):
        _, markup = get_menu(is_admin(user.id))
        update.callback_query.edit_message_text(
            "❌ Akses ditolak.",
            reply_markup=markup
        )
        return
    all_riwayat = get_riwayat_saldo(None, limit=50, admin_mode=True)
    user_map = {}
    total = 0
    if all_riwayat:
        for row in all_riwayat:
            waktu, user_id, tipe, nominal, ket = row
            nominal_int = int(nominal) if nominal is not None else 0
            if user_id not in user_map:
                user_map[user_id] = {"order": [], "topup": []}
            user_map[user_id]["order"].append((waktu, tipe, nominal_int, ket))
            total += nominal_int if nominal_int > 0 else 0
    for uid in get_all_user_ids():
        tups = get_riwayat_topup_user(uid)
        if tups:
            if uid not in user_map:
                user_map[uid] = {"order": [], "topup": []}
            user_map[uid]["topup"].extend([
                (tup.get("id"), int(tup.get("nominal", 0)), tup.get("status", ""), tup.get("tanggal", "")) for tup in tups
            ])
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
    _, markup = get_menu(is_admin(user.id))
    update.callback_query.edit_message_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )
