from telegram import ParseMode
from telegram.ext import ConversationHandler
from markup import reply_main_menu
from produk import get_produk_list
from saldo import get_saldo_user
from config import ADMIN_IDS
import logging

# IMPORT DARI FILE TERPUSAT
from handlers import CHOOSING_PRODUK, INPUT_TUJUAN

logger = logging.getLogger(__name__)

def produk_pilih_callback(update, context):
    query = update.callback_query
    user = query.from_user
    data = query.data
    
    # ANSWER CALLBACK QUERY FIRST - INI PENTING!
    query.answer()

    logger.info(f"🎯 produk_pilih_callback DIPANGGIL - User: {user.first_name}, Data: {data}")

    if data.startswith("produk_static|"):
        try:
            idx = int(data.split("|")[1])
            produk_list = get_produk_list()
            
            logger.info(f"📦 Processing product {idx} from {len(produk_list)} products")

            # Validasi index
            if idx < 0 or idx >= len(produk_list):
                logger.error(f"❌ Invalid product index: {idx}")
                query.edit_message_text(
                    "❌ Produk tidak valid atau tidak ditemukan.", 
                    reply_markup=reply_main_menu(user.id in ADMIN_IDS)
                )
                return ConversationHandler.END

            p = produk_list[idx]
            logger.info(f"✅ Product selected: {p['kode']} - {p['nama']} - Rp {p['harga']} - Kuota: {p.get('kuota', 0)}")
            
            # Validasi struktur produk
            if not all(key in p for key in ['kode', 'nama', 'harga']):
                logger.error(f"❌ Invalid product structure: {p}")
                query.edit_message_text(
                    "❌ Data produk tidak valid.", 
                    reply_markup=reply_main_menu(user.id in ADMIN_IDS)
                )
                return ConversationHandler.END
            
            context.user_data["produk"] = p

            # Cek saldo user
            saldo = get_saldo_user(user.id)
            logger.info(f"💰 User saldo: {saldo}, Product price: {p['harga']}")
            
            if saldo < p['harga']:
                logger.warning(f"❌ Insufficient balance: {saldo} < {p['harga']}")
                query.edit_message_text(
                    f"❌ Saldo tidak cukup!\n\n"
                    f"📦 Produk: <b>{p['nama']}</b>\n"
                    f"💰 Harga: Rp {p['harga']:,}\n"
                    f"💵 Saldo kamu: Rp {saldo:,}\n\n"
                    "Silakan top up terlebih dahulu.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_main_menu(user.id in ADMIN_IDS)
                )
                return ConversationHandler.END

            # SUCCESS - lanjut ke input tujuan
            logger.info("🎯 Moving to INPUT_TUJUAN state")
            query.edit_message_text(
                f"✅ <b>PRODUK DIPILIH</b>\n\n"
                f"📦 Produk: <b>{p['kode']} - {p['nama']}</b>\n"
                f"💰 Harga: Rp {p['harga']:,}\n"
                f"📊 Stok: <b>{p.get('kuota', 0)}</b>\n\n"
                "📱 <b>Silakan input nomor tujuan:</b>\n"
                "Contoh: <code>081234567890</code>\n\n"
                "Ketik /batal untuk membatalkan.",
                parse_mode=ParseMode.HTML
            )
            return INPUT_TUJUAN

        except Exception as e:
            logger.error(f"💥 Exception in produk_pilih_callback: {e}", exc_info=True)
            query.edit_message_text(
                "❌ Terjadi kesalahan saat memilih produk.",
                reply_markup=reply_main_menu(user.id in ADMIN_IDS)
            )
            return ConversationHandler.END

    elif data == "back_main":
        logger.info("⬅️ User kembali ke main menu")
        query.edit_message_text(
            "Kembali ke menu utama.", 
            reply_markup=reply_main_menu(user.id in ADMIN_IDS)
        )
        return ConversationHandler.END

    else:
        logger.warning(f"❓ Unknown callback data: {data}")
        query.edit_message_text(
            "❌ Pilihan tidak valid.", 
            reply_markup=reply_main_menu(user.id in ADMIN_IDS)
        )
        return ConversationHandler.END
