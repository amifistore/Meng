import os
import json
import random
import logging

logger = logging.getLogger(__name__)

SALDO_FILE = 'saldo.json'
RIWAYAT_FILE = 'riwayat_transaksi.json'
HARGA_PRODUK_FILE = 'harga_produk.json'
TOPUP_FILE = 'topup_user.json'

def load_json(filename, fallback=None):
    """Load JSON file dengan error handling yang lebih baik"""
    if fallback is None:
        fallback = {}
    
    if not os.path.exists(filename):
        return fallback
        
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # PERBAIKAN: Pastikan semua keys adalah string
            if isinstance(data, dict):
                return {str(k): v for k, v in data.items()}
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {filename}: {e}")
        return fallback
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
        return fallback

def save_json(filename, data):
    """Save JSON file dengan ensure_ascii=False dan error handling"""
    try:
        # PERBAIKAN: Pastikan semua keys adalah string sebelum menyimpan
        if isinstance(data, dict):
            data = {str(k): v for k, v in data.items()}
            
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving {filename}: {e}")
        return False

# Saldo management per-user
def get_user_saldo(user_id):
    """Get user saldo dengan konversi user_id ke string"""
    saldo_data = load_json(SALDO_FILE, {})
    user_id_str = str(user_id)
    return int(saldo_data.get(user_id_str, 0))

def set_user_saldo(user_id, amount):
    """Set user saldo dengan konversi user_id ke string"""
    saldo_data = load_json(SALDO_FILE, {})
    user_id_str = str(user_id)
    saldo_data[user_id_str] = int(amount)
    return save_json(SALDO_FILE, saldo_data)

def tambah_user_saldo(user_id, amount):
    """Tambah saldo user dengan konversi user_id ke string"""
    saldo_data = load_json(SALDO_FILE, {})
    user_id_str = str(user_id)
    current_saldo = int(saldo_data.get(user_id_str, 0))
    saldo_data[user_id_str] = current_saldo + int(amount)
    return save_json(SALDO_FILE, saldo_data)

def kurangi_saldo_user(user_id, amount):
    """Kurangi saldo user dengan konversi user_id ke string"""
    saldo_data = load_json(SALDO_FILE, {})
    user_id_str = str(user_id)
    current_saldo = int(saldo_data.get(user_id_str, 0))
    saldo_data[user_id_str] = max(0, current_saldo - int(amount))
    return save_json(SALDO_FILE, saldo_data)

def get_all_saldo():
    """Get semua saldo dengan keys yang sudah string"""
    return load_json(SALDO_FILE, {})

# Riwayat transaksi per-user
def load_riwayat(user_id=None):
    """Load riwayat transaksi dengan konversi user_id ke string"""
    riwayat = load_json(RIWAYAT_FILE, {})
    if user_id:
        user_id_str = str(user_id)
        return riwayat.get(user_id_str, [])
    return riwayat

def save_riwayat(user_id, riwayat_user):
    """Save riwayat transaksi dengan konversi user_id ke string"""
    riwayat = load_json(RIWAYAT_FILE, {})
    user_id_str = str(user_id)
    riwayat[user_id_str] = riwayat_user
    return save_json(RIWAYAT_FILE, riwayat)

def tambah_riwayat(user_id, transaksi):
    """Tambah riwayat transaksi dengan konversi user_id ke string"""
    riwayat = load_json(RIWAYAT_FILE, {})
    user_id_str = str(user_id)
    user_riwayat = riwayat.get(user_id_str, [])
    
    # PERBAIKAN: Pastikan transaksi memiliki timestamp jika belum ada
    if not any(key in transaksi for key in ['timestamp', 'waktu', 'time']):
        from datetime import datetime
        transaksi['timestamp'] = datetime.now().isoformat()
    
    user_riwayat.append(transaksi)
    riwayat[user_id_str] = user_riwayat
    return save_json(RIWAYAT_FILE, riwayat)

