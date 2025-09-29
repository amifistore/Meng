from markup import reply_main_menu
from provider import create_trx
from saldo import kurang_saldo_user
from riwayat import tambah_riwayat
import time

def handle_konfirmasi(update, context):
    if update.callback_query:
        query = update.callback_query
        user = query.from_user
        query.answer()
        data = query.data
        if data == "order_batal":
            context.user_data.clear()
            query.edit_message_text("❌ Order dibatalkan.", reply_markup=reply_main_menu(user.id))
            return ConversationHandler.END
        if data == "order_konfirmasi":
            produk = context.user_data.get("produk")
            tujuan = context.user_data.get("tujuan")
            ref_id = context.user_data.get("ref_id")
            if not all([produk, tujuan, ref_id]):
                query.edit_message_text("❌ Data order tidak lengkap. Silakan mulai lagi.", reply_markup=reply_main_menu(user.id))
                return ConversationHandler.END
            msg_proc = query.edit_message_text("🔄 Memproses order... Silakan tunggu.")
            try:
                result = create_trx(produk['kode'], tujuan, ref_id)
                status = str(result.get('status', '')).lower()
                message = str(result.get('message', '')).lower()
                status_code = result.get('status_code', None)
                if (
                    'sukses' in status or
                    status == 'success' or
                    'success' in message or
                    status == 'ok' or
                    (status_code is not None and str(status_code) == '0')
                ):
                    kurang_saldo_user(user.id, produk['harga'], tipe="order", keterangan=f"Order {produk['kode']} tujuan {tujuan}")
                    transaksi = {
                        "ref_id": ref_id,
                        "kode": produk['kode'],
                        "tujuan": tujuan,
                        "harga": produk['harga'],
                        "tanggal": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "success",
                        "sn": result.get('sn', ''),
                        "keterangan": result.get('message', '')
                    }
                    tambah_riwayat(user.id, transaksi)
                    msg_proc.edit_text(
                        f"✅ <b>ORDER BERHASIL</b>\n\n"
                        f"🆔 Ref ID: <code>{ref_id}</code>\n"
                        f"📦 Produk: <b>{produk['nama']}</b>\n"
                        f"💰 Harga: <b>Rp {produk['harga']:,}</b>\n"
                        f"📱 Tujuan: <b>{tujuan}</b>\n"
                        f"🎫 SN: <code>{result.get('sn', 'N/A')}</code>\n\n"
                        f"💾 Status: <b>{result.get('message', 'Success')}</b>",
                        parse_mode=ParseMode.HTML
                    )
                else:
                    error_msg = result.get('message', 'Unknown error')
                    msg_proc.edit_text(
                        f"❌ <b>ORDER GAGAL</b>\n\n"
                        f"🆔 Ref ID: <code>{ref_id}</code>\n"
                        f"📦 Produk: <b>{produk['nama']}</b>\n"
                        f"💬 Error: <b>{error_msg}</b>\n\n"
                        f"Silakan coba lagi atau hubungi admin.",
                        parse_mode=ParseMode.HTML
                    )
            except Exception as e:
                msg_proc.edit_text(
                    f"❌ <b>ERROR SYSTEM</b>\n\n"
                    f"Terjadi error saat memproses: <code>{str(e)}</code>\n"
                    f"Silakan hubungi admin.",
                    parse_mode=ParseMode.HTML
                )
            finally:
                context.user_data.clear()
                return ConversationHandler.END
        query.edit_message_text("❌ Pilihan tidak valid.", reply_markup=reply_main_menu(user.id))
        return ConversationHandler.END
    else:
        user = update.message.from_user
        text = update.message.text.strip().upper()
        if text == 'BATAL':
            context.user_data.clear()
            update.message.reply_text("❌ Order dibatalkan.", reply_markup=reply_main_menu(user.id))
            return ConversationHandler.END
        if text == 'YA':
            produk = context.user_data.get("produk")
            tujuan = context.user_data.get("tujuan")
            ref_id = context.user_data.get("ref_id")
            if not all([produk, tujuan, ref_id]):
                update.message.reply_text("❌ Data order tidak lengkap. Silakan mulai lagi.", reply_markup=reply_main_menu(user.id))
                return ConversationHandler.END
            processing_msg = update.message.reply_text("🔄 Memproses order... Silakan tunggu.")
            try:
                result = create_trx(produk['kode'], tujuan, ref_id)
                status = str(result.get('status', '')).lower()
                message = str(result.get('message', '')).lower()
                status_code = result.get('status_code', None)
                if (
                    'sukses' in status or
                    status == 'success' or
                    'success' in message or
                    status == 'ok' or
                    (status_code is not None and str(status_code) == '0')
                ):
                    kurang_saldo_user(user.id, produk['harga'], tipe="order", keterangan=f"Order {produk['kode']} tujuan {tujuan}")
                    transaksi = {
                        "ref_id": ref_id,
                        "kode": produk['kode'],
                        "tujuan": tujuan,
                        "harga": produk['harga'],
                        "tanggal": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "success",
                        "sn": result.get('sn', ''),
                        "keterangan": result.get('message', '')
                    }
                    tambah_riwayat(user.id, transaksi)
                    processing_msg.edit_text(
                        f"✅ <b>ORDER BERHASIL</b>\n\n"
                        f"🆔 Ref ID: <code>{ref_id}</code>\n"
                        f"📦 Produk: <b>{produk['nama']}</b>\n"
                        f"💰 Harga: <b>Rp {produk['harga']:,}</b>\n"
                        f"📱 Tujuan: <b>{tujuan}</b>\n"
                        f"🎫 SN: <code>{result.get('sn', 'N/A')}</code>\n\n"
                        f"💾 Status: <b>{result.get('message', 'Success')}</b>",
                        parse_mode=ParseMode.HTML
                    )
                else:
                    error_msg = result.get('message', 'Unknown error')
                    processing_msg.edit_text(
                        f"❌ <b>ORDER GAGAL</b>\n\n"
                        f"🆔 Ref ID: <code>{ref_id}</code>\n"
                        f"📦 Produk: <b>{produk['nama']}</b>\n"
                        f"💬 Error: <b>{error_msg}</b>\n\n"
                        f"Silakan coba lagi atau hubungi admin.",
                        parse_mode=ParseMode.HTML
                    )
            except Exception as e:
                processing_msg.edit_text(
                    f"❌ <b>ERROR SYSTEM</b>\n\n"
                    f"Terjadi error saat memproses: <code>{str(e)}</code>\n"
                    f"Silakan hubungi admin.",
                    parse_mode=ParseMode.HTML
                )
            finally:
                context.user_data.clear()
                return ConversationHandler.END
        update.message.reply_text(
            "❌ Konfirmasi tidak valid!\n"
            "Ketik YA untuk konfirmasi atau BATAL untuk membatalkan.",
            parse_mode=ParseMode.HTML
        )
        return 2  # KONFIRMASI
