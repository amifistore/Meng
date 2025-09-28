from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from markup import get_menu
from provider import create_trx
from saldo import get_saldo_user, kurang_saldo_user
from riwayat import tambah_riwayat
import random
import time

# States
INPUT_TUJUAN, KONFIRMASI = range(2)

def handle_input_tujuan(update, context):
    user = update.message.from_user
    text = update.message.text.strip()
    
    # Cancel command
    if text == '/batal':
        context.user_data.clear()
        update.message.reply_text("❌ Order dibatalkan.", reply_markup=get_menu(user.id))
        return ConversationHandler.END
    
    # Validate phone number (min 10 digit, all digit)
    if not text.isdigit() or len(text) < 10 or len(text) > 15:
        update.message.reply_text(
            "❌ Format nomor tidak valid! Harus angka minimal 10 digit dan maksimal 15 digit.\n"
            "Contoh: 081234567890\n\n"
            "Silakan input ulang atau ketik /batal untuk membatalkan."
        )
        return INPUT_TUJUAN
    
    # Get product from context
    produk = context.user_data.get("produk")
    if not produk:
        update.message.reply_text("❌ Sesi expired. Silakan mulai order lagi.", reply_markup=get_menu(user.id))
        return ConversationHandler.END
    
    # Check saldo
    saldo = get_saldo_user(user.id)
    if saldo < produk['harga']:
        update.message.reply_text(
            f"❌ Saldo tidak cukup!\n"
            f"Produk: {produk['nama']} - Rp {produk['harga']:,}\n"
            f"Saldo kamu: Rp {saldo:,}\n\n"
            "Silakan top up terlebih dahulu.",
            reply_markup=get_menu(user.id)
        )
        return ConversationHandler.END
    
    # Save destination
    context.user_data["tujuan"] = text
    context.user_data["ref_id"] = f"TRX{random.randint(100000, 999999)}"
    
    # Modern: Gunakan tombol konfirmasi/batal
    keyboard = [
        [InlineKeyboardButton("✅ Konfirmasi", callback_data="order_konfirmasi"),
         InlineKeyboardButton("❌ Batal", callback_data="order_batal")]
    ]
    update.message.reply_text(
        f"📋 <b>KONFIRMASI ORDER</b>\n\n"
        f"🆔 Ref ID: <code>{context.user_data['ref_id']}</code>\n"
        f"📦 Produk: <b>{produk['nama']}</b>\n"
        f"💰 Harga: <b>Rp {produk['harga']:,}</b>\n"
        f"📱 Tujuan: <b>{text}</b>\n\n"
        f"Klik <b>Konfirmasi</b> untuk melanjutkan atau <b>Batal</b> untuk membatalkan.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return KONFIRMASI

def handle_konfirmasi(update, context):
    # Handler tombol inline dan fallback teks
    if update.callback_query:
        query = update.callback_query
        user = query.from_user
        query.answer()
        data = query.data
        if data == "order_batal":
            context.user_data.clear()
            query.edit_message_text("❌ Order dibatalkan.", reply_markup=get_menu(user.id))
            return ConversationHandler.END
        if data == "order_konfirmasi":
            produk = context.user_data.get("produk")
            tujuan = context.user_data.get("tujuan")
            ref_id = context.user_data.get("ref_id")
            if not all([produk, tujuan, ref_id]):
                query.edit_message_text("❌ Data order tidak lengkap. Silakan mulai lagi.", reply_markup=get_menu(user.id))
                return ConversationHandler.END
            msg_proc = query.edit_message_text("🔄 Memproses order... Silakan tunggu.")
            try:
                result = create_trx(produk['kode'], tujuan, ref_id)
                if result.get('status') == 'success':
                    kurang_saldo_user(user.id, produk['harga'], tipe="order", keterangan=f"Order {produk['kode']} tujuan {tujuan}")
                    transaksi = {
                        "ref_id": ref_id,
                        "produk": produk['nama'],
                        "kode": produk['kode'],
                        "harga": produk['harga'],
                        "tujuan": tujuan,
                        "status": "success",
                        "tanggal": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "sn" : result.get('sn', ''),
                        "response": result
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
        # fallback: jika data lain
        query.edit_message_text("❌ Pilihan tidak valid.", reply_markup=get_menu(user.id))
        return ConversationHandler.END
    else:
        user = update.message.from_user
        text = update.message.text.strip().upper()
        if text == 'BATAL':
            context.user_data.clear()
            update.message.reply_text("❌ Order dibatalkan.", reply_markup=get_menu(user.id))
            return ConversationHandler.END
        if text == 'YA':
            # Proses order sama seperti tombol Konfirmasi
            produk = context.user_data.get("produk")
            tujuan = context.user_data.get("tujuan")
            ref_id = context.user_data.get("ref_id")
            if not all([produk, tujuan, ref_id]):
                update.message.reply_text("❌ Data order tidak lengkap. Silakan mulai lagi.", reply_markup=get_menu(user.id))
                return ConversationHandler.END
            processing_msg = update.message.reply_text("🔄 Memproses order... Silakan tunggu.")
            try:
                result = create_trx(produk['kode'], tujuan, ref_id)
                if result.get('status') == 'success':
                    kurang_saldo_user(user.id, produk['harga'], tipe="order", keterangan=f"Order {produk['kode']} tujuan {tujuan}")
                    transaksi = {
                        "ref_id": ref_id,
                        "produk": produk['nama'],
                        "kode": produk['kode'],
                        "harga": produk['harga'],
                        "tujuan": tujuan,
                        "status": "success",
                        "tanggal": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "sn" : result.get('sn', ''),
                        "response": result
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
        return KONFIRMASI
