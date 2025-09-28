# markup.py - VERSI FIX
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging

logger = logging.getLogger(__name__)

def is_admin(user_id):
    """Cek apakah user adalah admin"""
    try:
        from config import ADMIN_IDS
        return user_id in ADMIN_IDS
    except Exception as e:
        logger.error(f"Error checking admin: {e}")
        return False

def get_saldo_user_safe(user_id):
    """Ambil saldo user dengan error handling"""
    try:
        from saldo import get_saldo_user
        return get_saldo_user(user_id)
    except Exception as e:
        logger.error(f"Error getting saldo: {e}")
        return 0

def get_riwayat_saldo_safe(user_id, limit=3):
    """Ambil riwayat saldo dengan error handling"""
    try:
        from saldo import get_riwayat_saldo
        return get_riwayat_saldo(user_id, limit)
    except Exception as e:
        logger.error(f"Error getting riwayat: {e}")
        return []

def get_produk_list_safe():
    """Ambil daftar produk dengan error handling"""
    try:
        # Coba berbagai sumber produk
        try:
            from provider import list_product
            produk = list_product()
            if produk:
                return produk
        except ImportError:
            pass
        
        # Fallback ke produk static
        produk_static = [
            {"nama": "BPAL19", "harga": 19000, "kuota": 10, "kode": "BPAL19"},
            {"nama": "BPAL25", "harga": 25000, "kuota": 10, "kode": "BPAL25"},
            {"nama": "BPAL50", "harga": 50000, "kuota": 10, "kode": "BPAL50"},
            {"nama": "BPAL100", "harga": 100000, "kuota": 10, "kode": "BPAL100"},
        ]
        return produk_static
        
    except Exception as e:
        logger.error(f"Error getting produk list: {e}")
        return []

def menu_user(user_id):
    """Menu untuk user regular"""
    try:
        # Info user: ID, saldo, riwayat transaksi
        info_text = f"🆔 <b>ID User:</b> <code>{user_id}</code>\n"
        
        saldo = get_saldo_user_safe(user_id)
        info_text += f"💰 <b>Saldo:</b> Rp {saldo:,}\n"
        
        riwayat = get_riwayat_saldo_safe(user_id, limit=3)
        if riwayat:
            info_text += "📄 <b>Riwayat Terakhir:</b>\n"
            for i, trx in enumerate(riwayat[:3], 1):
                tipe, jumlah, keterangan, tanggal = trx
                status = "💰" if jumlah > 0 else "💸"
                info_text += f"{i}. {status} {tipe}: Rp {jumlah:+,}\n"
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
        
        # Cek apakah topup tersedia
        try:
            from handlers.topup_handler import topup_callback
        except ImportError:
            # Hapus tombol topup jika tidak tersedia
            keyboard[1] = [InlineKeyboardButton("🔍 Cek Status", callback_data='cek_status')]
        
        return info_text, InlineKeyboardMarkup(keyboard)
        
    except Exception as e:
        logger.error(f"Error creating user menu: {e}")
        # Fallback menu
        keyboard = [
            [InlineKeyboardButton("📦 Lihat Produk", callback_data='lihat_produk')],
            [InlineKeyboardButton("🛒 Beli Produk", callback_data='beli_produk')],
            [InlineKeyboardButton("🔄 Restart", callback_data='start')]
        ]
        return "🤖 <b>AMIFI BOT</b>\n\nPilih menu di bawah:", InlineKeyboardMarkup(keyboard)

def menu_admin(user_id):
    """Menu untuk admin"""
    try:
        info_text = f"🆔 <b>ID Admin:</b> <code>{user_id}</code>\n"
        
        saldo = get_saldo_user_safe(user_id)
        info_text += f"💰 <b>Saldo:</b> Rp {saldo:,}\n"
        
        riwayat = get_riwayat_saldo_safe(user_id, limit=3)
        if riwayat:
            info_text += "📄 <b>Riwayat Terakhir:</b>\n"
            for i, trx in enumerate(riwayat[:3], 1):
                tipe, jumlah, keterangan, tanggal = trx
                status = "💰" if jumlah > 0 else "💸"
                info_text += f"{i}. {status} {tipe}: Rp {jumlah:+,}\n"
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
                InlineKeyboardButton("💰 Lihat Saldo", callback_data='lihat_saldo'),
                InlineKeyboardButton("➕ Tambah Saldo", callback_data='tambah_saldo')
            ],
        ]
        
        # Tambah menu admin khusus jika tersedia
        try:
            from handlers.admin_produk_handler import admin_edit_produk_callback
            keyboard.append([
                InlineKeyboardButton("📝 Manage Produk", callback_data='manajemen_produk'),
                InlineKeyboardButton("🗃️ Semua Riwayat", callback_data='semua_riwayat')
            ])
        except ImportError:
            pass
            
        # Cek apakah topup admin tersedia
        try:
            from handlers.topup_handler import admin_topup_list_callback
            keyboard.append([InlineKeyboardButton("💳 Approve Topup", callback_data='riwayat_topup_admin')])
        except ImportError:
            pass

        return info_text, InlineKeyboardMarkup(keyboard)
        
    except Exception as e:
        logger.error(f"Error creating admin menu: {e}")
        # Fallback menu admin
        keyboard = [
            [InlineKeyboardButton("📦 Produk", callback_data='lihat_produk')],
            [InlineKeyboardButton("🛒 Beli", callback_data='beli_produk')],
            [InlineKeyboardButton("📝 Manage Produk", callback_data='manajemen_produk')],
            [InlineKeyboardButton("🔄 Restart", callback_data='start')]
        ]
        return "👑 <b>ADMIN PANEL</b>\n\nPilih menu di bawah:", InlineKeyboardMarkup(keyboard)

def get_menu(user_id):
    """Dapatkan menu berdasarkan user role"""
    try:
        if is_admin(user_id):
            return menu_admin(user_id)
        else:
            return menu_user(user_id)
    except Exception as e:
        logger.error(f"Error in get_menu: {e}")
        # Ultimate fallback
        keyboard = [[InlineKeyboardButton("🔄 Restart", callback_data="start")]]
        return "🤖 <b>AMIFI BOT</b>\n\nTerjadi error. Silakan restart.", InlineKeyboardMarkup(keyboard)

def produk_inline_keyboard():
    """Keyboard untuk daftar produk"""
    try:
        produk_list = get_produk_list_safe()
        keyboard = []
        
        for i, p in enumerate(produk_list):
            status = "✅" if p.get("kuota", 0) > 0 else "❌"
            # Pastikan harga adalah integer untuk formatting
            harga = p.get('harga', 0)
            if isinstance(harga, str):
                try:
                    harga = int(harga)
                except ValueError:
                    harga = 0
                    
            label = f"{status} {p['nama']} | Rp {harga:,}"
            callback_data = f"produk_static|{i}"
            keyboard.append([
                InlineKeyboardButton(label, callback_data=callback_data)
            ])
            
        keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")])
        return InlineKeyboardMarkup(keyboard)
        
    except Exception as e:
        logger.error(f"Error creating produk keyboard: {e}")
        # Fallback keyboard
        keyboard = [
            [InlineKeyboardButton("❌ Error loading products", callback_data="none")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)

def admin_edit_produk_keyboard(kode):
    """Keyboard untuk edit produk (admin)"""
    try:
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
    except Exception as e:
        logger.error(f"Error creating admin edit keyboard: {e}")
        return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="back_admin")]])
