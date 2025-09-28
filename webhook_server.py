import re
from saldo import tambah_saldo_user  # pastikan ini sudah benar
from database import update_riwayat_status, get_riwayat_by_refid

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    message = request.args.get("message") or request.form.get("message") or (request.json and request.json.get("message"))
    if not message:
        return {"ok": False, "error": "message kosong"}, 400

    # Regex sesuai provider
    RX = re.compile(
        r"RC=(?P<reffid>[a-f0-9-]+)\s+TrxID=(?P<trxid>\d+)\s+(?P<produk>[A-Z0-9]+)\.(?P<tujuan>\d+)\s+(?P<status_text>[A-Za-z]+)\s*(?P<keterangan>.+?)(?:\s+Saldo[\s\S]*?)?(?:\bresult=(?P<status_code>\d+))?\s*>?$",
        re.I
    )
    match = RX.search(message)
    if not match:
        return {"ok": False, "error": "format tidak dikenali"}, 200

    reffid = match.group("reffid")
    status_text = match.group("status_text")
    status_code = match.group("status_code")
    keterangan = match.group("keterangan").strip()

    # Normalisasi status_code
    if status_code is not None:
        status_code = int(status_code)
    else:
        if re.search(r"sukses", status_text, re.I):
            status_code = 0
        elif re.search(r"gagal|batal", status_text, re.I):
            status_code = 1

    # Ambil data transaksi dari database via reffid
    trx = get_riwayat_by_refid(reffid)
    if not trx:
        # transaksi tidak ditemukan, log investigasi!
        return {"ok": False, "error": "transaksi tidak ditemukan"}, 200

    user_id = trx[2]
    harga = trx[5]

    # PATCH: Penanganan pesanan gagal/batal!
    if status_code == 1 or re.search(r"gagal|batal", status_text, re.I):
        # Refund saldo user!
        tambah_saldo_user(user_id, harga, tipe="refund", keterangan=f"Refund transaksi gagal/batal {reffid}")
        update_riwayat_status(reffid, "GAGAL", keterangan)
        # Kamu bisa tambahkan notifikasi ke user di sini (via bot Telegram)
        print(f"[WEBHOOK] Refund saldo user {user_id} sebesar {harga} untuk transaksi gagal {reffid}")

    elif status_code == 0 or re.search(r"sukses", status_text, re.I):
        update_riwayat_status(reffid, "SUKSES", keterangan)
        # Transaksi sukses, saldo sudah dipotong saat order

    else:
        print(f"[WEBHOOK] Status tidak dikenali untuk reffid {reffid}")

    return {"ok": True, "parsed": match.groupdict()}, 200