# Harga produk
def load_harga_produk():
    """Load harga produk dengan keys yang sudah string"""
    return load_json(HARGA_PRODUK_FILE, {})

def save_harga_produk(harga_produk):
    """Save harga produk dengan keys yang sudah string"""
    return save_json(HARGA_PRODUK_FILE, harga_produk)

def get_harga_produk(kode_produk):
    """Get harga produk dengan konversi kode_produk ke string"""
    harga_produk = load_json(HARGA_PRODUK_FILE, {})
    kode_produk_str = str(kode_produk)
    return int(harga_produk.get(kode_produk_str, 0))

def set_harga_produk(kode_produk, harga):
    """Set harga produk dengan konversi kode_produk ke string"""
    harga_produk = load_json(HARGA_PRODUK_FILE, {})
    kode_produk_str = str(kode_produk)
    harga_produk[kode_produk_str] = int(harga)
    return save_json(HARGA_PRODUK_FILE, harga_produk)

# Top up (per user)
def load_topup(user_id=None):
    """Load data topup dengan konversi user_id ke string"""
    topup = load_json(TOPUP_FILE, {})
    if user_id:
        user_id_str = str(user_id)
        return topup.get(user_id_str, [])
    return topup

def save_topup(user_id, topup_list):
    """Save data topup dengan konversi user_id ke string"""
    topup = load_json(TOPUP_FILE, {})
    user_id_str = str(user_id)
    topup[user_id_str] = topup_list
    return save_json(TOPUP_FILE, topup)

def tambah_topup(user_id, topup_data):
    """Tambah data topup dengan konversi user_id ke string"""
    topup = load_json(TOPUP_FILE, {})
    user_id_str = str(user_id)
    user_topup = topup.get(user_id_str, [])
    
    # PERBAIKAN: Tambahkan timestamp jika belum ada
    if not any(key in topup_data for key in ['timestamp', 'waktu', 'time']):
        from datetime import datetime
        topup_data['timestamp'] = datetime.now().isoformat()
    
    user_topup.append(topup_data)
    topup[user_id_str] = user_topup
    return save_json(TOPUP_FILE, topup)

# Format stok dari provider
def format_stock_akrab(json_data):
    """Format stok produk dengan error handling yang lebih baik"""
    if not json_data or (isinstance(json_data, str) and not json_data.strip()):
        return "<b>❌ Gagal mengambil data stok dari provider.</b>\nSilakan cek koneksi/API provider."
    
    try:
        # Parse JSON jika masih string
        if isinstance(json_data, str):
            import json as json_lib
            data = json_lib.loads(json_data)
        else:
            data = json_data
            
        items = data.get("data", [])
        if not items:
            return "<b>Stok kosong atau tidak ditemukan.</b>"
            
        msg = "<b>📊 Cek Stok Produk Akrab:</b>\n\n"
        msg += "<b>Kode      | Nama                | Sisa Slot</b>\n"
        msg += "<pre>"
        
        for item in items:
            # PERBAIKAN: Handle missing keys dengan aman
            kode = str(item.get('type', 'N/A')).ljust(8)
            nama = str(item.get('nama', 'N/A')).ljust(20)
            slot = str(item.get('sisa_slot', 0)).rjust(4)
            msg += f"{kode} | {nama} | {slot}\n"
            
        msg += "</pre>"
        return msg
        
    except Exception as e:
        logger.error(f"Error formatting stock: {e}")
        return f"<b>❌ Error memproses data stok:</b>\n<pre>{str(e)}</pre>"

# Nominal unik untuk topup
def get_nominal_unik(nominal, min_unik=1, max_unik=99):
    """
    Generate nominal unik untuk top up (nominal + angka unik random 1-99)
    Return: total_nominal, kode_unik
    """
    try:
        nominal_int = int(nominal)
        kode_unik = random.randint(min_unik, max_unik)
        return nominal_int + kode_unik, kode_unik
    except (ValueError, TypeError):
        logger.error(f"Invalid nominal: {nominal}")
        return nominal, 0
