from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# ========== INLINE KEYBOARDS ==========

def main_menu_markup(is_admin=False):
    buttons = [
        [InlineKeyboardButton("🛒 Order Produk", callback_data="beli_produk")],
        [InlineKeyboardButton("💳 Top Up Saldo", callback_data="topup")],
        [InlineKeyboardButton("📦 Cek Stok", callback_data="stock_akrab")],
        [InlineKeyboardButton("📋 Riwayat Transaksi", callback_data="riwayat")],
        [InlineKeyboardButton("💰 Lihat Saldo", callback_data="lihat_saldo")],
        [InlineKeyboardButton("🔍 Cek Status", callback_data="cek_status")],
        [InlineKeyboardButton("❓ Bantuan", callback_data="help")],
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="back_admin")])
    return InlineKeyboardMarkup(buttons)

def admin_menu_markup():
    buttons = [
        [InlineKeyboardButton("📝 Manajemen Produk", callback_data="manajemen_produk")],
        [InlineKeyboardButton("💳 Approve Topup", callback_data="riwayat_topup_admin")],
        [InlineKeyboardButton("👤 Tambah Saldo User", callback_data="tambah_saldo")],
        [InlineKeyboardButton("🏠 Kembali ke Main Menu", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(buttons)

def produk_kategori_markup(kategori_list):
    buttons = [[InlineKeyboardButton(kat['nama'], callback_data=f"category|{kat['id']}")] for kat in kategori_list]
    buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")])
    return InlineKeyboardMarkup(buttons)

def produk_list_markup(produk_list):
    buttons = [
        [InlineKeyboardButton(f"{prod['nama']} ({prod['harga']:,})", callback_data=f"produk|{prod['kode']}")]
        for prod in produk_list
    ]
    buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")])
    return InlineKeyboardMarkup(buttons)

def produk_inline_keyboard(produk_list):
    return produk_list_markup(produk_list)

def konfirmasi_order_markup():
    buttons = [
        [InlineKeyboardButton("✅ Konfirmasi", callback_data="konfirmasi_order"),
         InlineKeyboardButton("❌ Batalkan", callback_data="batal_order")],
        [InlineKeyboardButton("⬅️ Kembali ke Menu", callback_data="back_menu")]
    ]
    return InlineKeyboardMarkup(buttons)

def topup_nominal_markup():
    buttons = [
        [InlineKeyboardButton("50.000", callback_data="topup_nominal|50000"),
         InlineKeyboardButton("100.000", callback_data="topup_nominal|100000")],
        [InlineKeyboardButton("200.000", callback_data="topup_nominal|200000"),
         InlineKeyboardButton("500.000", callback_data="topup_nominal|500000")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")]
    ]
    return InlineKeyboardMarkup(buttons)

def confirm_topup_markup():
    buttons = [
        [InlineKeyboardButton("✅ Konfirmasi Topup", callback_data="topup_konfirm"),
         InlineKeyboardButton("❌ Batalkan", callback_data="back_menu")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")]
    ]
    return InlineKeyboardMarkup(buttons)

def admin_topup_action_markup(topup_id):
    buttons = [
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_topup|{topup_id}"),
         InlineKeyboardButton("❌ Reject", callback_data=f"reject_topup|{topup_id}")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="riwayat_topup_admin")]
    ]
    return InlineKeyboardMarkup(buttons)

def edit_produk_markup(produk_id):
    buttons = [
        [InlineKeyboardButton("Edit Harga", callback_data=f"editharga|{produk_id}"),
         InlineKeyboardButton("Edit Deskripsi", callback_data=f"editdeskripsi|{produk_id}")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="manajemen_produk")]
    ]
    return InlineKeyboardMarkup(buttons)

def admin_edit_produk_keyboard(produk_id):
    return edit_produk_markup(produk_id)

def riwayat_menu_markup():
    buttons = [
        [InlineKeyboardButton("Semua Riwayat", callback_data="semua_riwayat")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")]
    ]
    return InlineKeyboardMarkup(buttons)

def stock_menu_markup():
    buttons = [
        [InlineKeyboardButton("Cek Stok", callback_data="stock_akrab")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")]
    ]
    return InlineKeyboardMarkup(buttons)

def saldo_menu_markup():
    buttons = [
        [InlineKeyboardButton("Tambah Saldo", callback_data="tambah_saldo")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")]
    ]
    return InlineKeyboardMarkup(buttons)

def status_menu_markup():
    buttons = [
        [InlineKeyboardButton("Cek Status", callback_data="cek_status")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")]
    ]
    return InlineKeyboardMarkup(buttons)

def help_menu_markup():
    buttons = [
        [InlineKeyboardButton("⬅️ Kembali ke Menu", callback_data="back_menu")]
    ]
    return InlineKeyboardMarkup(buttons)

# ========== REPLY KEYBOARDS ==========

def reply_main_menu():
    buttons = [
        [KeyboardButton("🛒 Order Produk"), KeyboardButton("💳 Top Up Saldo")],
        [KeyboardButton("📦 Cek Stok"), KeyboardButton("📋 Riwayat Transaksi")],
        [KeyboardButton("💰 Lihat Saldo"), KeyboardButton("🔍 Cek Status")],
        [KeyboardButton("❓ Bantuan")],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def reply_cancel_menu():
    buttons = [
        [KeyboardButton("❌ Batal"), KeyboardButton("⬅️ Kembali")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def reply_admin_panel():
    buttons = [
        [KeyboardButton("📝 Manajemen Produk")],
        [KeyboardButton("💳 Approve Topup")],
        [KeyboardButton("👤 Tambah Saldo User")],
        [KeyboardButton("🏠 Kembali ke Main Menu")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# ========== UTILITY ==========

def custom_inline_keyboard(buttons):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text, cbdata) for text, cbdata in row]
        for row in buttons
    ])

def custom_reply_keyboard(buttons):
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_menu(is_admin=False):
    info_text = (
        "<b>🤖 Selamat datang di Bot PPOB!</b>\n\n"
        "Silakan pilih menu di bawah ini untuk mulai transaksi, cek saldo, riwayat, dan lain-lain."
    )
    markup = main_menu_markup(is_admin=is_admin)
    return info_text, markup

# ========== END OF FILE ==========
