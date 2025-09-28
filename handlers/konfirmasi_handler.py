# Di handlers/konfirmasi_handler.py - tambahkan fungsi safe_int_convert

def safe_int_convert(value):
    """Convert value to integer safely"""
    try:
        if isinstance(value, str):
            # Remove any non-digit characters except minus
            cleaned = ''.join(c for c in value if c.isdigit() or c == '-')
            return int(cleaned) if cleaned else 0
        elif isinstance(value, (int, float)):
            return int(value)
        else:
            return 0
    except (ValueError, TypeError):
        return 0

# Di setiap fungsi yang menggunakan harga, tambahkan konversi:
def handle_successful_order(result, msg_proc, user, produk, tujuan, ref_id, sn, context):
    """Handle successful order untuk inline button"""
    try:
        # PASTIKAN harga adalah integer dengan safe conversion
        harga = safe_int_convert(produk['harga'])
        
        # Potong saldo user
        if not kurang_saldo_user(user.id, harga, tipe="order", 
                               keterangan=f"Order {produk['kode']} ke {tujuan}"):
            msg_proc.edit_text(
                f"❌ <b>GAGAL POTONG SALDO</b>\n\n"
                f"Order berhasil di provider tapi gagal memotong saldo.\n"
                f"Silakan hubungi admin untuk refund.",
                parse_mode=ParseMode.HTML
            )
            context.user_data.clear()
            return ConversationHandler.END
        
        # Simpan riwayat transaksi
        transaksi = {
            "ref_id": ref_id,
            "kode": produk['kode'],
            "tujuan": tujuan,
            "harga": harga,  # Gunakan harga yang sudah di-convert
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
            f"💰 Harga: <b>Rp {harga:,}</b>\n"  # Gunakan harga yang sudah di-convert
            f"📱 Tujuan: <b>{tujuan}</b>\n"
            f"🎫 SN: <code>{sn}</code>\n\n"
            f"💾 Status: <b>{result.get('message', 'Success')}</b>\n\n"
            f"Terima kasih telah berbelanja! 🛍️",
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"Error handling successful order {ref_id}: {str(e)}")
        msg_proc.edit_text(
            f"⚠️ <b>ORDER BERHASIL TAPI ADA KENDALA SYSTEM</b>\n\n"
            f"Order di provider sukses tapi ada kendala system.\n"
            f"Ref ID: <code>{ref_id}</code>\n"
            f"Silakan hubungi admin dengan Ref ID di atas.",
            parse_mode=ParseMode.HTML
        )
    
    finally:
        context.user_data.clear()
        return ConversationHandler.END
