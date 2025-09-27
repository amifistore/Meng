from telegram import ParseMode
from markup import get_menu
from utils import load_riwayat

def riwayat_user(query, context):
    user = query.from_user
    try:
        riwayat = load_riwayat()
        items = [r for r in riwayat.values() if r.get("user_id") == user.id]
        items = sorted(items, key=lambda x: x.get("waktu", ""), reverse=True)
        msg = "<b>📜 Riwayat Transaksi Anda:</b>\n\n"
        for r in items[:10]:
            msg += (
                f"⏰ {r.get('waktu','')}\n"
                f"🔢 RefID: <code>{r['reffid']}</code>\n"
                f"📦 {r['produk']} ke {r['tujuan']}\n"
                f"💰 Rp {r['harga']:,}\n"
                f"📊 Status: <b>{r['status_text']}</b>\n\n"
            )
        if not items:
            msg += "Belum ada transaksi."
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
    except Exception as e:
        query.edit_message_text(f"❌ Error memuat riwayat: {str(e)}", parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))

def semua_riwayat(query, context):
    try:
        riwayat = list(load_riwayat().values())
        riwayat = sorted(riwayat, key=lambda x: x.get("waktu", ""), reverse=True)
        msg = "<b>📜 Semua Riwayat Transaksi (max 30):</b>\n\n"
        for r in riwayat[:30]:
            msg += (
                f"⏰ {r.get('waktu','')}\n"
                f"🔢 RefID: <code>{r['reffid']}</code>\n"
                f"📦 {r['produk']} ke {r['tujuan']}\n"
                f"💰 Rp {r['harga']:,}\n"
                f"📊 Status: <b>{r['status_text']}</b>\n"
                f"👤 User: {r.get('username','-')}\n\n"
            )
        if not riwayat:
            msg += "Belum ada transaksi."
        query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=get_menu(query.from_user.id))
    except Exception as e:
        query.edit_message_text(f"❌ Error memuat riwayat: {str(e)}", parse_mode=ParseMode.HTML, reply_markup=get_menu(query.from_user.id))
