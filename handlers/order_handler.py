import logging
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ConversationHandler, CallbackContext

from markup import reply_main_menu, konfirmasi_order_keyboard, produk_inline_keyboard
from saldo import get_saldo_user, kurang_saldo_user, tambah_saldo_user
from produk import get_produk_list
from provider import create_trx
from riwayat import tambah_riwayat
from config import ADMIN_IDS

# States untuk Conversation Handler
CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI = range(3)

logger = logging.getLogger(__name__)

class OrderHandlers:
    """Handler terpusat untuk semua proses order"""
    
    @staticmethod
    async def handle_all_callbacks(update: Update, context: CallbackContext):
        """Handle semua callback query dari button produk"""
        try:
            # Pastikan update dan callback_query ada
            if not update or not update.callback_query:
                logger.error("❌ Update or callback_query is None")
                return
            
            query = update.callback_query
            user = query.from_user
            callback_data = query.data
            
            logger.info(f"📲 CALLBACK RECEIVED from {user.id}: {callback_data}")
            
            # Jawab callback dulu
            await query.answer()
            
            # Handle berbagai jenis callback
            if callback_data.startswith('produk_'):
                # Handle pemilihan produk dari topup_handler
                product_id = callback_data.replace('produk_', '')
                logger.info(f"🎯 Product selected from topup: {product_id} by user {user.id}")
                
                # Simpan data produk ke context
                context.user_data['selected_product'] = product_id
                
                await query.edit_message_text(
                    f"✅ Produk dipilih: {product_id}\n\n"
                    f"Silakan ketik nomor tujuan:\n"
                    f"Contoh: 081234567890\n\n"
                    f"Ketik /cancel untuk membatalkan"
                )
                
            elif callback_data.startswith('produk_static|'):
                # Handle pemilihan produk dari conversation handler
                await OrderHandlers.produk_pilih_callback(update, context)
                
            elif callback_data == 'back_main':
                # Handle kembali ke menu utama
                from handlers.main_menu_handler import start
                return await start(update, context)
                
            elif callback_data in ['order_konfirmasi', 'order_batal']:
                # Handle konfirmasi order
                return await OrderHandlers.handle_konfirmasi(update, context)
                
            elif callback_data.startswith('topup_'):
                # Handle topup callbacks - forward ke topup_handler
                from handlers.topup_handler import admin_topup_callback
                return await admin_topup_callback(update, context)
                
            elif callback_data.startswith('admin_'):
                # Handle admin callbacks
                if callback_data.startswith('admin_edit_produk|'):
                    from handlers.admin_edit_handler import admin_edit_produk_callback
                    return await admin_edit_produk_callback(update, context)
                elif callback_data.startswith('edit_'):
                    from handlers.admin_edit_handler import admin_edit_harga_prompt, admin_edit_deskripsi_prompt
                    if 'harga' in callback_data:
                        return await admin_edit_harga_prompt(update, context)
                    elif 'deskripsi' in callback_data:
                        return await admin_edit_deskripsi_prompt(update, context)
                
            elif callback_data == 'riwayat_topup_admin' or callback_data.startswith('admin_topup_detail'):
                # Handle admin topup list
                from handlers.topup_handler import admin_topup_list_callback, admin_topup_detail_callback
                if callback_data == 'riwayat_topup_admin':
                    return await admin_topup_list_callback(update, context)
                else:
                    return await admin_topup_detail_callback(update, context)
                    
            elif callback_data == 'semua_riwayat':
                # Handle semua riwayat admin
                from handlers.riwayat_handler import semua_riwayat_callback
                return await semua_riwayat_callback(update, context)
                
            else:
                logger.warning(f"🤖 Unknown callback: {callback_data}")
                await query.edit_message_text("❌ Perintah tidak dikenali")
                
        except Exception as e:
            logger.error(f"💥 Error in callback handler: {e}")
            if update and update.callback_query:
                await update.callback_query.answer("Error processing request", show_alert=True)

    @staticmethod
    async def lihat_produk_callback(update: Update, context: CallbackContext):
        """Handler untuk menampilkan daftar produk"""
        try:
            user = update.message.from_user
            logger.info(f"User {user.first_name} (ID: {user.id}) memilih Order Produk")
            
            # Clear previous data
            context.user_data.clear()
            
            # Get product list
            produk_list = get_produk_list()
            logger.info(f"Retrieved {len(produk_list)} products")
            
            if not produk_list:
                await update.message.reply_text(
                    "❌ Maaf, saat ini tidak ada produk yang tersedia.\n"
                    "Silakan coba lagi beberapa saat atau hubungi admin."
                )
                return
            
            # Debug: Check if products have proper structure
            for i, produk in enumerate(produk_list[:2]):
                logger.info(f"Sample product {i}: {produk.get('kode')} - {produk.get('nama')} - Kuota: {produk.get('kuota', 'N/A')}")
            
            await update.message.reply_text(
                "🛒 <b>PILIH PRODUK</b>\n\n"
                "Silakan pilih produk yang ingin dibeli:\n"
                "ℹ️ Stok ditampilkan dalam tanda kurung",
                parse_mode='HTML',
                reply_markup=produk_inline_keyboard(produk_list)
            )
            logger.info("Successfully sent product list to user")
            
        except Exception as e:
            logger.error(f"Error in lihat_produk_callback: {e}")
            await update.message.reply_text(
                "❌ Terjadi kesalahan saat menampilkan produk.\n"
                "Silakan coba lagi atau hubungi admin."
            )

    @staticmethod
    async def produk_pilih_callback(update: Update, context: CallbackContext):
        """Handler untuk memilih produk dari inline keyboard"""
        query = update.callback_query
        user = query.from_user
        data = query.data
        
        # ANSWER CALLBACK QUERY FIRST - INI PENTING!
        await query.answer()

        logger.info(f"🎯 produk_pilih_callback DIPANGGIL - User: {user.first_name}, Data: {data}")

        if data.startswith("produk_static|"):
            try:
                idx = int(data.split("|")[1])
                produk_list = get_produk_list()
                
                logger.info(f"📦 Processing product {idx} from {len(produk_list)} products")

                # Validasi index
                if idx < 0 or idx >= len(produk_list):
                    logger.error(f"❌ Invalid product index: {idx}")
                    await query.edit_message_text(
                        "❌ Produk tidak valid atau tidak ditemukan.", 
                        reply_markup=reply_main_menu(user.id in ADMIN_IDS)
                    )
                    return ConversationHandler.END

                p = produk_list[idx]
                logger.info(f"✅ Product selected: {p['kode']} - {p['nama']} - Rp {p['harga']} - Kuota: {p.get('kuota', 0)}")
                
                # Validasi struktur produk
                if not all(key in p for key in ['kode', 'nama', 'harga']):
                    logger.error(f"❌ Invalid product structure: {p}")
                    await query.edit_message_text(
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
                    await query.edit_message_text(
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
                await query.edit_message_text(
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
                await query.edit_message_text(
                    "❌ Terjadi kesalahan saat memilih produk.",
                    reply_markup=reply_main_menu(user.id in ADMIN_IDS)
                )
                return ConversationHandler.END

        elif data == "back_main":
            logger.info("⬅️ User kembali ke main menu")
            await query.edit_message_text(
                "Kembali ke menu utama.", 
                reply_markup=reply_main_menu(user.id in ADMIN_IDS)
            )
            return ConversationHandler.END

        else:
            logger.warning(f"❓ Unknown callback data: {data}")
            await query.edit_message_text(
                "❌ Pilihan tidak valid.", 
                reply_markup=reply_main_menu(user.id in ADMIN_IDS)
            )
            return ConversationHandler.END

    @staticmethod
    async def handle_input_tujuan(update: Update, context: CallbackContext):
        """Handler untuk input nomor tujuan"""
        user = update.message.from_user
        text = update.message.text.strip()
        is_admin = user.id in ADMIN_IDS

        logger.info(f"🎯 handle_input_tujuan DIPANGGIL - User: {user.first_name}, Text: {text}")

        if text == '/batal':
            logger.info("❌ User membatalkan order")
            context.user_data.clear()
            await update.message.reply_text("❌ Order dibatalkan.", reply_markup=reply_main_menu(is_admin=is_admin))
            return ConversationHandler.END
            
        if not text.isdigit() or len(text) < 10 or len(text) > 15:
            logger.warning(f"❌ Invalid phone number format: {text}")
            await update.message.reply_text(
                "❌ Format nomor tidak valid! Harus angka minimal 10 digit dan maksimal 15 digit.\n"
                "Contoh: 081234567890\n\n"
                "Silakan input ulang atau ketik /batal untuk membatalkan."
            )
            return INPUT_TUJUAN
            
        produk = context.user_data.get("produk")
        if not produk:
            logger.error("❌ No product found in user_data - session expired")
            await update.message.reply_text("❌ Sesi expired. Silakan mulai order lagi.", reply_markup=reply_main_menu(is_admin=is_admin))
            return ConversationHandler.END

        # Cek saldo user
        saldo = get_saldo_user(user.id)
        logger.info(f"💰 Final saldo check: {saldo} >= {produk['harga']}")
        
        if saldo < produk['harga']:
            logger.warning(f"❌ Insufficient balance in final check: {saldo} < {produk['harga']}")
            await update.message.reply_text(
                f"❌ Saldo tidak cukup!\n"
                f"Produk: {produk['nama']} - Rp {produk['harga']:,}\n"
                f"Saldo kamu: Rp {saldo:,}\n\n"
                "Silakan top up terlebih dahulu.",
                reply_markup=reply_main_menu(is_admin=is_admin)
            )
            return ConversationHandler.END

        context.user_data["tujuan"] = text
        context.user_data["ref_id"] = str(uuid.uuid4())[:8].upper()
        
        logger.info(f"✅ Ready for confirmation - Ref: {context.user_data['ref_id']}, Tujuan: {text}")
        
        await update.message.reply_text(
            f"📋 <b>KONFIRMASI ORDER</b>\n\n"
            f"🆔 Ref ID: <code>{context.user_data['ref_id']}</code>\n"
            f"📦 Produk: <b>{produk['nama']}</b>\n"
            f"💰 Harga: <b>Rp {produk['harga']:,}</b>\n"
            f"📱 Tujuan: <b>{text}</b>\n"
            f"📊 Stok: <b>{produk.get('kuota', 0)}</b>\n\n"
            f"Klik <b>Konfirmasi</b> untuk melanjutkan atau <b>Batal</b> untuk membatalkan.",
            parse_mode=ParseMode.HTML,
            reply_markup=konfirmasi_order_keyboard()
        )
        return KONFIRMASI

    @staticmethod
    async def handle_konfirmasi(update: Update, context: CallbackContext):
        """Handler untuk konfirmasi order akhir"""
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

    @staticmethod
    async def topup_nominal_step(update: Update, context: CallbackContext):
        """Handler untuk memproses nominal topup"""
        user = update.message.from_user
        text = update.message.text.strip()

        if text == '/batal':
            await OrderHandlers.cancel(update, context)
            return ConversationHandler.END

        try:
            nominal = int(text)
            if nominal < 10000:
                await update.message.reply_text(
                    "❌ Nominal terlalu kecil! Minimal top up adalah Rp 10,000\n"
                    "Silakan masukkan nominal yang valid:"
                )
                return TOPUP_NOMINAL

            # Generate kode unik
            kode_unik = random.randint(1, 99)
            total_bayar = nominal + kode_unik

            # Simpan data topup
            topup_data = {
                'user_id': user.id,
                'user_name': user.first_name,
                'nominal': nominal,
                'kode_unik': kode_unik,
                'total_bayar': total_bayar,
                'status': 'pending',
                'timestamp': datetime.now().isoformat()
            }

            context.user_data['topup_data'] = topup_data

            # Kirim instruksi pembayaran
            message = (
                f"💳 <b>DETAIL TOP UP</b>\n\n"
                f"👤 User: {user.first_name}\n"
                f"💰 Nominal: Rp {nominal:,}\n"
                f"🎯 Kode Unik: {kode_unik}\n"
                f"💵 <b>Total Bayar: Rp {total_bayar:,}</b>\n\n"
                f"📝 <b>INSTRUKSI PEMBAYARAN:</b>\n"
                f"1. Transfer tepat <b>Rp {total_bayar:,}</b>\n"
                f"2. Ke rekening: <b>1234-5678-9012 (BRI)</b>\n"
                f"3. Konfirmasi ke admin setelah transfer\n\n"
                f"Saldo akan otomatis ditambahkan setelah admin approve."
            )

            await update.message.reply_text(message, parse_mode=ParseMode.HTML)

            # Notify admin
            admin_message = (
                f"🔔 <b>PERMINTAAAN TOP UP BARU</b>\n\n"
                f"👤 User: {user.first_name} (@{user.username or 'N/A'})\n"
                f"🆔 ID: <code>{user.id}</code>\n"
                f"💰 Nominal: Rp {nominal:,}\n"
                f"🎯 Kode Unik: {kode_unik}\n"
                f"💵 Total: Rp {total_bayar:,}\n"
                f"⏰ Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message,
                        parse_mode=ParseMode.HTML,
                        reply_markup=topup_admin_keyboard(user.id)
                    )
                except Exception as e:
                    logging.error(f"Gagal mengirim notifikasi ke admin {admin_id}: {e}")

            # Simpan ke database
            tambah_topup_db(user.id, topup_data)

            await update.message.reply_text(
                "✅ Permintaan top up telah dikirim ke admin.\n"
                "Silakan tunggu approval.",
                reply_markup=reply_main_menu(user.id)
            )

            return ConversationHandler.END

        except ValueError:
            await update.message.reply_text(
                "❌ Format nominal tidak valid! Harus angka.\n"
                "Contoh: <code>100000</code>\n\n"
                "Silakan masukkan nominal yang valid:"
            )
            return TOPUP_NOMINAL

    @staticmethod
    async def admin_topup_callback(update: Update, context: CallbackContext):
        """Handler untuk admin mengelola topup"""
        query = update.callback_query
        user = query.from_user
        data = query.data

        await query.answer()

        if user.id not in ADMIN_IDS:
            await query.edit_message_text("❌ Akses ditolak.")
            return

        if data.startswith("topup_approve|"):
            user_id = int(data.split("|")[1])
            topup_data = None

            # Cari data topup terbaru user
            all_topup = get_all_topup()
            user_topup = all_topup.get(str(user_id), [])
            if user_topup:
                topup_data = user_topup[-1]  # Ambil yang terbaru

            if not topup_data:
                await query.edit_message_text("❌ Data top up tidak ditemukan.")
                return

            # Approve topup
            nominal = topup_data['nominal']
            result = await tambah_saldo_user(
                user_id, 
                nominal, 
                "topup", 
                f"Top up approved by admin {user.first_name}"
            )

            if result['success']:
                # Update status topup
                topup_data['status'] = 'approved'
                topup_data['approved_by'] = user.first_name
                topup_data['approved_at'] = datetime.now().isoformat()
                tambah_topup_db(user_id, topup_data)

                await query.edit_message_text(
                    f"✅ Top up approved!\n"
                    f"User: {topup_data.get('user_name', 'Unknown')}\n"
                    f"Nominal: Rp {nominal:,}\n"
                    f"Saldo baru: Rp {result['saldo_sekarang']:,}"
                )

                # Notify user
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"✅ Top up Anda telah disetujui!\n\n"
                             f"💰 Nominal: Rp {nominal:,}\n"
                             f"💳 Saldo sekarang: Rp {result['saldo_sekarang']:,}\n\n"
                             f"Terima kasih! 😊"
                    )
                except Exception as e:
                    logging.error(f"Gagal mengirim notifikasi ke user {user_id}: {e}")

            else:
                await query.edit_message_text("❌ Gagal menambahkan saldo.")

        elif data.startswith("topup_batal|"):
            user_id = int(data.split("|")[1])
            
            # Update status topup
            all_topup = get_all_topup()
            user_topup = all_topup.get(str(user_id), [])
            if user_topup:
                topup_data = user_topup[-1]
                topup_data['status'] = 'rejected'
                topup_data['rejected_by'] = user.first_name
                topup_data['rejected_at'] = datetime.now().isoformat()
                tambah_topup_db(user_id, topup_data)

            await query.edit_message_text("❌ Top up ditolak.")

            # Notify user
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="❌ Top up Anda ditolak oleh admin.\n"
                         "Silakan hubungi admin untuk informasi lebih lanjut."
                )
            except Exception as e:
                logging.error(f"Gagal mengirim notifikasi ke user {user_id}: {e}")

    @staticmethod
    async def reply_menu_handler(update: Update, context: CallbackContext):
        """Handler untuk reply keyboard menu"""
        user = update.message.from_user
        text = update.message.text

        if text == "❓ Bantuan":
            help_text = (
                "🤖 <b>BANTUAN & CARA PENGGUNAAN</b>\n\n"
                "📋 <b>Fitur yang tersedia:</b>\n"
                "• 🛒 <b>Order Produk</b> - Beli produk digital\n"
                "• 💰 <b>Lihat Saldo</b> - Cek saldo akun\n"
                "• 📦 <b>Cek Stok</b> - Lihat ketersediaan produk\n"
                "• 📋 <b>Riwayat Transaksi</b> - Lihat history transaksi\n"
                "• 💳 <b>Top Up Saldo</b> - Isi saldo akun\n"
                "• 🔍 <b>Cek Status</b> - Pantau status order\n\n"
                "📞 <b>Butuh bantuan?</b>\n"
                "Hubungi admin untuk pertanyaan lebih lanjut."
            )
            await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

        elif text == "👑 Admin Panel" and user.id in ADMIN_IDS:
            admin_text = (
                "👑 <b>ADMIN PANEL</b>\n\n"
                "Fitur admin yang tersedia:\n"
                "• Auto approve/reject top up via notifikasi\n"
                "• Monitor semua transaksi user\n"
                "• Kelola produk dan stok\n\n"
                "Gunakan menu biasa untuk akses fitur user."
            )
            await update.message.reply_text(admin_text, parse_mode=ParseMode.HTML)

        else:
            await update.message.reply_text(
                "❌ Perintah tidak dikenali. Silakan gunakan menu yang tersedia.",
                reply_markup=reply_main_menu(user.id)
            )

# ============================ EXPORT FUNCTIONS ============================
# Export functions untuk compatibility dengan kode lama
handle_all_callbacks = OrderHandlers.handle_all_callbacks
lihat_produk_callback = OrderHandlers.lihat_produk_callback
produk_pilih_callback = OrderHandlers.produk_pilih_callback
handle_input_tujuan = OrderHandlers.handle_input_tujuan
handle_konfirmasi = OrderHandlers.handle_konfirmasi
start = OrderHandlers.start
cancel = OrderHandlers.cancel
stock_akrab_callback = OrderHandlers.stock_akrab_callback
lihat_saldo_callback = OrderHandlers.lihat_saldo_callback
riwayat_callback = OrderHandlers.riwayat_callback
cek_status_callback = OrderHandlers.cek_status_callback
topup_callback = OrderHandlers.topup_callback
topup_nominal_step = OrderHandlers.topup_nominal_step
admin_topup_callback = OrderHandlers.admin_topup_callback
reply_menu_handler = OrderHandlers.reply_menu_handler

# ============================ MAIN BOT SETUP ============================
def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def log_error(error_text):
    """Log error to file"""
    with open("error.log", "a", encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {error_text}\n")

def main():
    """Main function to run the bot"""
    print("=" * 60)
    print("🤖 BOT STARTING - SINGLE FILE VERSION")
    print("=" * 60)
    
    try:
        setup_logging()
        logger = logging.getLogger(__name__)
        
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher

        # Callback query handler
        dp.add_handler(CallbackQueryHandler(handle_all_callbacks))

        # Order conversation handler
        order_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(Filters.regex("^(🛒 Order Produk)$"), lihat_produk_callback)],
            states={
                CHOOSING_PRODUK: [
                    CallbackQueryHandler(produk_pilih_callback, pattern="^produk_static\\|"),
                    CallbackQueryHandler(produk_pilih_callback, pattern="^back_main$")
                ],
                INPUT_TUJUAN: [MessageHandler(Filters.text & ~Filters.command, handle_input_tujuan)],
                KONFIRMASI: [
                    CallbackQueryHandler(handle_konfirmasi, pattern="^(order_konfirmasi|order_batal)$"),
                    MessageHandler(Filters.text & ~Filters.command, handle_konfirmasi)
                ]
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            allow_reentry=True,
        )
        dp.add_handler(order_conv_handler)

        # Topup conversation handler
        topup_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(Filters.regex("^(💳 Top Up Saldo)$"), topup_callback)],
            states={TOPUP_NOMINAL: [MessageHandler(Filters.text & ~Filters.command, topup_nominal_step)]},
            fallbacks=[CommandHandler('cancel', cancel)],
            allow_reentry=True,
        )
        dp.add_handler(topup_conv_handler)

        # Command handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", start))
        dp.add_handler(CommandHandler("menu", start))
        dp.add_handler(CommandHandler("cancel", cancel))
        dp.add_handler(CommandHandler("batal", cancel))

        # Message handlers for menu buttons
        dp.add_handler(MessageHandler(Filters.regex("^(📦 Cek Stok)$"), stock_akrab_callback))
        dp.add_handler(MessageHandler(Filters.regex("^(📋 Riwayat Transaksi)$"), riwayat_callback))
        dp.add_handler(MessageHandler(Filters.regex("^(💰 Lihat Saldo)$"), lihat_saldo_callback))
        dp.add_handler(MessageHandler(Filters.regex("^(🔍 Cek Status)$"), cek_status_callback))
        dp.add_handler(MessageHandler(Filters.regex("^(❓ Bantuan)$"), start))

        # Admin callback handlers
        dp.add_handler(CallbackQueryHandler(admin_topup_callback, pattern="^topup_(approve|batal)\\|"))

        # Fallback message handler
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reply_menu_handler))

        # Error handler
        def error_handler(update, context):
            try:
                error_msg = f"Error: {context.error}"
                logger.error(error_msg)
                log_error(error_msg)
                if update and update.effective_message:
                    is_admin = update.effective_user and update.effective_user.id in ADMIN_IDS
                    update.effective_message.reply_text(
                        "❌ Maaf, terjadi kesalahan sistem. Silakan coba lagi.",
                        reply_markup=reply_main_menu(is_admin=is_admin)
                    )
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
        dp.add_error_handler(error_handler)

        # Start bot
        updater.bot.delete_webhook()
        time.sleep(1)
        
        print("🔄 Memulai polling...")
        print("✅ Semua handler terpasang")
        
        updater.start_polling(drop_pending_updates=True)
        
        print("🎉 BOT BERHASIL DIJALANKAN!")
        print("🤖 Bot sedang berjalan...")
        print("=" * 60)
        
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Gagal menjalankan bot: {e}")
        log_error(f"❌ Gagal menjalankan bot: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
