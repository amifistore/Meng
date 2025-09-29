def lihat_produk_callback(update, context):
    produk_list = [
        {"nama": "Pulsa 50rb", "kode": "pulsa50"},
        {"nama": "Paket Data 10GB", "kode": "data10"},
        {"nama": "Voucher Game", "kode": "gamevouch"}
    ]
    msg = "🛒 Daftar produk:\n"
    for produk in produk_list:
        msg += f"- {produk['nama']} ({produk['kode']})\n"
    update.message.reply_text(msg)
