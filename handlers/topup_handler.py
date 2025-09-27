from telegram import ParseMode
from provider_qris import generate_qris

TOPUP_NOMINAL = 3

def topup_nominal_step(update, context):
    text = update.message.text.strip()
    try:
        nominal = int(text.replace(".", "").replace(",", ""))
        if nominal < 10000:
            update.message.reply_text("❌ Nominal minimal 10.000. Masukkan kembali nominal:")
            return TOPUP_NOMINAL
        resp = generate_qris(nominal)
        if resp.get("status") != "success":
            update.message.reply_text(f"❌ Gagal generate QRIS: {resp.get('message', 'Unknown error')}")
            return ConversationHandler.END
        qris_base64 = resp.get("qris_base64")
        msg = f"💰 Silakan lakukan pembayaran Top Up sebesar <b>Rp {nominal:,}</b>\n\nScan QRIS berikut:"
        if qris_base64:
            update.message.reply_photo(
                photo=f"data:image/png;base64,{qris_base64}", 
                caption=msg, 
                parse_mode=ParseMode.HTML
            )
        else:
            update.message.reply_text(msg + "\n\n❌ QRIS tidak tersedia", parse_mode=ParseMode.HTML)
    except ValueError:
        update.message.reply_text("❌ Format nominal tidak valid. Masukkan angka:")
        return TOPUP_NOMINAL
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")
    return ConversationHandler.END
