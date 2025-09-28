from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import ADMIN_IDS
from produk import get_produk_list
from saldo import get_saldo_user
from database import get_riwayat_saldo

def is_admin(user_id):
    return user_id in ADMIN_IDS

def menu_user(user_id):
    # Info user: ID, saldo, riwayat transaksi
    info_text = f"🆔 <b>ID User:</b> <code>{user_id}</code>\n"
    saldo = get_saldo_user(user_id)
    info_text += f"💰 <b>Saldo:</b> Rp {saldo:,}\n"
    riwayat = get_riwayat_saldo(user_id, limit=3)
    if riwayat:
        info_text += "📄 <b>Riwayat Terakhir:</b>\n"
        for i, trx in enumerate(reversed(riwayat), 1):
            tipe = trx[1]
            nominal = trx[2]
            ket = trx[3]
            waktu = trx[0]
            status = "✅" if nominal > 0 else "❌"
            info_text += f"{i}. {status} {tipe} {nominal:+,} ({ket})\n"
    else:
        info_text += "📄 <i>Belum ada riwayat transaksi.</i>\n"

    keyboard = [
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
    ]
    return info_text, InlineKeyboardMarkup(keyboard)

def menu_admin(user_id):
    info_text = f"🆔 <b>ID Admin:</b> <code>{user_id}</code>\n"
    saldo = get_saldo_user(user_id)
    info_text += f"💰 <b>Saldo:</b> Rp {saldo:,}\n"
    riwayat = get_riwayat_saldo(user_id, limit=3)
    if riwayat:
        info_text += "📄 <b>Riwayat Terakhir:</b>\n"
        for i, trx in enumerate(reversed(riwayat), 1):
            tipe = trx[1]
            nominal = trx[2]
            ket = trx[3]
            waktu = trx[0]
            status = "✅" if nominal > 0 else "❌"
            info_text += f"{i}. {status} {tipe} {nominal:+,} ({ket})\n"
    else:
        info_text += "📄 <i>Belum ada riwayat transaksi.</i>\n"

    keyboard = [
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
    ]
    return info_text, InlineKeyboardMarkup(keyboard)

def get_menu(user_id):
    if is_admin(user_id):
        return menu_admin(user_id)
    else:
        return menu_user(user_id)

def produk_inline_keyboard():
    produk_list = get_produk_list()
    keyboard = []
    for i, p in enumerate(produk_list):
        status = "✅" if p.get("kuota", 0) > 0 else "❌"
        label = f"{status} {p['nama']} | Rp {p['harga']:,}"
        callback_data = f"produk_static|{i}"
        keyboard.append([
            InlineKeyboardButton(label, callback_data=callback_data)
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
