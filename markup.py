from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import ADMIN_IDS
from produk import get_produk_list

def is_admin(user_id):
    return user_id in ADMIN_IDS

def menu_user():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📦 Lihat Produk", callback_data='lihat_produk'),
            InlineKeyboardButton("🛒 Beli Produk", callback_data='beli_produk')
        ],
        [
            InlineKeyboardButton("💸 Top Up", callback_data='topup'),
            InlineKeyboardButton("🔍 Cek Status", callback_data='cek_status')
        ],
        [
            InlineKeyboardButton("📄 Riwayat", callback_data='riwayat'),
            InlineKeyboardButton("📊 Stock XL/Axis", callback_data='stock_akrab')
        ],
    ])

def menu_admin():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📦 Produk", callback_data='lihat_produk'),
            InlineKeyboardButton("🛒 Beli", callback_data='beli_produk'),
            InlineKeyboardButton("💸 Top Up", callback_data='topup')
        ],
        [
            InlineKeyboardButton("📄 Riwayat", callback_data='riwayat'),
            InlineKeyboardButton("🔍 Cek Status", callback_data='cek_status'),
            InlineKeyboardButton("📊 Stock", callback_data='stock_akrab')
        ],
        [
            InlineKeyboardButton("📝 Manage Produk", callback_data='manajemen_produk'),
            InlineKeyboardButton("🗃️ Semua Riwayat", callback_data='semua_riwayat')
        ],
        [
            InlineKeyboardButton("💰 Lihat Saldo", callback_data='lihat_saldo'),
            InlineKeyboardButton("➕ Tambah Saldo", callback_data='tambah_saldo')
        ],
    ])

def get_menu(user_id):
    return menu_admin() if is_admin(user_id) else menu_user()

def produk_inline_keyboard():
    produk_list = get_produk_list()
    keyboard = []
    for i, p in enumerate(produk_list):
        status = "✅" if p.get("kuota", 0) > 0 else "❌"
        label = f"{status} {p['nama']} | Rp {p['harga']:,}"
        keyboard.append([
            InlineKeyboardButton(label, callback_data=f"produk_static|{i}")
        ])
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)

def admin_edit_produk_keyboard(kode):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💵 Edit Harga", callback_data=f"editharga|{kode}"),
            InlineKeyboardButton("📝 Edit Deskripsi", callback_data=f"editdeskripsi|{kode}")
        ],
        [
            InlineKeyboardButton("🔄 Reset Custom", callback_data=f"resetcustom|{kode}"),
            InlineKeyboardButton("⬅️ Kembali", callback_data="back_admin")
        ]
    ])
