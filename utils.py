import os
import json
import random

SALDO_FILE = 'saldo.json'
RIWAYAT_FILE = 'riwayat_transaksi.json'
HARGA_PRODUK_FILE = 'harga_produk.json'
TOPUP_FILE = 'topup_user.json'

def load_json(filename, fallback=None):
    if os.path.exists(filename):
        try:
            with open(filename, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return fallback if fallback is not None else {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Saldo management per-user
def get_user_saldo(user_id):
    saldo_data = load_json(SALDO_FILE, {})
    return int(saldo_data.get(str(user_id), 0))

def set_user_saldo(user_id, amount):
    saldo_data = load_json(SALDO_FILE, {})
    saldo_data[str(user_id)] = int(amount)
    save_json(SALDO_FILE, saldo_data)

def tambah_user_saldo(user_id, amount):
    saldo_data = load_json(SALDO_FILE, {})
    saldo_data[str(user_id)] = int(saldo_data.get(str(user_id), 0)) + int(amount)
    save_json(SALDO_FILE, saldo_data)

def kurangi_saldo_user(user_id, amount):
    saldo_data = load_json(SALDO_FILE, {})
    saldo_data[str(user_id)] = max(0, int(saldo_data.get(str(user_id), 0)) - int(amount))
    save_json(SALDO_FILE, saldo_data)

def get_all_saldo():
    return load_json(SALDO_FILE, {})

# Riwayat transaksi per-user
def load_riwayat(user_id=None):
    riwayat = load_json(RIWAYAT_FILE, {})
    if user_id:
        return riwayat.get(str(user_id), [])
    return riwayat

def save_riwayat(user_id, riwayat_user):
    riwayat = load_json(RIWAYAT_FILE, {})
    riwayat[str(user_id)] = riwayat_user
    save_json(RIWAYAT_FILE, riwayat)

def tambah_riwayat(user_id, transaksi):
    riwayat = load_json(RIWAYAT_FILE, {})
    user_riwayat = riwayat.get(str(user_id), [])
    user_riwayat.append(transaksi)
    riwayat[str(user_id)] = user_riwayat
    save_json(RIWAYAT_FILE, riwayat)

# Harga produk
def load_harga_produk():
    return load_json(HARGA_PRODUK_FILE, {})

def save_harga_produk(harga_produk):
    save_json(HARGA_PRODUK_FILE, harga_produk)

def get_harga_produk(kode_produk):
    harga_produk = load_json(HARGA_PRODUK_FILE, {})
    return int(harga_produk.get(str(kode_produk), 0))

def set_harga_produk(kode_produk, harga):
    harga_produk = load_json(HARGA_PRODUK_FILE, {})
    harga_produk[str(kode_produk)] = int(harga)
    save_json(HARGA_PRODUK_FILE, harga_produk)

# Top up (per user)
def load_topup(user_id=None):
    topup = load_json(TOPUP_FILE, {})
    if user_id:
        return topup.get(str(user_id), [])
    return topup

def save_topup(user_id, topup_list):
    topup = load_json(TOPUP_FILE, {})
    topup[str(user_id)] = topup_list
    save_json(TOPUP_FILE, topup)

def tambah_topup(user_id, topup_data):
    topup = load_json(TOPUP_FILE, {})
    user_topup = topup.get(str(user_id), [])
    user_topup.append(topup_data)
    topup[str(user_id)] = user_topup
    save_json(TOPUP_FILE, topup)

# Format stok dari provider
def format_stock_akrab(json_data):
    import json as _json
    if not json_data or (isinstance(json_data, str) and not json_data.strip()):
        return "<b>❌ Gagal mengambil data stok dari provider.</b>\nSilakan cek koneksi/API provider."
    if isinstance(json_data, dict):
        data = json_data
    else:
        try:
            data = _json.loads(json_data)
        except Exception as e:
            return f"<b>❌ Error parsing data stok:</b>\n<pre>{e}\n{json_data}</pre>"
    items = data.get("data", [])
    if not items:
        return "<b>Stok kosong atau tidak ditemukan.</b>"
    msg = "<b>📊 Cek Stok Produk Akrab:</b>\n\n"
    msg += "<b>Kode      | Nama                | Sisa Slot</b>\n"
    msg += "<pre>"
    for item in items:
        kode = item['type'].ljust(8)
        nama = item['nama'].ljust(20)
        slot = str(item['sisa_slot']).rjust(4)
        msg += f"{kode} | {nama} | {slot}\n"
    msg += "</pre>"
    return msg

# Nominal unik untuk topup
def get_nominal_unik(nominal, min_unik=1, max_unik=99):
    """
    Generate nominal unik untuk top up (nominal + angka unik random 1-99)
    Return: total_nominal, kode_unik
    """
    kode_unik = random.randint(min_unik, max_unik)
    return nominal + kode_unik, kode_unik
