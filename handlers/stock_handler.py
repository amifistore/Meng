import requests
from telegram import Update
from telegram.ext import CallbackContext
from utils import format_stock_akrab
from markup import get_menu

PROVIDER_STOCK_URL = "https://panel.khfy-store.com/api_v3/cek_stock_akrab"

def stock_akrab_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    try:
        resp = requests.get(PROVIDER_STOCK_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        msg = format_stock_akrab(data)
    except Exception as e:
        msg = f"<b>❌ Gagal mengambil data stok dari provider:</b>\n{str(e)}"
    query.edit_message_text(
        msg,
        parse_mode="HTML",
        reply_markup=get_menu(query.from_user.id)
    )
