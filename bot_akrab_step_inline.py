import os
import json
import uuid
import base64
import logging
import sqlite3
import time
import threading
import random
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, InputMediaPhoto
)
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler, CallbackContext,
)
import requests

# Setup logging
LOG_FILE = 'bot_error.log'
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Pemeriksaan konfigurasi saat startup ---
try:
    with open("config.json") as f:
        cfg = json.load(f)
    TOKEN = cfg["TOKEN"]
    ADMIN_IDS = [int(i) for i in cfg["ADMIN_IDS"]]
    BASE_URL = cfg["BASE_URL"]
    API_KEY = cfg["API_KEY"]
    QRIS_STATIS = cfg["QRIS_STATIS"]
    API_PRODUK_URL = cfg.get("API_PRODUK_URL", "https://panel.khfy-store.com/api_v3/cek_stock_akrab")
except FileNotFoundError:
    print("FATAL: File config.json tidak ditemukan. Harap buat file konfigurasi sesuai contoh.")
    exit()
except (KeyError, TypeError) as e:
    print(f"FATAL: Kunci '{e}' tidak ditemukan atau formatnya salah di config.json.")
    exit()

# Cache untuk data produk
produk_cache = {"data": [], "last_updated": 0, "update_in_progress": False}
CACHE_DURATION = 300

# --- Database setup & Functions ---
DBNAME = "botdata.db"

def get_conn():
    return sqlite3.connect(DBNAME, check_same_thread=False)

