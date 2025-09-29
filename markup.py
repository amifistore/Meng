from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Inline keyboard menu utama (tombol di pesan bot)
def main_menu_markup(is_admin=False):
    buttons = [
        [InlineKeyboardButton("🛒 Order Produk", callback_data="beli_produk")],
        [InlineKeyboardButton("💳 Top Up Saldo", callback_data="topup")],
        [InlineKeyboardButton("📦 Cek Stok", callback_data="stock_akrab")],
        [InlineKeyboardButton("📋 Riwayat Transaksi", callback_data="riwayat")],
        [InlineKeyboardButton("💰 Lihat Saldo", callback_data="lihat_saldo")],
        [InlineKeyboardButton("🔍 Cek Status", callback_data="cek_status")],
        [InlineKeyboardButton("❓ Bantuan", callback_data="help")]
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="back_admin")])
    return InlineKeyboardMarkup(buttons)

# Reply keyboard menu utama (tombol di bawah chat, user/admin)
def get_menu(is_admin=False):
    buttons = [
        [KeyboardButton("🛒 Order Produk"), KeyboardButton("💳 Top Up Saldo")],
        [KeyboardButton("📦 Cek Stok"), KeyboardButton("📋 Riwayat Transaksi")],
        [KeyboardButton("💰 Lihat Saldo"), KeyboardButton("🔍 Cek Status")],
        [KeyboardButton("❓ Bantuan")]
    ]
    if is_admin:
        buttons.append([KeyboardButton("🛠 Admin Panel")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# Alias agar handler lama tetap berjalan
reply_main_menu = get_menu

# Inline keyboard produk (daftar produk, fallback jika kosong)
def produk_inline_keyboard(produk_list=None):
    buttons = []
    if produk_list:
        for produk in produk_list:
            # PERBAIKAN: Pastikan id produk selalu string
            produk_id = str(produk.get('id', ''))
            produk_nama = produk.get('nama', produk_id)
            buttons.append([InlineKeyboardButton(
                produk_nama,
                callback_data=f"produk|{produk_id}"  # Sudah string
            )])
    else:
        buttons.append([InlineKeyboardButton("Tidak ada produk tersedia", callback_data="produk|none")])
    
    # PERBAIKAN: Tambahkan tombol kembali
    buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")])
    
    return InlineKeyboardMarkup(buttons)

# Inline keyboard admin edit produk (panel admin)
def admin_edit_produk_keyboard(produk_id):
    # PERBAIKAN: Pastikan produk_id selalu string
    produk_id = str(produk_id)
    buttons = [
        [InlineKeyboardButton("✏️ Edit Harga", callback_data=f"editharga|{produk_id}")],
        [InlineKeyboardButton("✏️ Edit Deskripsi", callback_data=f"editdeskripsi|{produk_id}")],
        [InlineKeyboardButton("✏️ Edit Stok", callback_data=f"editstok|{produk_id}")],
        [InlineKeyboardButton("🗑 Hapus Produk", callback_data=f"hapusproduk|{produk_id}")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_admin")]
    ]
    return InlineKeyboardMarkup(buttons)

# Keyboard untuk konfirmasi admin
def admin_confirmation_keyboard(action, item_id):
    item_id = str(item_id)
    buttons = [
        [
            InlineKeyboardButton("✅ Ya", callback_data=f"confirm_{action}|{item_id}"),
            InlineKeyboardButton("❌ Tidak", callback_data="cancel_admin")
        ],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_admin")]
    ]
    return InlineKeyboardMarkup(buttons)

# Keyboard untuk pilihan topup
def topup_inline_keyboard():
    buttons = [
        [InlineKeyboardButton("💳 Transfer Bank", callback_data="topup_bank")],
        [InlineKeyboardButton("📱 E-Wallet", callback_data="topup_ewallet")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(buttons)

# Keyboard untuk bantuan
def help_inline_keyboard():
    buttons = [
        [InlineKeyboardButton("📞 Kontak Admin", callback_data="contact_admin")],
        [InlineKeyboardButton("❓ FAQ", callback_data="faq")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(buttons)
