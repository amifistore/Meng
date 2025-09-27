import base64
import random
from io import BytesIO
from telegram.ext import ConversationHandler
from provider_qris import generate_qris
from PIL import Image

TOPUP_NOMINAL = 3

# Path ke template QRIS PNG (background merah-putih dengan logo QRIS)
QRIS_TEMPLATE_PATH = "qris_template.png"

# QRIS statis merchant (pastikan sesuai merchant kamu)
QRIS_STATIS = "00020101021126610014COM.GO-JEK.WWW01189360091434506469550210G4506469550303UMI51440014ID.CO.QRIS.WWW0215ID10243341364120303UMI5204569753033605802ID5923Amifi Store, Kmb, TLGSR6009BONDOWOSO61056827262070703A01630431E8"

def get_nominal_unik(nominal, min_unik=1, max_unik=99):
    """
    Generate nominal unik untuk top up (nominal + angka unik random 1-99)
    Return: total_nominal, kode_unik
    """
    kode_unik = random.randint(min_unik, max_unik)
    return nominal + kode_unik, kode_unik

def make_qris_image(qris_base64, template_path=QRIS_TEMPLATE_PATH):
    """Gabungkan QR code ke atas template QRIS background merah-putih"""
    try:
        qr_bytes = base64.b64decode(qris_base64)
        qr_img = Image.open(BytesIO(qr_bytes)).convert("RGBA")

        # Open template
        template = Image.open(template_path).convert("RGBA")

        # Resize QR code agar proporsional di template (atur sesuai area kosong template kamu)
        qr_size = (300, 300)
        qr_img = qr_img.resize(qr_size)

        # Tempelkan QR code ke template (tengah secara horizontal, atur vertikal sesuai template)
        pos = ((template.width - qr_size[0]) // 2, 430)
        template.paste(qr_img, pos, qr_img)

        # Output ke BytesIO
        output = BytesIO()
        template.save(output, format="PNG")
        output.name = "qris_final.png"
        output.seek(0)
        return output
    except Exception as e:
        return None

def topup_nominal_step(update, context):
    text = update.message.text.strip()
    try:
        nominal = int(text.replace(".", "").replace(",", ""))
        if nominal < 10000:
            update.message.reply_text("❌ Nominal minimal 10.000. Masukkan kembali nominal:")
            return TOPUP_NOMINAL

        # Generate nominal unik
        total_bayar, kode_unik = get_nominal_unik(nominal)

        resp = generate_qris(total_bayar, QRIS_STATIS)

        if resp.get("status") != "success":
            update.message.reply_text(f"❌ Gagal generate QRIS: {resp.get('message', 'Unknown error')}")
            return ConversationHandler.END

        qris_base64 = resp.get("qris_base64")
        msg = (
            f"💰 Silakan lakukan pembayaran Top Up sebesar <b>Rp {total_bayar:,}</b>\n"
            f"(Nominal unik: <b>{kode_unik:02d}</b>)\n"
            "Scan QRIS berikut (aktif 15 menit).\n\n"
            "Setelah bayar, kirim bukti transfer dan tunggu konfirmasi admin."
        )
        if qris_base64:
            img = make_qris_image(qris_base64)
            if img:
                update.message.reply_photo(photo=img, caption=msg, parse_mode="HTML")
            else:
                # Jika gagal template, kirim QR polos
                try:
                    qr_bytes = base64.b64decode(qris_base64)
                    bio = BytesIO(qr_bytes)
                    bio.name = "qris.png"
                    bio.seek(0)
                    update.message.reply_photo(photo=bio, caption=msg, parse_mode="HTML")
                except Exception as e:
                    update.message.reply_text(f"❌ Error decode QRIS: {str(e)}")
        else:
            update.message.reply_text(msg + "\n❌ QRIS tidak tersedia", parse_mode="HTML")
    except ValueError:
        update.message.reply_text("❌ Format nominal tidak valid. Masukkan angka:")
        return TOPUP_NOMINAL
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")
    return ConversationHandler.END