def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, nama TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS saldo (user_id INTEGER PRIMARY KEY, saldo INTEGER DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS riwayat_transaksi (id TEXT PRIMARY KEY, user_id INTEGER, produk TEXT, tujuan TEXT, harga INTEGER, waktu TEXT, status_text TEXT, keterangan TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS topup_pending (id TEXT PRIMARY KEY, user_id INTEGER, username TEXT, nama TEXT, nominal INTEGER, waktu TEXT, status TEXT, bukti_file_id TEXT, bukti_caption TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS produk_admin (kode TEXT PRIMARY KEY, harga INTEGER, deskripsi TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS kode_unik_topup (kode TEXT PRIMARY KEY, user_id INTEGER, nominal INTEGER, digunakan INTEGER DEFAULT 0, dibuat_pada TEXT, digunakan_pada TEXT)""")
        conn.commit()

def db_query(query, params=(), fetchone=False, fetchall=False):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetchone: return cursor.fetchone()
        if fetchall: return cursor.fetchall()
        conn.commit()

def tambah_user(user_id, username, nama):
    db_query("INSERT OR IGNORE INTO users (id, username, nama) VALUES (?, ?, ?)", (user_id, username, nama))
    db_query("INSERT OR IGNORE INTO saldo (user_id, saldo) VALUES (?, 0)", (user_id,))

def get_saldo(user_id):
    result = db_query("SELECT saldo FROM saldo WHERE user_id=?", (user_id,), fetchone=True)
    return result[0] if result else 0

def tambah_saldo(user_id, amount):
    db_query("INSERT OR IGNORE INTO saldo(user_id, saldo) VALUES (?,0)", (user_id,))
    db_query("UPDATE saldo SET saldo=saldo+? WHERE user_id=?", (amount, user_id))

def kurang_saldo(user_id, amount):
    db_query("UPDATE saldo SET saldo=saldo-? WHERE user_id=?", (amount, user_id))

def log_riwayat(id, user_id, produk, tujuan, harga, waktu, status_text, keterangan):
    db_query("INSERT OR REPLACE INTO riwayat_transaksi (id, user_id, produk, tujuan, harga, waktu, status_text, keterangan) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (id, user_id, produk, tujuan, harga, waktu, status_text, keterangan))

def get_user(user_id):
    return db_query("SELECT id, username, nama FROM users WHERE id=?", (user_id,), fetchone=True)
    
def get_all_users():
    return db_query("SELECT id, username, nama FROM users", fetchall=True)

def get_riwayat_jml(user_id):
    result = db_query("SELECT COUNT(*) FROM riwayat_transaksi WHERE user_id=?", (user_id,), fetchone=True)
    return result[0] if result else 0

def get_riwayat_user(user_id, limit=10):
    return db_query("SELECT * FROM riwayat_transaksi WHERE user_id=? ORDER BY waktu DESC LIMIT ?", (user_id, limit), fetchall=True)
        
def get_all_riwayat(limit=20):
    return db_query("SELECT * FROM riwayat_transaksi ORDER BY waktu DESC LIMIT ?", (limit,), fetchall=True)

def insert_topup_pending(id, user_id, username, nama, nominal, waktu, status):
    db_query("INSERT INTO topup_pending (id, user_id, username, nama, nominal, waktu, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
             (id, user_id, username, nama, nominal, waktu, status))

def update_topup_bukti(id, file_id, caption):
    db_query("UPDATE topup_pending SET bukti_file_id=?, bukti_caption=? WHERE id=?", (file_id, caption, id))

def update_topup_status(id, status):
    db_query("UPDATE topup_pending SET status=? WHERE id=?", (status, id))

def get_topup_pending_by_user(user_id, limit=10):
    return db_query("SELECT * FROM topup_pending WHERE user_id=? ORDER BY waktu DESC LIMIT ?", (user_id, limit), fetchall=True)

def get_topup_pending_all(limit=10):
    return db_query("SELECT * FROM topup_pending WHERE status='pending' ORDER BY waktu DESC LIMIT ?", (limit,), fetchall=True)

def get_topup_by_id(id):
    return db_query("SELECT * FROM topup_pending WHERE id=?", (id,), fetchone=True)

def get_produk_admin(kode):
    row = db_query("SELECT harga, deskripsi FROM produk_admin WHERE kode=?", (kode,), fetchone=True)
    if row: return {"harga": row[0], "deskripsi": row[1]}
    return None

def get_all_produk_admin():
    rows = db_query("SELECT kode, harga, deskripsi FROM produk_admin", fetchall=True)
    return {row[0]: {"harga": row[1], "deskripsi": row[2]} for row in rows}

def set_produk_admin_harga(kode, harga):
    db_query("INSERT OR IGNORE INTO produk_admin (kode, harga, deskripsi) VALUES (?, ?, '')", (kode, harga))
    db_query("UPDATE produk_admin SET harga=? WHERE kode=?", (harga, kode))

def set_produk_admin_deskripsi(kode, deskripsi):
    db_query("INSERT OR IGNORE INTO produk_admin (kode, harga, deskripsi) VALUES (?, 0, ?)", (kode, deskripsi))
    db_query("UPDATE produk_admin SET deskripsi=? WHERE kode=?", (deskripsi, kode))

def simpan_kode_unik(kode, user_id, nominal):
    db_query("INSERT INTO kode_unik_topup (kode, user_id, nominal, digunakan, dibuat_pada) VALUES (?, ?, ?, 0, ?)",
             (kode, user_id, nominal, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

def get_kode_unik(kode):
    row = db_query("SELECT kode, user_id, nominal, digunakan FROM kode_unik_topup WHERE kode=?", (kode,), fetchone=True)
    if row: return {"kode": row[0], "user_id": row[1], "nominal": row[2], "digunakan": row[3]}
    return None

def gunakan_kode_unik(kode):
    db_query("UPDATE kode_unik_topup SET digunakan=1, digunakan_pada=? WHERE kode=?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), kode))

def get_kode_unik_user(user_id, limit=5):
    rows = db_query("SELECT kode, nominal, digunakan, dibuat_pada FROM kode_unik_topup WHERE user_id=? ORDER BY dibuat_pada DESC LIMIT ?", (user_id, limit), fetchall=True)
    return [{"kode": r[0], "nominal": r[1], "digunakan": r[2], "dibuat_pada": r[3]} for r in rows]

# --- Helper Functions ---
def update_produk_cache_background():
    if produk_cache["update_in_progress"]: return
    produk_cache["update_in_progress"] = True
    try:
        res = requests.get(API_PRODUK_URL, timeout=10)
        res.raise_for_status()
        data = res.json()
        if isinstance(data.get("data"), list):
            produk_cache["data"] = data["data"]
            produk_cache["last_updated"] = time.time()
            logger.info(f"Cache produk diperbarui: {len(data['data'])} produk.")
        else:
            logger.error("Format data stok tidak dikenali dari API.")
    except Exception as e:
        logger.error(f"Gagal memperbarui cache produk: {e}")
    finally:
        produk_cache["update_in_progress"] = False

def get_harga_produk(kode):
    admin_data = get_produk_admin(kode)
    if admin_data and admin_data.get("harga", 0) > 0:
        return admin_data["harga"]
    
    try:
        if produk_cache["data"]:
            for produk in produk_cache["data"]:
                if produk["type"] == kode:
                    return int(produk.get("harga", 0))
    except Exception:
        pass
    return 0

def get_produk_info(kode):
    harga = get_harga_produk(kode)
    nama = "Produk Tidak Dikenal"
    try:
        if produk_cache["data"]:
            for produk in produk_cache["data"]:
                if produk["type"] == kode:
                    nama = produk.get("nama", "Produk")
                    break
    except Exception:
        pass
    return nama, harga

def generate_kode_unik():
    return str(random.randint(100, 999))

# --- States ---
(CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, 
 BC_MESSAGE, TOPUP_AMOUNT, TOPUP_UPLOAD, 
 ADMIN_EDIT_HARGA, ADMIN_EDIT_DESKRIPSI, 
 USER_INPUT_KODE_UNIK, ADMIN_GENERATE_KODE_NOMINAL) = range(10)

# --- UI Components ---
def btn_kembali(callback_data="main_menu"): 
    return InlineKeyboardButton("🔙 Kembali", callback_data=callback_data)

def get_menu(uid):
    base_menu = [
        [InlineKeyboardButton("🛒 Beli Produk", callback_data='beli_produk'),
         InlineKeyboardButton("💳 Top Up Saldo", callback_data='topup_menu')],
        [InlineKeyboardButton("📋 Riwayat Transaksi", callback_data='riwayat'),
         InlineKeyboardButton("📦 Info Stok", callback_data='cek_stok')],
        [InlineKeyboardButton("🧾 Riwayat Top Up", callback_data="topup_riwayat"),
         InlineKeyboardButton("🔑 Kode Unik Saya", callback_data="my_kode_unik")],
    ]
    if uid in ADMIN_IDS:
        base_menu.insert(2, [InlineKeyboardButton("👑 Admin Panel", callback_data='admin_panel')])
    base_menu.append([InlineKeyboardButton("ℹ️ Bantuan", callback_data="bantuan")])
    return InlineKeyboardMarkup(base_menu)

def admin_panel_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Data User", callback_data='admin_cekuser'),
         InlineKeyboardButton("📊 Semua Riwayat", callback_data='semua_riwayat')],
        [InlineKeyboardButton("📢 Broadcast Pesan", callback_data='broadcast'),
         InlineKeyboardButton("⚙️ Manajemen Produk", callback_data="admin_produk")],
        [InlineKeyboardButton("✅ Approve Top Up", callback_data="admin_topup_pending")],
        [InlineKeyboardButton("🔑 Generate Kode Unik", callback_data="admin_generate_kode")],
        [btn_kembali()]
    ])
    
def topup_menu_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 QRIS (Otomatis)", callback_data="topup_qris")],
        [InlineKeyboardButton("🔑 Kode Unik (Manual)", callback_data="topup_kode_unik")],
        [btn_kembali()]
    ])
    
def produk_inline_keyboard(is_admin=False):
    try:
        data_list = produk_cache.get("data", [])
        keyboard = []
        
        if not data_list:
            return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Tidak ada produk", callback_data="noop")], [btn_kembali()]])
        
        admin_produk = get_all_produk_admin()
        processed_codes = set()
        
        for produk in data_list:
            kode = produk['type']
            processed_codes.add(kode)
            nama = produk['nama']
            slot = int(produk.get('sisa_slot', 0))
            harga = get_harga_produk(kode)
            
            if is_admin:
                status = "✅" if slot > 0 else "❌"
                label = f"{status} [{kode}] {nama} | Rp{harga:,}"
                keyboard.append([InlineKeyboardButton(label, callback_data=f"admin_produk_detail|{kode}")])
            elif slot > 0:
                label = f"✅ [{kode}] {nama} | Rp{harga:,}"
                keyboard.append([InlineKeyboardButton(label, callback_data=f"produk|{kode}|{nama}")])
        
        if is_admin:
            for kode, info in admin_produk.items():
                if kode not in processed_codes:
                    label = f"⚠️ [{kode}] (Tidak di API) | Rp{info['harga']:,}"
                    keyboard.append([InlineKeyboardButton(label, callback_data=f"admin_produk_detail|{kode}")])
        
        if not keyboard:
            keyboard.append([InlineKeyboardButton("❌ Semua produk habis", callback_data="noop")])
        
        keyboard.append([btn_kembali()])
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logger.error(f"Error loading products: {e}")
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Gagal memuat", callback_data="beli_produk")], [btn_kembali()]])

# --- CORE BOT HANDLERS ---
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    tambah_user(user.id, user.username or "", user.full_name)
    update.message.reply_text(
        dashboard_msg(user),
        parse_mode=ParseMode.HTML,
        reply_markup=get_menu(user.id)
    )
    if context.user_data: context.user_data.clear()
    return ConversationHandler.END

def main_menu_callback(update: Update, context: CallbackContext):
    user = update.effective_user
    query = update.callback_query
    msg = dashboard_msg(user)
    markup = get_menu(user.id)
    
    if query:
        query.answer()
        try: query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)
        except Exception: pass
    else:
        context.bot.send_message(chat_id=user.id, text=msg, parse_mode=ParseMode.HTML, reply_markup=markup)
    
    if context.user_data: context.user_data.clear()
    return ConversationHandler.END

def batal(update: Update, context: CallbackContext):
    user = update.effective_user
    logger.info(f"User {user.id} membatalkan percakapan.")
    
    message_text = "Aksi dibatalkan."
    if update.message:
        update.message.reply_text(message_text)
    elif update.callback_query:
        # Hapus tombol dari pesan sebelumnya jika memungkinkan
        try: update.callback_query.edit_message_reply_markup(None)
        except Exception: pass
        update.callback_query.answer(message_text)

    main_menu_callback(update, context)
    return ConversationHandler.END

def dashboard_msg(user):
    saldo = get_saldo(user.id)
    total_trx = get_riwayat_jml(user.id)
    return (
        f"✨ <b>DASHBOARD ANDA</b> ✨\n\n"
        f"👤 <b>Nama:</b> {user.full_name}\n"
        f"📧 <b>Username:</b> @{user.username or 'Tidak ada'}\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n\n"
        f"💰 <b>Saldo:</b> <code>Rp {saldo:,}</code>\n"
        f"📊 <b>Total Transaksi:</b> <b>{total_trx}</b>\n\n"
        "Silakan pilih menu di bawah ini:"
    )

def cek_stok_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data_list = produk_cache.get("data", [])
    
    msg = "📦 <b>Info Stok Akrab XL/Axis</b>\n\n"
    if not data_list:
        msg += "❌ Gagal mengambil data stok saat ini."
    else:
        for produk in data_list:
            status = "✅" if int(produk.get('sisa_slot', 0)) > 0 else "❌"
            msg += f"{status} <b>[{produk['type']}]</b> {produk['nama']}: {produk.get('sisa_slot', 'N/A')} unit\n"
    
    query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[btn_kembali()]]))

def riwayat_user(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    items = get_riwayat_user(query.from_user.id)
    msg = "📋 <b>RIWAYAT TRANSAKSI ANDA (10 terbaru)</b>\n\n"
    if not items:
        msg += "Anda belum memiliki riwayat transaksi."
    else:
        for r in items:
            status = r[6].upper()
            emoji = "✅" if "SUKSES" in status else ("❌" if "GAGAL" in status else "⏳")
            msg += (f"{emoji} <b>{r[5]}</b>\nID: <code>{r[0]}</code>\nProduk: [{r[2]}] ke {r[3]}\n"
                    f"Harga: Rp {r[4]:,}\nStatus: <b>{status}</b>\n\n")
    query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[btn_kembali()]]))

def topup_riwayat_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    items = get_topup_pending_by_user(update.effective_user.id)
    msg = "🧾 <b>RIWAYAT TOP UP ANDA (10 terbaru)</b>\n\n"
    if not items:
        msg += "Anda belum pernah melakukan permintaan top up."
    else:
        status_map = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
        for r in items:
            emoji = status_map.get(r[6], "❓")
            msg += (f"{emoji} <b>{r[5]}</b>\nID: <code>{r[0]}</code>\nNominal: Rp {r[4]:,}\nStatus: <b>{r[6].capitalize()}</b>\n\n")
            
    query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[btn_kembali()]]))

def my_kode_unik_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    items = get_kode_unik_user(update.effective_user.id)
    msg = "🔑 <b>KODE UNIK SAYA (5 terbaru)</b>\n\n"
    if not items:
        msg += "Belum ada kode unik yang dibuat untuk Anda."
    else:
        for kode in items:
            status = "✅ Digunakan" if kode["digunakan"] else "⏳ Belum digunakan"
            msg += (f"Kode: <code>{kode['kode']}</code> | Nominal: <b>Rp {kode['nominal']:,}</b>\nStatus: {status}\n\n")
    query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[btn_kembali()]]))

def bantuan_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    msg = (
        "❓ <b>PUSAT BANTUAN</b>\n\n"
        "Gunakan tombol di menu utama untuk navigasi.\n\n"
        "🛒 <b>Beli Produk</b>: Untuk membeli produk yang tersedia.\n"
        "💳 <b>Top Up Saldo</b>: Untuk menambah saldo melalui QRIS atau Kode Unik.\n"
        "📋 <b>Riwayat</b>: Melihat riwayat transaksi dan top up.\n"
        "📦 <b>Info Stok</b>: Cek ketersediaan produk.\n\n"
        "📞 Jika ada kendala, hubungi admin."
    )
    query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[btn_kembali()]]))
    
# --- ALUR BELI PRODUK (DENGAN PERBAIKAN) ---
def beli_produk_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    keyboard = produk_inline_keyboard()
    query.edit_message_text(
        "🛒 <b>PILIH PRODUK</b>\n\nPilih produk yang ingin dibeli:",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
    return CHOOSING_PRODUK

def pilih_produk_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.user_data['pilihan_produk'] = query.data
    
    query.edit_message_text(
        "📱 <b>Masukkan nomor tujuan Anda:</b>\n\nKetik /batal untuk membatalkan.",
        parse_mode=ParseMode.HTML
    )
    return INPUT_TUJUAN

def input_tujuan_step(update: Update, context: CallbackContext):
    tujuan = update.message.text.strip()
    if not tujuan.isdigit() or len(tujuan) < 8:
        update.message.reply_text("❌ Nomor tujuan tidak valid. Ulangi, atau ketik /batal.")
        return INPUT_TUJUAN
    
    try:
        pilihan_produk_data = context.user_data['pilihan_produk']
        _, kode, nama = pilihan_produk_data.split("|")
        harga = get_harga_produk(kode)

        callback_data_confirm = f"confirm_trx|{kode}|{tujuan}"
        
        update.message.reply_text(
            f"✨ <b>KONFIRMASI AKHIR</b> ✨\n\n"
            f"📦 Produk: [{kode}] {nama}\n"
            f"💰 Harga: Rp {harga:,}\n"
            f"📱 Tujuan: <code>{tujuan}</code>\n\n"
            "Apakah data sudah benar?",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Ya, Konfirmasi", callback_data=callback_data_confirm)],
                [InlineKeyboardButton("❌ Batal", callback_data="main_menu")]
            ])
        )
        return KONFIRMASI
    except Exception as e:
        logger.error(f"Error di input_tujuan_step: {e}")
        update.message.reply_text("❌ Sesi berakhir. Silakan ulangi dari awal.")
        return ConversationHandler.END

def konfirmasi_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user = query.from_user

    try:
        _, kode_produk, tujuan = query.data.split("|")
    except (ValueError, IndexError):
        query.edit_message_text("❌ Error: Tombol tidak valid. Silakan ulangi.", reply_markup=get_menu(user.id))
        return ConversationHandler.END

    nama_produk, harga = get_produk_info(kode_produk)

    if harga <= 0:
        query.edit_message_text("❌ Gagal mendapatkan harga produk. Transaksi dibatalkan.", reply_markup=get_menu(user.id))
        return ConversationHandler.END

    saldo = get_saldo(user.id)
    if saldo < harga:
        query.edit_message_text(f"❌ Saldo Anda tidak cukup (Rp {saldo:,}).", reply_markup=get_menu(user.id))
        return ConversationHandler.END
        
    query.edit_message_text("⏳ Memproses transaksi, mohon tunggu...")
    
    reffid = str(uuid.uuid4())
    url = f"{BASE_URL}trx?produk={kode_produk}&tujuan={tujuan}&reff_id={reffid}&api_key={API_KEY}"
    
    try:
        res = requests.get(url, timeout=25)
        res.raise_for_status()
        data = res.json()
        if not isinstance(data, dict) or not data.get("refid"): raise ValueError("Respons API tidak valid.")
    except Exception as e:
        logger.error(f"Transaksi GAGAL user {user.id}. URL: {url}. Error: {e}")
        log_riwayat(reffid, user.id, kode_produk, tujuan, harga, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "GAGAL", str(e))
        query.edit_message_text("❌ <b>TRANSAKSI GAGAL</b>\n\nPesan: Gangguan pada provider. Hubungi admin.", parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
        return ConversationHandler.END

    status_text = data.get('status', 'PENDING').strip()
    pesan_provider = data.get("message", "-")
    
    if "gagal" not in status_text.lower():
        kurang_saldo(user.id, harga)
        emoji = "✅" if "sukses" in status_text.lower() else "⏳"
    else:
        emoji = "❌"
    
    saldo_now = get_saldo(user.id)
    log_riwayat(reffid, user.id, kode_produk, tujuan, harga, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status_text, pesan_provider)
    
    query.edit_message_text(
        f"{emoji} <b>STATUS TRANSAKSI</b>\n\n📦 Produk: [{kode_produk}] {nama_produk}\n📱 Tujuan: <code>{tujuan}</code>\n🔖 RefID: <code>{reffid}</code>\n📊 Status: <b>{status_text.upper()}</b>\n💬 Pesan: {pesan_provider}\n\n💰 Sisa Saldo: Rp {saldo_now:,}",
        parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id)
    )
    context.user_data.clear()
    return ConversationHandler.END

# --- Alur Top Up ---
# (Fungsi-fungsi Top Up diletakkan di sini)

# --- Alur Admin ---
# (Fungsi-fungsi Admin diletakkan di sini)


# --- MAIN FUNCTION ---
def main():
    init_db()
    threading.Thread(target=update_produk_cache_background, daemon=True).start()
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(beli_produk_menu, pattern="^beli_produk$"),
            # Tambahkan entry points untuk alur lain (top up, admin) di sini
        ],
        states={
            CHOOSING_PRODUK: [CallbackQueryHandler(pilih_produk_callback, pattern="^produk\\|")],
            INPUT_TUJUAN: [MessageHandler(Filters.text & ~Filters.command, input_tujuan_step)],
            KONFIRMASI: [CallbackQueryHandler(konfirmasi_callback, pattern="^confirm_trx\\|")],
            # Tambahkan state untuk alur lain di sini
        },
        fallbacks=[
            CommandHandler('batal', batal),
            CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"),
            CommandHandler('start', start)
        ],
        per_message=False # Penting untuk alur message -> callback
    )
    
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('menu', main_menu_callback))
    dp.add_handler(CommandHandler('batal', batal))
    dp.add_handler(conv_handler)
    
    # Handler untuk tombol single-click di luar percakapan
    def simple_callback_router(update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        data = query.data
        
        # Panggil fungsi yang sesuai berdasarkan data callback
        if data == "cek_stok": cek_stok_menu(update, context)
        elif data == "riwayat": riwayat_user(update, context)
        elif data == "topup_riwayat": topup_riwayat_menu(update, context)
        elif data == "my_kode_unik": my_kode_unik_menu(update, context)
        elif data == "bantuan": bantuan_menu(update, context)
        # Tambahkan callback admin jika diperlukan
        elif data == "admin_panel" and query.from_user.id in ADMIN_IDS: admin_panel(update, context)

    dp.add_handler(CallbackQueryHandler(simple_callback_router))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, lambda u,c: u.message.reply_text("Perintah tidak dikenali.")))

    logger.info("Bot started...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
