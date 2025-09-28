import time
import logging
from telegram.ext import ConversationHandler

# Import dari modul lain (pastikan file saldo.py dan riwayat.py sudah ada)
from saldo import kurang_saldo_user
from riwayat import tambah_riwayat

logger = logging.getLogger(__name__)

def safe_int_convert(value):
    """Convert value to integer safely"""
    try:
        if isinstance(value, str):
            cleaned = ''.join(c for c in value if c.isdigit() or c == '-')
            return int(cleaned) if cleaned else 0
        elif isinstance(value, (int, float)):
            return int(value)
        else:
            return 0
    except (ValueError, TypeError):
        return 0

def handle_konfirmasi(update, context):
    """Handler utama untuk proses konfirmasi order"""
    try:
        # Ambil data dari context
        user = update.effective_user
        produk = context.user_data.get('produk')
        tujuan = context.user_data.get('tujuan')
        ref_id = context.user_data.get('ref_id')
        sn = context.user_data.get('sn', '-')
        result = context.user_data.get('order_result', {})
        msg_proc = update.callback_query if getattr(update, "callback_query", None) else update.message

        if not produk or not tujuan or not ref_id:
            msg_proc.edit_text(
                "❌ Data order tidak lengkap. Silakan ulangi proses order.",
                parse_mode="HTML"
            )
            context.user_data.clear()
            return ConversationHandler.END

        # Pastikan harga selalu integer!
        harga = safe_int_convert(produk.get('harga', 0))

        # Potong saldo user
        if not kurang_saldo_user(user.id, harga, tipe="order", 
                               keterangan=f"Order {produk['kode']} ke {tujuan}"):
            msg_proc.edit_text(
                f"❌ <b>GAGAL POTONG SALDO</b>\n\n"
                f"Order berhasil di provider tapi gagal memotong saldo.\n"
                f"Silakan hubungi admin untuk refund.",
                parse_mode="HTML"
            )
            context.user_data.clear()
            return ConversationHandler.END

        # Simpan riwayat transaksi
        transaksi = {
            "ref_id": ref_id,
            "kode": produk['kode'],
            "tujuan": tujuan,
            "harga": harga,
            "tanggal": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "success",
            "sn": sn,
            "keterangan": result.get('message', 'Success'),
            "raw_response": str(result)
        }
        tambah_riwayat(user.id, transaksi)
        logger.info(f"Order sukses dicatat: {ref_id}")

        # Kirim pesan sukses
        msg_proc.edit_text(
            f"✅ <b>ORDER BERHASIL!</b>\n\n"
            f"🆔 Ref ID: <code>{ref_id}</code>\n"
            f"📦 Produk: <b>{produk['nama']}</b>\n"
            f"💰 Harga: <b>Rp {harga:,}</b>\n"
            f"📱 Tujuan: <b>{tujuan}</b>\n"
            f"🎫 SN: <code>{sn}</code>\n\n"
            f"💾 Status: <b>{result.get('message', 'Success')}</b>\n\n"
            f"Terima kasih telah berbelanja! 🛍️",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error handle_konfirmasi {ref_id if 'ref_id' in locals() else ''}: {str(e)}")
        try:
            msg_proc.edit_text(
                f"⚠️ <b>ORDER BERHASIL TAPI ADA KENDALA SYSTEM</b>\n\n"
                f"Order di provider sukses tapi ada kendala system.\n"
                f"Ref ID: <code>{ref_id if 'ref_id' in locals() else '-'}</code>\n"
                f"Silakan hubungi admin dengan Ref ID di atas.",
                parse_mode="HTML"
            )
        except Exception:
            pass
    finally:
        context.user_data.clear()
        return ConversationHandler.END

def handle_successful_order(result, msg_proc, user, produk, tujuan, ref_id, sn, context):
    """Handle successful order untuk inline button (jika dipanggil langsung)"""
    try:
        harga = safe_int_convert(produk['harga'])
        if not kurang_saldo_user(user.id, harga, tipe="order", 
                               keterangan=f"Order {produk['kode']} ke {tujuan}"):
            msg_proc.edit_text(
                f"❌ <b>GAGAL POTONG SALDO</b>\n\n"
                f"Order berhasil di provider tapi gagal memotong saldo.\n"
                f"Silakan hubungi admin untuk refund.",
                parse_mode="HTML"
            )
            context.user_data.clear()
            return ConversationHandler.END

        transaksi = {
            "ref_id": ref_id,
            "kode": produk['kode'],
            "tujuan": tujuan,
            "harga": harga,
            "tanggal": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "success",
            "sn": sn,
            "keterangan": result.get('message', 'Success'),
            "raw_response": str(result)
        }
        tambah_riwayat(user.id, transaksi)
        logger.info(f"Order sukses dicatat: {ref_id}")

        msg_proc.edit_text(
            f"✅ <b>ORDER BERHASIL!</b>\n\n"
            f"🆔 Ref ID: <code>{ref_id}</code>\n"
            f"📦 Produk: <b>{produk['nama']}</b>\n"
            f"💰 Harga: <b>Rp {harga:,}</b>\n"
            f"📱 Tujuan: <b>{tujuan}</b>\n"
            f"🎫 SN: <code>{sn}</code>\n\n"
            f"💾 Status: <b>{result.get('message', 'Success')}</b>\n\n"
            f"Terima kasih telah berbelanja! 🛍️",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error handling successful order {ref_id}: {str(e)}")
        try:
            msg_proc.edit_text(
                f"⚠️ <b>ORDER BERHASIL TAPI ADA KENDALA SYSTEM</b>\n\n"
                f"Order di provider sukses tapi ada kendala system.\n"
                f"Ref ID: <code>{ref_id}</code>\n"
                f"Silakan hubungi admin dengan Ref ID di atas.",
                parse_mode="HTML"
            )
        except Exception:
            pass
    finally:
        context.user_data.clear()
        return ConversationHandler.END
