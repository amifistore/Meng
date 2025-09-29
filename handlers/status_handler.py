from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import requests
from markup import reply_main_menu

INPUT_REFID = 100

PROVIDER_STATUS_URL = "https://panel.khfy-store.com/api_v2/history"

def cek_status_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    query.edit_message_text(
        "🔎 Silakan masukkan kode/ID transaksi (refid) yang ingin dicek statusnya:",
        reply_markup=reply_main_menu(user_id)
    )
    return INPUT_REFID

def input_refid_step(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    api_key = context.bot_data.get("provider_api_key")  # Set api_key di bot_data pada start up (main.py)
    refid = text
    if not api_key or not refid:
        update.message.reply_text("❌ API Key belum diset atau refid kosong.", reply_markup=reply_main_menu(update.message.from_user.id))
        return ConversationHandler.END

    url = f"{PROVIDER_STATUS_URL}?api_key={api_key}&refid={refid}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if "status" in data and data["status"] == "success":
            hasil = data.get("result", {})
            trxid = hasil.get("trxid", "-")
            produk = hasil.get("produk", "-")
            tujuan = hasil.get("tujuan", "-")
            status_text = hasil.get("status_text", "-")
            keterangan = hasil.get("keterangan", "-")
            msg = (
                f"📝 <b>STATUS TRANSAKSI</b>\n"
                f"RefID: <code>{refid}</code>\n"
                f"TrxID: <code>{trxid}</code>\n"
                f"Produk: <b>{produk}</b>\n"
                f"Tujuan: <b>{tujuan}</b>\n"
                f"Status: <b>{status_text}</b>\n"
                f"Keterangan: <i>{keterangan}</i>"
            )
        else:
            msg = f"❌ Status tidak ditemukan atau gagal.\n{data.get('message', '')}"
        update.message.reply_text(msg, parse_mode="HTML", reply_markup=reply_main_menu(update.message.from_user.id))
    except Exception as e:
        update.message.reply_text(f"❌ Error mengambil status: {e}", reply_markup=reply_main_menu(update.message.from_user.id))
    return ConversationHandler.END
