import re
from flask import Flask, request, jsonify
from saldo import tambah_saldo_user
from database import get_riwayat_by_refid, update_riwayat_status
# import telegram bot init di sini (misal telegram.Bot(TOKEN))
from telegram import Bot
from config import TELEGRAM_TOKEN  # pastikan token bot

app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

# REGEX sesuai dokumentasi provider
RX = re.compile(
    r"RC=(?P<reffid>[a-f0-9-]+)\s+TrxID=(?P<trxid>\d+)\s+(?P<produk>[A-Z0-9]+)\.(?P<tujuan>\d+)\s+(?P<status_text>[A-Za-z]+)\s*(?P<keterangan>.+?)(?:\s+Saldo[\s\S]*?)?(?:\bresult=(?P<status_code>\d+))?\s*>?$",
    re.I
)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    message = request.args.get("message") or request.form.get("message") or (request.json and request.json.get("message"))
    if not message:
        return jsonify({"ok": False, "error": "message kosong"}), 400

    match = RX.search(message)
    if not match:
        return jsonify({"ok": False, "error": "format tidak dikenali"}), 200

    reffid = match.group("reffid")
    status_text = match.group("status_text")
    status_code = match.group("status_code")
    keterangan = match.group("keterangan").strip()
    sn = keterangan if "SN:" in keterangan or "SN=" in keterangan else None

    # Normalisasi status_code
    if status_code is not None:
        status_code = int(status_code)
    else:
        if re.search(r"sukses", status_text, re.I):
            status_code = 0
        elif re.search(r"gagal|batal", status_text, re.I):
            status_code = 1

    trx = get_riwayat_by_refid(reffid)
    if not trx:
        # transaksi tidak ditemukan, log investigasi!
        return jsonify({"ok": False, "error": "transaksi tidak ditemukan"}), 200

    # trx: (id, ref_id, user_id, produk_kode, tujuan, harga, tanggal, status, keterangan)
    user_id = trx[2]
    harga = trx[5]
    produk_kode = trx[3]
    tujuan = trx[4]

    # Refund saldo jika gagal/batal
    if status_code == 1 or re.search(r"gagal|batal", status_text, re.I):
        tambah_saldo_user(user_id, harga, tipe="refund", keterangan=f"Refund transaksi gagal/batal {reffid}")
        update_riwayat_status(reffid, "GAGAL", keterangan)
        # Notifikasi ke user
        bot.send_message(
            chat_id=user_id,
            text=(
                f"❌ <b>TRANSAKSI GAGAL/BATAL</b>\n\n"
                f"RefID: <code>{reffid}</code>\n"
                f"Produk: <b>{produk_kode}</b>\n"
                f"Tujuan: <b>{tujuan}</b>\n"
                f"Saldo dikembalikan: <b>Rp {harga:,}</b>\n"
                f"Status: <b>{status_text}</b>\n"
                f"Info: {keterangan}"
            ),
            parse_mode="HTML"
        )

    # SN/Serial Number Notifikasi jika sukses
    elif status_code == 0 or re.search(r"sukses", status_text, re.I):
        update_riwayat_status(reffid, "SUKSES", keterangan)
        if sn:
            bot.send_message(
                chat_id=user_id,
                text=(
                    f"✅ <b>TRANSAKSI SUKSES</b>\n\n"
                    f"RefID: <code>{reffid}</code>\n"
                    f"Produk: <b>{produk_kode}</b>\n"
                    f"Tujuan: <b>{tujuan}</b>\n"
                    f"SN: <code>{sn}</code>\n"
                    f"Info: {keterangan}"
                ),
                parse_mode="HTML"
            )
        else:
            bot.send_message(
                chat_id=user_id,
                text=(
                    f"✅ <b>TRANSAKSI SUKSES</b>\n\n"
                    f"RefID: <code>{reffid}</code>\n"
                    f"Produk: <b>{produk_kode}</b>\n"
                    f"Tujuan: <b>{tujuan}</b>\n"
                    f"Info: {keterangan}"
                ),
                parse_mode="HTML"
            )

    else:
        # Status tidak dikenali, log untuk investigasi
        bot.send_message(
            chat_id=user_id,
            text=(
                f"❔ <b>STATUS TIDAK DIKENALI</b>\n\n"
                f"RefID: <code>{reffid}</code>\n"
                f"Status: <b>{status_text}</b>\n"
                f"Info: {keterangan}"
            ),
            parse_mode="HTML"
        )

    return jsonify({"ok": True, "parsed": match.groupdict()}), 200

# Flask run: app.run(host="0.0.0.0", port=PORT)
