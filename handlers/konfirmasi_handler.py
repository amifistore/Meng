from telegram import Update, ParseMode
from telegram.ext import CallbackContext, ConversationHandler
from typing import Dict, Any, Optional
import logging

from markup import get_menu
from provider import create_trx
from utils import get_user_saldo, set_user_saldo, load_riwayat, save_riwayat

# Constants
KONFIRMASI = 2
logger = logging.getLogger(__name__)

class TransactionConfirmationHandler:
    """Handler untuk proses konfirmasi transaksi"""

    def __init__(self):
        self.expected_responses = {"YA", "BATAL"}

    def handle_konfirmasi(self, update: Update, context: CallbackContext) -> int:
        """Menangani input konfirmasi dari user"""
        # Bisa dari message atau callback (untuk inline button)
        user_input = None
        if update.message:
            user_input = update.message.text.strip().upper()
        elif update.callback_query:
            user_input = update.callback_query.data.strip().upper()
            update = update.callback_query  # Agar reply tetap ke callback

        user_id = update.effective_user.id

        # Validasi input
        if user_input not in self.expected_responses:
            update.message.reply_text(
                "❌ Ketik 'YA' untuk konfirmasi atau 'BATAL' untuk batal.",
                reply_markup=get_menu(user_id)
            )
            return KONFIRMASI

        # Jika batal
        if user_input == "BATAL":
            update.message.reply_text(
                "❌ Transaksi dibatalkan.",
                reply_markup=get_menu(user_id)
            )
            context.user_data.clear()
            return ConversationHandler.END

        # Proses transaksi
        produk = context.user_data.get("produk")
        tujuan = context.user_data.get("tujuan")
        if not produk or not tujuan:
            update.message.reply_text(
                "❌ Data transaksi tidak lengkap.",
                reply_markup=get_menu(user_id)
            )
            context.user_data.clear()
            return ConversationHandler.END

        harga = produk.get("harga")
        saldo = get_user_saldo(user_id)

        if saldo < harga:
            update.message.reply_text(
                f"❌ Saldo kamu tidak cukup untuk transaksi ini.\n"
                f"Saldo: Rp {saldo:,}\nHarga: Rp {harga:,}\n"
                "Silakan top up dahulu.",
                reply_markup=get_menu(user_id)
            )
            context.user_data.clear()
            return ConversationHandler.END

        # Eksekusi via provider API
        try:
            api_response = create_trx(produk["kode"], tujuan)
            if not api_response or not api_response.get("refid"):
                error_msg = api_response.get("message", "Gagal membuat transaksi.") if api_response else "Tidak ada respon API."
                update.message.reply_text(
                    f"❌ Gagal membuat transaksi:\n<b>{error_msg}</b>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_menu(user_id)
                )
                context.user_data.clear()
                return ConversationHandler.END

            # Simpan riwayat transaksi
            riwayat = load_riwayat()
            refid = api_response["refid"]
            riwayat[refid] = {
                "trxid": api_response.get("trxid", ""),
                "refid": refid,
                "produk": produk["kode"],
                "tujuan": tujuan,
                "status_text": api_response.get("status", "pending"),
                "status_code": None,
                "keterangan": api_response.get("message", ""),
                "waktu": api_response.get("waktu", ""),
                "harga": harga,
                "user_id": user_id,
                "username": update.effective_user.username or "",
                "nama": update.effective_user.full_name if hasattr(update.effective_user, "full_name") else "",
            }
            save_riwayat(riwayat)

            # Update saldo user
            set_user_saldo(user_id, saldo - harga)

            # Pesan sukses
            current_balance = get_user_saldo(user_id)
            success_message = (
                f"✅ Transaksi berhasil!\n\n"
                f"📦 Produk: {produk['kode']}\n"
                f"📱 Tujuan: {tujuan}\n"
                f"🔢 RefID: <code>{api_response['refid']}</code>\n"
                f"📊 Status: {api_response.get('status', 'pending')}\n"
                f"💰 Saldo kamu: Rp {current_balance:,}"
            )
            update.message.reply_text(
                success_message,
                parse_mode=ParseMode.HTML,
                reply_markup=get_menu(user_id)
            )

        except Exception as e:
            logger.error(f"Error transaksi: {str(e)}")
            update.message.reply_text(
                f"❌ Error saat transaksi: {str(e)}",
                parse_mode=ParseMode.HTML,
                reply_markup=get_menu(user_id)
            )
        finally:
            context.user_data.clear()

        return ConversationHandler.END

# Instance handler untuk import di main.py
transaction_confirmation_handler = TransactionConfirmationHandler()
handle_konfirmasi = transaction_confirmation_handler.handle_konfirmasi
