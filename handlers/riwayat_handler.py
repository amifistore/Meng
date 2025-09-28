# handlers/riwayat_handler.py
from telegram import ParseMode
from saldo import get_riwayat_saldo, get_all_user_ids
from riwayat import get_riwayat_user, cari_riwayat_order
from markup import get_menu, is_admin

def riwayat_callback(update, context):
    """Callback untuk tombol Riwayat transaksi user di menu utama"""
    user = update.callback_query.from_user
    update.callback_query.answer()
    
    # Ambil riwayat saldo dan order
    riwayat_saldo_data = get_riwayat_saldo(user.id)
    riwayat_order_data = get_riwayat_user(user.id)
    
    msg = ""
    if not riwayat_saldo_data and not riwayat_order_data:
        msg = "📄 *Riwayat Transaksi Kosong*\n\nBelum ada transaksi yang dilakukan."
    else:
        msg = "📄 *Riwayat Transaksi Terakhir*\n\n"
        
        # Riwayat Saldo (topup/potongan)
        if riwayat_saldo_data:
            msg += "*Riwayat Saldo:*\n"
            for i, trx in enumerate(riwayat_saldo_data[:5], 1):
                tipe, jumlah, keterangan, tanggal = trx
                status = "💰" if jumlah > 0 else "💸"
                msg += f"{i}. {status} {tipe}: Rp {jumlah:+,}\n"
                msg += f"   📝 {keterangan}\n"
                msg += f"   🕒 {tanggal}\n\n"
        
        # Riwayat Order
        if riwayat_order_data:
            msg += "*Riwayat Order:*\n"
            for i, order in enumerate(riwayat_order_data[:5], 1):
                ref_id, produk, harga, tujuan, status, tanggal, sn, keterangan = order
                status_icon = "✅" if status == "success" else "❌"
                msg += f"{i}. {status_icon} {produk} - Rp {harga:,}\n"
                msg += f"   📱 {tujuan} | 🆔 {ref_id[:8]}...\n"
                if sn and sn != 'N/A':
                    msg += f"   🎫 SN: {sn}\n"
                msg += f"   🕒 {tanggal}\n\n"
    
    info_text, markup = get_menu(user.id)
    update.callback_query.edit_message_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

def semua_riwayat_callback(update, context):
    """Callback untuk tombol Semua Riwayat (admin) di menu admin"""
    user = update.callback_query.from_user
    update.callback_query.answer()
    
    if not is_admin(user.id):
        info_text, markup = get_menu(user.id)
        update.callback_query.edit_message_text(
            "❌ Akses ditolak.",
            reply_markup=markup
        )
        return
    
    # Ambil semua riwayat saldo
    all_riwayat_saldo = get_riwayat_saldo(limit=50)
    all_user_ids = get_all_user_ids()
    
    user_map = {}
    total_saldo = 0
    
    # Process riwayat saldo
    if all_riwayat_saldo:
        for row in all_riwayat_saldo:
            user_id, tipe, jumlah, keterangan, tanggal = row
            if user_id not in user_map:
                user_map[user_id] = {"saldo": [], "order": []}
            user_map[user_id]["saldo"].append((tipe, jumlah, keterangan, tanggal))
            total_saldo += jumlah
    
    # Process riwayat order untuk semua user
    for user_id in all_user_ids:
        riwayat_order = get_riwayat_user(user_id, limit=3)
        if riwayat_order:
            if user_id not in user_map:
                user_map[user_id] = {"saldo": [], "order": []}
            user_map[user_id]["order"].extend(riwayat_order)
    
    if not user_map:
        msg = "📄 *Semua Riwayat Kosong*\n\nBelum ada transaksi dari semua user."
    else:
        msg = "📄 *Semua Riwayat Transaksi*\n\n"
        for user_id, transaksi in user_map.items():
            msg += f"👤 User `{user_id}`:\n"
            
            # Tampilkan riwayat saldo
            for trx in transaksi["saldo"][:2]:
                tipe, jumlah, keterangan, tanggal = trx
                status = "💰" if jumlah > 0 else "💸"
                msg += f"   {status} {tipe}: Rp {jumlah:+,}\n"
                msg += f"   📝 {keterangan[:30]}...\n"
            
            # Tampilkan riwayat order
            for order in transaksi["order"][:2]:
                ref_id, produk, harga, tujuan, status, tanggal, sn, keterangan = order
                status_icon = "✅" if status == "success" else "❌"
                msg += f"   {status_icon} {produk}: Rp {harga:,}\n"
                msg += f"   📱 {tujuan}\n"
            
            msg += "\n"
        
        msg += f"💰 *Total Saldo Diproses: Rp {total_saldo:,}*"
    
    info_text, markup = get_menu(user.id)
    update.callback_query.edit_message_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

def riwayat_user(update, context):
    """Bisa dipanggil via command (misal /riwayat) atau callback"""
    user = update.effective_user
    
    # Ambil riwayat saldo dan order
    riwayat_saldo_data = get_riwayat_saldo(user.id)
    riwayat_order_data = get_riwayat_user(user.id)
    
    msg = ""
    if not riwayat_saldo_data and not riwayat_order_data:
        msg = "📄 *Riwayat Transaksi Kosong*\n\nBelum ada transaksi yang dilakukan."
    else:
        msg = "📄 *Riwayat Transaksi Terakhir*\n\n"
        
        # Riwayat Saldo (topup/potongan)
        if riwayat_saldo_data:
            msg += "*Riwayat Saldo:*\n"
            for i, trx in enumerate(riwayat_saldo_data[:5], 1):
                tipe, jumlah, keterangan, tanggal = trx
                status = "💰" if jumlah > 0 else "💸"
                msg += f"{i}. {status} {tipe}: Rp {jumlah:+,}\n"
                msg += f"   📝 {keterangan}\n"
                msg += f"   🕒 {tanggal}\n\n"
        
        # Riwayat Order
        if riwayat_order_data:
            msg += "*Riwayat Order:*\n"
            for i, order in enumerate(riwayat_order_data[:5], 1):
                ref_id, produk, harga, tujuan, status, tanggal, sn, keterangan = order
                status_icon = "✅" if status == "success" else "❌"
                msg += f"{i}. {status_icon} {produk} - Rp {harga:,}\n"
                msg += f"   📱 {tujuan} | 🆔 {ref_id[:8]}...\n"
                if sn and sn != 'N/A':
                    msg += f"   🎫 SN: {sn}\n"
                msg += f"   🕒 {tanggal}\n\n"
    
    info_text, markup = get_menu(user.id)
    update.message.reply_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )
