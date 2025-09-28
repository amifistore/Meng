from telegram import ParseMode
from riwayat import cari_riwayat_order
from topup import cari_riwayat_topup
from markup import get_menu

def cari_riwayat_order_callback(update, context):
    user = update.callback_query.from_user
    update.callback_query.answer()
    keyword = context.args[0] if context.args else ""
    results = cari_riwayat_order(user_id=user.id, ref_id=keyword)
    if not results:
        msg = f"📄 Tidak ditemukan riwayat order dengan kata kunci: <code>{keyword}</code>"
    else:
        msg = f"📄 Hasil pencarian order dengan kata kunci: <code>{keyword}</code>\n\n"
        for i, trx in enumerate(results, 1):
            msg += f"{i}. {trx[0]} | {trx[1]} | Rp {trx[2]:,} | Tujuan: {trx[3]} | Status: {trx[4]} | {trx[5]}\n"
    update.callback_query.edit_message_text(
        msg,
        parse_mode=ParseMode.HTML,
        reply_markup=get_menu(user.id)
    )

def cari_riwayat_topup_callback(update, context):
    user = update.callback_query.from_user
    update.callback_query.answer()
    keyword = context.args[0] if context.args else ""
    results = cari_riwayat_topup(user_id=user.id, status=keyword if keyword else None)
    if not results:
        msg = f"📄 Tidak ditemukan riwayat topup dengan status: <code>{keyword}</code>"
    else:
        msg = f"📄 Hasil pencarian topup dengan status: <code>{keyword}</code>\n\n"
        for i, t in enumerate(results, 1):
            msg += f"{i}. ID: {t[0]} | Rp {t[1]:,} | Status: {t[2]} | {t[3]}\n"
    update.callback_query.edit_message_text(
        msg,
        parse_mode=ParseMode.HTML,
        reply_markup=get_menu(user.id)
    )
