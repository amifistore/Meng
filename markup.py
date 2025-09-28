from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# ========== INLINE KEYBOARDS ==========

def main_menu_markup(is_admin=False):
    buttons = [
        [InlineKeyboardButton("🛒 Order Produk", callback_data="beli_produk")],
        [InlineKeyboardButton("💳 Top Up Saldo", callback_data="topup")],
        [InlineKeyboardButton("📦 Cek Stock", callback_data="stock_akrab")],
        [InlineKeyboardButton("📋 Riwayat Transaksi", callback_data="riwayat")],
        [InlineKeyboardButton("💰 Lihat Saldo", callback_data="lihat_saldo")],
        [InlineKeyboardButton("🔍 Cek Status", callback_data="cek_status")],
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
    buttons = [[InlineKeyboardButton(kategori['nama'], callback_data=f"category|{kategori['id']}")] for kategori in kategori_list]
    buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")])
    return InlineKeyboardMarkup(buttons)

def produk_list_markup(produk_list):
    buttons = [[InlineKeyboardButton(f"{produk['nama']} ({produk['harga']:,})", callback_data=f"produk|{produk['id']}")] for produk in produk_list]
    buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")])
    return InlineKeyboardMarkup(buttons)

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
        [InlineKeyboardButton("✅ Konfirmasi Topup", callback_data="confirm_topup"),
         InlineKeyboardButton("❌ Batalkan", callback_data="cancel_topup")],
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

def riwayat_menu_markup():
    buttons = [
        [InlineKeyboardButton("Semua Riwayat", callback_data="semua_riwayat")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")]
    ]
    return InlineKeyboardMarkup(buttons)

def stock_menu_markup():
    buttons = [
        [InlineKeyboardButton("Cek Stock", callback_data="stock_akrab")],
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

# ========== REPLY KEYBOARDS ==========

def reply_main_menu():
    buttons = [
        [KeyboardButton("🛒 Order Produk"), KeyboardButton("💳 Top Up Saldo")],
        [KeyboardButton("📦 Cek Stock"), KeyboardButton("📋 Riwayat Transaksi")],
        [KeyboardButton("💰 Lihat Saldo"), KeyboardButton("🔍 Cek Status")],
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
    """
    buttons: list of list, e.g.
    [
        [("Tombol 1", "cb_data_1"), ("Tombol 2", "cb_data_2")],
        [("Tombol 3", "cb_data_3")]
    ]
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text, cbdata) for text, cbdata in row]
        for row in buttons
    ])

def custom_reply_keyboard(buttons):
    """
    buttons: list of list, e.g.
    [
        ["Tombol 1", "Tombol 2"],
        ["Tombol 3"]
    ]
    """
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# ========== END OF FILE ==========
