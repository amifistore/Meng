from telegram import ParseMode
from telegram.ext import ConversationHandler
from markup import reply_main_menu
from provider import create_trx
from saldo import kurang_saldo_user
from riwayat import tambah_riwayat
import time
import logging
import uuid

logger = logging.getLogger(__name__)

async def handle_konfirmasi(update, context):
    logger.info("🎯 handle_konfirmasi DIPANGGIL")
    
    if update.callback_query:
        query = update.callback_query
        user = query.from_user
        await query.answer()
        data = query.data
        
        logger.info(f"🔘 Callback confirmation: {data}")
        
        if data == "order_batal":
            logger.info("❌ User canceled order via button")
            context.user_data.clear()
            await query.edit_message_text("❌ Order dibatalkan.", reply_markup=reply_main_menu(user.id))
            return ConversationHandler.END
            
        elif data == "order_konfirmasi":
            try:
                # Ambil data dari context
                produk = context.user_data.get("produk")
                tujuan = context.user_data.get("tujuan")
                
                if not produk or not tujuan:
                    await query.edit_message_text("❌ Data order tidak lengkap. Silakan ulangi dari awal.")
                    context.user_data.clear()
                    return ConversationHandler.END
                
                product_id = produk.get('kode')
                product_name = produk.get('nama')
                product_price = produk.get('harga')
                
                # Generate unique ref_id
                ref_id = str(uuid.uuid4())
                
                logger.info(f"🔄 Memproses order: {product_name} untuk {tujuan} - Ref: {ref_id}")
                
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
                
                # 1. Kurangi saldo user
                saldo_result = await kurang_saldo_user(user.id, product_price)
                if not saldo_result.get('success'):
                    logger.warning(f"❌ Saldo tidak cukup: {saldo_result}")
                    await query.edit_message_text(
                        f"❌ {saldo_result.get('message', 'Saldo tidak cukup')}\n"
                        f"💳 Saldo Anda: Rp {saldo_result.get('saldo_sekarang', 0):,}",
                        reply_markup=reply_main_menu(user.id)
                    )
                    context.user_data.clear()
                    return ConversationHandler.END
                
                logger.info("✅ Saldo berhasil dikurangi")
                
                # 2. Create transaction di provider
                trx_result = await create_trx(product_id, tujuan, ref_id)
                
                if not trx_result.get('success'):
                    # Kembalikan saldo jika gagal
                    logger.error(f"❌ Provider error: {trx_result}")
                    from saldo import tambah_saldo_user
                    await tambah_saldo_user(user.id, product_price, "refund", f"Refund gagal order: {trx_result.get('message')}")
                    
                    await query.edit_message_text(
                        f"❌ Gagal memproses di provider:\n{trx_result.get('message', 'Unknown error')}\n\n"
                        f"Saldo telah dikembalikan.",
                        reply_markup=reply_main_menu(user.id)
                    )
                    context.user_data.clear()
                    return ConversationHandler.END
                
                trx_id = trx_result.get('trx_id', '')
                logger.info(f"✅ Transaction created: {trx_id}")
                
                # 3. Simpan riwayat
                riwayat_data = {
                    'user_id': user.id,
                    'product_name': product_name,
                    'target': tujuan,
                    'price': product_price,
                    'trx_id': trx_id,
                    'ref_id': ref_id,
                    'status': 'pending'  # Akan diupdate via webhook
                }
                riwayat_result = await tambah_riwayat(riwayat_data)
                
                # 4. Tampilkan hasil sukses
                success_text = (
                    f"✅ <b>ORDER BERHASIL DIPROSES</b>\n\n"
                    f"📦 Produk: {product_name}\n"
                    f"📱 Tujuan: {tujuan}\n"
                    f"💰 Harga: Rp {product_price:,}\n"
                    f"🆔 Ref ID: {ref_id}\n"
                    f"📋 Trx ID: {trx_id}\n"
                    f"💳 Sisa Saldo: Rp {saldo_result.get('saldo_sekarang', 0):,}\n\n"
                    f"⏳ Status: Sedang diproses provider...\n\n"
                    f"Gunakan menu <b>🔍 Cek Status</b> untuk memantau order Anda.\n"
                    f"Status akan otomatis diupdate via webhook."
                )
                
                await query.edit_message_text(
                    success_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_main_menu(user.id)
                )
                
                logger.info(f"✅ Order berhasil: User {user.id} - {product_name} - {tujuan} - Ref: {ref_id} - Trx: {trx_id}")
                
            except Exception as e:
                logger.error(f"💥 Error dalam proses order: {e}", exc_info=True)
                await query.edit_message_text(
                    "❌ Terjadi kesalahan sistem saat memproses order. Silakan coba lagi.",
                    reply_markup=reply_main_menu(user.id)
                )
            
            # Clear user data setelah order selesai
            context.user_data.clear()
            return ConversationHandler.END
            
    else:
        # Handle text confirmation
        user = update.message.from_user
        text = update.message.text.strip().lower()
        
        logger.info(f"📝 Text confirmation: {text}")
        
        if text in ['batal', 'cancel', '/cancel']:
            logger.info("❌ User canceled order via text")
            context.user_data.clear()
            await update.message.reply_text("❌ Order dibatalkan.", reply_markup=reply_main_menu(user.id))
            return ConversationHandler.END
            
        elif text in ['ya', 'y', 'ok', 'konfirmasi']:
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
