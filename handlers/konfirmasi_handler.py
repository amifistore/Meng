from telegram import Update, ParseMode
from telegram.ext import CallbackContext, ConversationHandler
from typing import Dict, Any, Optional
import logging

from markup import get_menu
from provider import create_trx
from utils import get_saldo, set_saldo, load_riwayat, save_riwayat

# Constants
KONFIRMASI = 2
logger = logging.getLogger(__name__)

class TransactionConfirmationHandler:
    """Handler untuk proses konfirmasi transaksi"""
    
    def __init__(self):
        self.expected_responses = {"YA", "BATAL"}
    
    def handle_confirmation(self, update: Update, context: CallbackContext) -> int:
        """Menangani input konfirmasi dari user"""
        user_input = update.message.text.strip().upper()
        user_id = update.effective_user.id
        
        # Validasi input
        if not self._validate_input(user_input, update):
            return KONFIRMASI
        
        # Handle batal
        if user_input == "BATAL":
            return self._cancel_transaction(update, user_id)
        
        # Handle konfirmasi
        return self._process_transaction(update, context, user_id)
    
    def _validate_input(self, user_input: str, update: Update) -> bool:
        """Validasi input user"""
        if user_input not in self.expected_responses:
            update.message.reply_text(
                "❌ Ketik 'YA' untuk konfirmasi atau 'BATAL' untuk batal."
            )
            return False
        return True
    
    def _cancel_transaction(self, update: Update, user_id: int) -> int:
        """Membatalkan transaksi"""
        update.message.reply_text(
            "❌ Transaksi dibatalkan.", 
            reply_markup=get_menu(user_id)
        )
        return ConversationHandler.END
    
    def _process_transaction(self, update: Update, context: CallbackContext, user_id: int) -> int:
        """Memproses transaksi yang dikonfirmasi"""
        # Validasi data transaksi
        transaction_data = self._validate_transaction_data(context, update, user_id)
        if not transaction_data:
            return ConversationHandler.END
        
        produk, tujuan, harga = transaction_data
        
        # Validasi saldo
        if not self._validate_balance(harga, update, user_id):
            return ConversationHandler.END
        
        # Eksekusi transaksi
        return self._execute_transaction(update, context, user_id, produk, tujuan, harga)
    
    def _validate_transaction_data(self, context: CallbackContext, update: Update, user_id: int) -> Optional[tuple]:
        """Validasi kelengkapan data transaksi"""
        produk = context.user_data.get("produk")
        tujuan = context.user_data.get("tujuan")
        
        if not produk or not tujuan:
            update.message.reply_text(
                "❌ Data transaksi tidak lengkap.", 
                reply_markup=get_menu(user_id)
            )
            return None
        
        return (produk, tujuan, produk["harga"])
    
    def _validate_balance(self, harga: int, update: Update, user_id: int) -> bool:
        """Validasi kecukupan saldo"""
        saldo = get_saldo()
        
        if saldo < harga:
            update.message.reply_text(
                "❌ Saldo bot tidak cukup.", 
                reply_markup=get_menu(user_id)
            )
            return False
        return True
    
    def _execute_transaction(self, update: Update, context: CallbackContext, user_id: int, 
                           produk: Dict[str, Any], tujuan: str, harga: int) -> int:
        """Mengeksekusi transaksi melalui API"""
        try:
            # Create transaction via API
            api_response = create_trx(produk["kode"], tujuan)
            
            if not self._is_transaction_successful(api_response):
                self._handle_api_error(api_response, update, user_id)
                return ConversationHandler.END
            
            # Save transaction record
            self._save_transaction_record(api_response, produk, tujuan, harga, update.effective_user)
            
            # Update balance
            self._update_balance(harga)
            
            # Send success message
            self._send_success_message(update, api_response, produk, tujuan, harga, user_id)
            
        except Exception as e:
            logger.error(f"Transaction error: {str(e)}")
            self._handle_transaction_error(update, e, user_id)
        finally:
            context.user_data.clear()
        
        return ConversationHandler.END
    
    def _is_transaction_successful(self, api_response: Optional[Dict]) -> bool:
        """Cek apakah transaksi API berhasil"""
        return api_response and api_response.get("refid")
    
    def _handle_api_error(self, api_response: Optional[Dict], update: Update, user_id: int):
        """Handle error response dari API"""
        error_msg = api_response.get("message", "Gagal membuat transaksi.") if api_response else "Tidak ada respon API."
        
        update.message.reply_text(
            f"❌ Gagal membuat transaksi:\n<b>{error_msg}</b>", 
            parse_mode=ParseMode.HTML, 
            reply_markup=get_menu(user_id)
        )
    
    def _save_transaction_record(self, api_response: Dict, produk: Dict, tujuan: str, 
                               harga: int, user: Any):
        """Menyimpan record transaksi ke riwayat"""
        riwayat = load_riwayat()
        refid = api_response["refid"]
        
        riwayat[refid] = {
            "trxid": api_response.get("trxid", ""),
            "reffid": refid,
            "produk": produk["kode"],
            "tujuan": tujuan,
            "status_text": api_response.get("status", "pending"),
            "status_code": None,
            "keterangan": api_response.get("message", ""),
            "waktu": api_response.get("waktu", ""),
            "harga": harga,
            "user_id": user.id,
            "username": user.username or "",
            "nama": user.full_name,
        }
        
        save_riwayat(riwayat)
    
    def _update_balance(self, harga: int):
        """Update saldo bot"""
        current_balance = get_saldo()
        set_saldo(current_balance - harga)
    
    def _send_success_message(self, update: Update, api_response: Dict, produk: Dict, 
                            tujuan: str, harga: int, user_id: int):
        """Kirim pesan sukses transaksi"""
        current_balance = get_saldo() - harga  # Already updated, but we calculate for message
        
        success_message = (
            f"✅ Transaksi berhasil!\n\n"
            f"📦 Produk: {produk['kode']}\n"
            f"📱 Tujuan: {tujuan}\n"
            f"🔢 RefID: <code>{api_response['refid']}</code>\n"
            f"📊 Status: {api_response.get('status', 'pending')}\n"
            f"💰 Saldo bot: Rp {current_balance:,}"
        )
        
        update.message.reply_text(
            success_message,
            parse_mode=ParseMode.HTML,
            reply_markup=get_menu(user_id)
        )
    
    def _handle_transaction_error(self, update: Update, error: Exception, user_id: int):
        """Handle error selama proses transaksi"""
        update.message.reply_text(
            f"❌ Error membuat transaksi: {str(error)}",
            parse_mode=ParseMode.HTML,
            reply_markup=get_menu(user_id)
        )

# Instance untuk digunakan di main bot
confirmation_handler = TransactionConfirmationHandler()

# Fungsi kompatibilitas untuk existing code
def konfirmasi_step(update: Update, context: CallbackContext) -> int:
    """Wrapper function untuk compatibility dengan existing code"""
    return confirmation_handler.handle_confirmation(update, context)
