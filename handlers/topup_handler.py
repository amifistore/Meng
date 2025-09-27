import base64
from io import BytesIO
from telegram.ext import ConversationHandler
from provider_qris import generate_qris

def topup_nominal_step(update, context):
    text = update.message.text.strip()
    try:
        nominal = int(text.replace(".", "").replace(",", ""))
        if nominal < 10000:
            update.message.reply_text("❌ Nominal minimal 10.000. Masukkan kembali nominal:")
            return TOPUP_NOMINAL

        # Ambil QRIS statis, bisa dari config, produk, atau hardcode
        qris_statis = "XXXE3353COM.GO-JEK.WWWVDXXX44553463.CO.QRIS.WWXXXX4664XX.MERCHANT ENTE, XX65646XXXXTY5YY"
        resp = generate_qris(nominal, qris_statis)

        if resp.get("status") != "success":
            update.message.reply_text(f"❌ Gagal generate QRIS: {resp.get('message', 'Unknown error')}")
            return ConversationHandler.END

        qris_base64 = resp.get("qris_base64")
        msg = f"💰 Silakan lakukan pembayaran Top Up sebesar <b>Rp {nominal:,}</b>\n\nScan QRIS berikut:"
        if qris_base64:
            try:
                # Decode base64 ke bytes
                img_bytes = base64.b64decode(qris_base64)
                bio = BytesIO(img_bytes)
                bio.name = "qris.png"
                bio.seek(0)
                update.message.reply_photo(
                    photo=bio,
                    caption=msg,
                    parse_mode="HTML"
                )
            except Exception as e:
                update.message.reply_text(f"❌ Error decode gambar QRIS: {str(e)}")
        else:
            update.message.reply_text(msg + "\n\n❌ QRIS tidak tersedia", parse_mode="HTML")
    except ValueError:
        update.message.reply_text("❌ Format nominal tidak valid. Masukkan angka:")
        return TOPUP_NOMINAL
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")
    return ConversationHandler.END
