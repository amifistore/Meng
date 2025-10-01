from telegram import ParseMode
from telegram.ext import ConversationHandler
from markup import reply_main_menu
from provider import create_trx
from saldo import kurang_saldo_user
from riwayat import tambah_riwayat
from config import ADMIN_IDS  # ✅ IMPORT ADMIN_IDS
import time
import logging

# IMPORT DARI FILE TERPUSAT
from handlers import KONFIRMASI

logger = logging.getLogger(__name__)

async def handle_konfirmasi(update, context):
    logger.info("🎯 handle_konfirmasi DIPANGGIL")
    
    if update.callback_query:
        query = update.callback_query
        user = query.from_user
        is_admin = user.id in ADMIN_IDS  # ✅ CEK ADMIN STATUS
        await query.answer()
        data = query.data
        
        logger.info(f"🔘 Callback confirmation: {data} from user {user.id}")
        
        if data == "order_batal":
            logger.info("❌ User canceled order via button")
            context.user_data.clear()
            await query.edit_message_text(
                "❌ Order dibatalkan.", 
                reply_markup=reply_main_menu(is_admin=is_admin)  # ✅ PERBAIKI PARAMETER
            )
            return ConversationHandler.END
            
        elif data == "order_konfirmasi":
            # ✅ LOGIC KONFIRMASI ORDER
            try:
                # Ambil data dari context - PERBAIKI INI!
                produk = context.user_data.get("produk")  # ✅ GUNAKAN "produk" BUKAN "selected_product"
                tujuan = context.user_data.get("tujuan")
                ref_id = context.user_data.get("ref_id", "N/A")
                
                logger.info(f"📦 Data produk: {produk}")
                logger.info(f"📱 Tujuan: {tujuan}")
                logger.info(f"🆔 Ref ID: {ref_id}")
                
                if not produk or not tujuan:
                    logger.error("❌ Data order tidak lengkap")
                    await query.edit_message_text(
                        "❌ Data order tidak lengkap. Silakan ulangi dari awal.",
                        reply_markup=reply_main_menu(is_admin=is_admin)
                    )
                    context.user_data.clear()
                    return ConversationHandler.END
                
                # ✅ AMBIL DATA PRODUK DARI OBJECT - TIDAK PERLU SPLIT!
                product_id = produk.get('kode')
                product_name = produk.get('nama')
                product_price = produk.get('harga')
                
                if not all([product_id, product_name, product_price]):
                    logger.error(f"❌ Invalid product data: {produk}")
                    await query.edit_message_text(
                        "❌ Data produk tidak valid.",
                        reply_markup=reply_main_menu(is_admin=is_admin)
                    )
                    context.user_data.clear()
                    return ConversationHandler.END
                
                logger.info(f"🔄 Memproses order: {product_name} untuk {tujuan} - Rp {product_price:,}")
                
                # Tampilkan pesan processing
                await query.edit_message_text(
                    f"⏳ <b>MEMPROSES ORDER...</b>\n\n"
                    f"📦 Produk: {product_name}\n"
                    f"📱 Tujuan: {tujuan}\n"
                    f"💰 Harga: Rp {product_price:,}\n"
                    f"🆔 Ref: {ref_id}\n\n"
                    f"Harap tunggu sebentar...",
                    parse_mode=ParseMode.HTML
                )
                
                # ✅ PROSES ORDER DI SINI
                # 1. Kurangi saldo
                saldo_result = await kurang_saldo_user(user.id, product_price)
                if not saldo_result.get('success'):
                    logger.warning(f"❌ Saldo tidak cukup: {saldo_result}")
                    await query.edit_message_text(
                        f"❌ {saldo_result.get('message', 'Saldo tidak cukup')}\n"
                        f"💳 Saldo Anda: Rp {saldo_result.get('saldo_sekarang', 0):,}",
                        reply_markup=reply_main_menu(is_admin=is_admin)
                    )
                    context.user_data.clear()
                    return ConversationHandler.END
                
                logger.info("✅ Saldo berhasil dikurangi")
                
                # 2. Create transaction di provider
                trx_result = await create_trx(product_id, tujuan)
                if not trx_result.get('success'):
                    # Kembalikan saldo jika gagal
                    logger.error(f"❌ Provider error: {trx_result}")
                    from saldo import tambah_saldo_user
                    await tambah_saldo_user(user.id, product_price)
                    
                    await query.edit_message_text(
                        f"❌ Gagal memproses di provider:\n{trx_result.get('message', 'Unknown error')}",
                        reply_markup=reply_main_menu(is_admin=is_admin)
                    )
                    context.user_data.clear()
                    return ConversationHandler.END
                
                logger.info(f"✅ Transaction created: {trx_result.get('trx_id')}")
                
                # 3. Simpan riwayat
                riwayat_data = {
                    'user_id': user.id,
                    'product_name': product_name,
                    'target': tujuan,
                    'price': product_price,
                    'trx_id': trx_result.get('trx_id', ''),
                    'ref_id': ref_id,
                    'status': 'pending'
                }
                riwayat_result = await tambah_riwayat(riwayat_data)
                
                if not riwayat_result.get('success'):
                    logger.error(f"❌ Gagal simpan riwayat: {riwayat_result}")
                    # Tetap lanjut, karena order sudah sukses di provider
                
                # 4. Tampilkan hasil sukses
                success_text = (
                    f"✅ <b>ORDER BERHASIL</b>\n\n"
                    f"📦 Produk: {product_name}\n"
                    f"📱 Tujuan: {tujuan}\n"
                    f"💰 Harga: Rp {product_price:,}\n"
                    f"🆔 Ref ID: {ref_id}\n"
                    f"📋 Trx ID: {trx_result.get('trx_id', 'N/A')}\n"
                    f"💳 Sisa Saldo: Rp {saldo_result.get('saldo_sekarang', 0):,}\n\n"
                    f"⏳ Status: Sedang diproses...\n\n"
                    f"Gunakan menu <b>🔍 Cek Status</b> untuk memantau order Anda."
                )
                
                await query.edit_message_text(
                    success_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_main_menu(is_admin=is_admin)
                )
                
                logger.info(f"✅ Order berhasil: User {user.id} - {product_name} - {tujuan} - Trx: {trx_result.get('trx_id')}")
                
            except Exception as e:
                logger.error(f"💥 Error dalam proses order: {e}", exc_info=True)
                await query.edit_message_text(
                    "❌ Terjadi kesalahan sistem saat memproses order. Silakan coba lagi.",
                    reply_markup=reply_main_menu(is_admin=is_admin)
                )
            
            # Clear user data setelah order selesai
            context.user_data.clear()
            return ConversationHandler.END
            
    else:
        # Handle text confirmation (jika ada)
        user = update.message.from_user
        is_admin = user.id in ADMIN_IDS
        text = update.message.text.strip().lower()
        
        logger.info(f"📝 Text confirmation: {text} from user {user.id}")
        
        if text in ['batal', 'cancel', '/cancel']:
            logger.info("❌ User canceled order via text")
            context.user_data.clear()
            await update.message.reply_text(
                "❌ Order dibatalkan.", 
                reply_markup=reply_main_menu(is_admin=is_admin)
            )
            return ConversationHandler.END
            
        elif text in ['ya', 'y', 'ok', 'konfirmasi']:
            # Logic untuk konfirmasi via text
            await update.message.reply_text(
                "⚠️ Silakan gunakan button konfirmasi di atas untuk melanjutkan order.",
                reply_markup=reply_main_menu(is_admin=is_admin)
            )
        else:
            await update.message.reply_text(
                "❌ Perintah tidak dikenali. Gunakan button '✅ Konfirmasi' atau '❌ Batal' di atas.",
                reply_markup=reply_main_menu(is_admin=is_admin)
            )
        
    return KONFIRMASI
