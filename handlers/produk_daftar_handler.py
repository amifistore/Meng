def produk_pilih_callback(update, context):
    query = update.callback_query
    query.answer()
    data = query.data
    if data.startswith("produk|"):
        kode = data.split("|")[1]
        context.user_data["order_produk_kode"] = kode
        msg = f"Masukkan nomor tujuan untuk produk <b>{kode}</b> (misal: 08123456789)"
        query.edit_message_text(msg, parse_mode="HTML")
        # Next: input_tujuan_step
