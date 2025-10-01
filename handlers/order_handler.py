from telegram import ParseMode
from telegram.ext import ConversationHandler
from markup import reply_main_menu
from provider import create_trx
from saldo import kurang_saldo_user
from riwayat import tambah_riwayat
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
        await query.answer()  # ✅ PERBAIKI: tambah await
        data = query.data
        
        logger.info(f"🔘 Callback confirmation: {data}")
        
        if data == "order_batal":
            logger.info("❌ User canceled order via button")
            context.user_data.clear()
            await query.edit_message_text("❌ Order dibatalkan.", reply_markup=reply_main_menu(user.id))
            return ConversationHandler.END
            
        elif data == "order_konfirmasi":
            # ✅ LOGIC KONFIRMASI ORDER
            try:
                # Ambil data dari context
                product_data = context.user_data.get('selected_product')
                tujuan = context.user_data.get('tujuan')
                
                if not product_data or not tujuan:
                    await query.edit_message_text("❌ Data order tidak lengkap. Silakan ulangi dari awal.")
                    context.user_data.clear()
                    return ConversationHandler.END
                
                # Parse product data
                product_parts = product_data.split('|')
                if len(product_parts) < 3:
                    await query.edit_message_text("❌ Format produk tidak valid.")
                    context.user_data.clear()
                    return ConversationHandler.END
                
                product_id = product_parts[0]
                product_name = product_parts[1]
                product_price = int(product_parts[2])
                
                logger.info(f"🔄 Memproses order: {product_name} untuk {tujuan}")
                
                # Tampilkan pesan processing
                await query.edit_message_text(
                    f"⏳ Memproses order Anda...\n"
                    f"📦 Produk: {product_name}\n"
                    f"📱 Tujuan: {tujuan}\n"
                    f"💸 Harga: Rp {product_price:,}\n\n"
                    f"Harap tunggu..."
                )
                
                # ✅ PROSES ORDER DI SINI
                # 1. Kurangi saldo
                saldo_result = await kurang_saldo_user(user.id, product_price)
                if not saldo_result.get('success'):
                    await query.edit_message_text(
                        f"❌ Gagal: {saldo_result.get('message', 'Saldo tidak cukup')}\n"
                        f"💳 Saldo Anda: Rp {saldo_result.get('saldo_sekarang', 0):,}",
                        reply_markup=reply_main_menu(user.id)
                    )
                    context.user_data.clear()
                    return ConversationHandler.END
                
                # 2. Create transaction di provider
                trx_result = await create_trx(product_id, tujuan)
                if not trx_result.get('success'):
                    # Kembalikan saldo jika gagal
                    from saldo import tambah_saldo_user
                    await tambah_saldo_user(user.id, product_price)
                    
                    await query.edit_message_text(
                        f"❌ Gagal memproses di provider: {trx_result.get('message', 'Unknown error')}",
                        reply_markup=reply_main_menu(user.id)
                    )
                    context.user_data.clear()
                    return ConversationHandler.END
                
                # 3. Simpan riwayat
                riwayat_data = {
                    'user_id': user.id,
                    'product_name': product_name,
                    'target': tujuan,
                    'price': product_price,
                    'trx_id': trx_result.get('trx_id', ''),
                    'status': 'pending'
                }
                await tambah_riwayat(riwayat_data)
                
                # 4. Tampilkan hasil sukses
                success_text = (
                    f"✅ **ORDER BERHASIL**\n\n"
                    f"📦 Produk: {product_name}\n"
                    f"📱 Tujuan: {tujuan}\n"
                    f"💸 Harga: Rp {product_price:,}\n"
                    f"🆔 Trx ID: {trx_result.get('trx_id', 'N/A')}\n"
                    f"💳 Sisa Saldo: Rp {saldo_result.get('saldo_sekarang', 0):,}\n\n"
                    f"⏳ Status: Sedang diproses...\n\n"
                    f"Gunakan menu '🔍 Cek Status' untuk memantau order Anda."
                )
                
                await query.edit_message_text(
                    success_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_main_menu(user.id)
                )
                
                logger.info(f"✅ Order berhasil: User {user.id} - {product_name} - {tujuan}")
                
            except Exception as e:
                logger.error(f"💥 Error dalam proses order: {e}")
                await query.edit_message_text(
                    "❌ Terjadi kesalahan sistem saat memproses order. Silakan coba lagi.",
                    reply_markup=reply_main_menu(user.id)
                )
            
            # Clear user data setelah order selesai
            context.user_data.clear()
            return ConversationHandler.END
            
    else:
        # Handle text confirmation (jika ada)
        user = update.message.from_user
        text = update.message.text.strip().lower()
        
        logger.info(f"📝 Text confirmation: {text}")
        
        if text in ['batal', 'cancel', '/cancel']:
            logger.info("❌ User canceled order via text")
            context.user_data.clear()
            await update.message.reply_text("❌ Order dibatalkan.", reply_markup=reply_main_menu(user.id))
            return ConversationHandler.END
            
        elif text in ['ya', 'y', 'ok', 'konfirmasi']:
            # Logic untuk konfirmasi via text
            await update.message.reply_text(
                "⚠️ Silakan gunakan button konfirmasi di atas untuk melanjutkan order.",
                reply_markup=reply_main_menu(user.id)
            )
        else:
            await update.message.reply_text(
                "❌ Perintah tidak dikenali. Gunakan button '✅ Konfirmasi' atau '❌ Batal' di atas.",
                reply_markup=reply_main_menu(user.id)
            )
        
    return KONFIRMASI
