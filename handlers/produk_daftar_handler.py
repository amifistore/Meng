from produk import get_produk_list

def lihat_produk_callback(update, context):
    produk_list = get_produk_list()
    msg = "🛒 Daftar Produk:\n"
    for produk in produk_list:
        msg += (
            f"- {produk['nama']} ({produk['kode']})\n"
            f"  Harga: Rp{produk['harga']:,}\n"
            f"  Stok: {produk.get('kuota', 0)}\n"
            f"  Deskripsi: {produk.get('deskripsi','')}\n\n"
        )
    update.message.reply_text(msg)
