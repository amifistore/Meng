from telegram import ParseMode
from markup import get_menu
from provider import create_trx
from utils import get_saldo, set_saldo, load_riwayat, save_riwayat

KONFIRMASI = 2

def konfirmasi_step(update, context):
    text = update.message.text.strip().upper()
    if text == "BATAL":
        update.message.reply_text("❌ Transaksi dibatalkan.", reply_markup=get_menu(update.effective_user.id))
        return ConversationHandler.END
    if text != "YA":
        update.message.reply_text("❌ Ketik 'YA' untuk konfirmasi atau 'BATAL' untuk batal.")
        return KONFIRMASI
    
    p = context.user_data.get("produk")
    tujuan = context.user_data.get("tujuan")
    if not p or not tujuan:
        update.message.reply_text("❌ Data transaksi tidak lengkap.", reply_markup=get_menu(update.effective_user.id))
        return ConversationHandler.END
    harga = p["harga"]
    saldo = get_saldo()
    if saldo < harga:
        update.message.reply_text("❌ Saldo bot tidak cukup.", reply_markup=get_menu(update.effective_user.id))
        return ConversationHandler.END
    try:
        data = create_trx(p["kode"], tujuan)
        if not data or not data.get("refid"):
            err_msg = data.get("message", "Gagal membuat transaksi.") if data else "Tidak ada respon API."
            update.message.reply_text(f"❌ Gagal membuat transaksi:\n<b>{err_msg}</b>", parse_mode=ParseMode.HTML, reply_markup=get_menu(update.effective_user.id))
            return ConversationHandler.END
        riwayat = load_riwayat()
        refid = data["refid"]
        user = update.effective_user
        riwayat[refid] = {
            "trxid": data.get("trxid", ""),
            "reffid": refid,
            "produk": p["kode"],
            "tujuan": tujuan,
            "status_text": data.get("status", "pending"),
            "status_code": None,
            "keterangan": data.get("message", ""),
            "waktu": data.get("waktu", ""),
            "harga": harga,
            "user_id": user.id,
            "username": user.username or "",
            "nama": user.full_name,
        }
        save_riwayat(riwayat)
        set_saldo(saldo - harga)
        update.message.reply_text(
            f"✅ Transaksi berhasil!\n\n📦 Produk: {p['kode']}\n📱 Tujuan: {tujuan}\n🔢 RefID: <code>{refid}</code>\n📊 Status: {data.get('status','pending')}\n💰 Saldo bot: Rp {saldo-harga:,}",
            parse_mode=ParseMode.HTML,
            reply_markup=get_menu(user.id)
        )
    except Exception as e:
        update.message.reply_text(
            f"❌ Error membuat transaksi: {str(e)}",
            parse_mode=ParseMode.HTML,
            reply_markup=get_menu(update.effective_user.id)
        )
    finally:
        context.user_data.clear()
    return ConversationHandler.END
