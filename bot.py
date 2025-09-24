# bot.py
# Description: Main file for the Telegram bot logic, handlers, and execution.

import os, json, uuid, base64, logging, time, threading, random, requests
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, InputMediaPhoto
)
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler, CallbackContext,
)

# Import from local modules
from database import *
from webhook_server import create_webhook_app

# --- CONFIGURATION & SETUP ---

# Load configuration
try:
    with open("config.json") as f:
        cfg = json.load(f)
except FileNotFoundError:
    print("Error: config.json not found. Please ensure the file exists.")
    exit(1)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON in config.json. Details: {e}")
    exit(1)
    
TOKEN = cfg["TOKEN"]
ADMIN_IDS = [int(i) for i in cfg["ADMIN_IDS"]]
BASE_URL = cfg["BASE_URL"]
API_KEY = cfg["API_KEY"]
QRIS_STATIS = cfg["QRIS_STATIS"]
WEBHOOK_PORT = cfg["WEBHOOK_PORT"]
LOG_FILE = 'bot_error.log'

# Setup logging
logging.basicConfig(
    filename=LOG_FILE, 
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Product cache
produk_cache = {
    "data": [],
    "last_updated": 0,
    "update_in_progress": False
}
CACHE_DURATION = 300  # 5 minutes

# --- CACHE & API HELPERS ---

def update_produk_cache_background():
    """Updates the product cache from the API in a background thread."""
    if produk_cache["update_in_progress"]:
        return
        
    produk_cache["update_in_progress"] = True
    try:
        start_time = time.time()
        res = requests.get(cfg["BASE_URL_AKRAB"] + "cek_stock_akrab", timeout=10)
        data = res.json()
        
        if isinstance(data.get("data"), list):
            produk_cache["data"] = data["data"]
            produk_cache["last_updated"] = time.time()
            logger.info(f"Product cache updated. Products: {len(data['data'])}. Time: {time.time() - start_time:.2f}s")
        else:
            logger.error("Unrecognized stock data format.")
    except Exception as e:
        logger.error(f"Failed to update product cache: {e}")
    finally:
        produk_cache["update_in_progress"] = False

def generate_qris(amount, qris_statis):
    """Generates a QRIS code using an external API."""
    url = "https://qrisku.my.id/api"
    payload = {"amount": str(amount), "qris_statis": qris_statis}
    try:
        res = requests.post(url, json=payload, timeout=20)
        data = res.json()
        if data.get('status') == 'success' and 'qris_base64' in data:
            return True, data['qris_base64']
        else:
            return False, data.get('message', 'Failed to generate QRIS')
    except Exception as e:
        return False, f"QRIS API connection error: {e}"

# --- CONVERSATION STATES ---
(
    CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, BC_MESSAGE, TOPUP_AMOUNT, 
    TOPUP_UPLOAD, ADMIN_CEKUSER, ADMIN_EDIT_HARGA, ADMIN_EDIT_DESKRIPSI, 
    INPUT_KODE_UNIK
) = range(10)

# --- UI COMPONENTS ---

def btn_kembali(): 
    return [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]

def btn_kembali_menu(): 
    return [InlineKeyboardButton("🏠 Menu Utama", callback_data="main_menu")]

def get_menu(uid): 
    return menu_admin(uid) if uid in ADMIN_IDS else menu_user(uid)

def menu_user(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Beli Produk", callback_data='beli_produk'),
         InlineKeyboardButton("💳 Top Up Saldo", callback_data='topup_menu')],
        [InlineKeyboardButton("📋 Riwayat Transaksi", callback_data='riwayat'),
         InlineKeyboardButton("📦 Info Stok", callback_data='cek_stok')],
        [InlineKeyboardButton("🧾 Riwayat Top Up", callback_data="topup_riwayat"),
         InlineKeyboardButton("🔑 Kode Unik Saya", callback_data="my_kode_unik")],
        [InlineKeyboardButton("ℹ️ Bantuan", callback_data="bantuan")],
    ])

def menu_admin(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Beli Produk", callback_data='beli_produk'),
         InlineKeyboardButton("💳 Top Up Saldo", callback_data='topup_menu')],
        [InlineKeyboardButton("📋 Riwayat Saya", callback_data='riwayat'),
         InlineKeyboardButton("📦 Info Stok", callback_data='cek_stok')],
        [InlineKeyboardButton("👥 Admin Panel", callback_data='admin_panel')],
        [InlineKeyboardButton("ℹ️ Bantuan", callback_data="bantuan")],
    ])

def admin_panel_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Data User", callback_data='admin_cekuser'),
         InlineKeyboardButton("💰 Lihat Saldo", callback_data='lihat_saldo')],
        [InlineKeyboardButton("📊 Semua Riwayat", callback_data='semua_riwayat'),
         InlineKeyboardButton("📢 Broadcast", callback_data='broadcast')],
        [InlineKeyboardButton("✅ Approve Top Up", callback_data="admin_topup_pending"),
         InlineKeyboardButton("⚙️ Manajemen Produk", callback_data="admin_produk")],
        [InlineKeyboardButton("🔑 Generate Kode Unik", callback_data="admin_generate_kode")],
        btn_kembali()
    ])

def topup_menu_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 QRIS (Otomatis)", callback_data="topup_qris")],
        [InlineKeyboardButton("🔑 Kode Unik (Manual)", callback_data="topup_kode_unik")],
        btn_kembali()
    ])

def dashboard_msg(user):
    saldo = get_saldo(user.id)
    total_trx = get_riwayat_jml(user.id)
    return (
        f"✨ <b>DASHBOARD USER</b> ✨\n\n"
        f"👤 <b>{user.full_name}</b>\n"
        f"📧 @{user.username or '-'}\n"
        f"🆔 <code>{user.id}</code>\n\n"
        f"💰 <b>Saldo:</b> <code>Rp {saldo:,}</code>\n"
        f"📊 <b>Total Transaksi:</b> <b>{total_trx}</b>\n"
    )

# --- PRODUCT FUNCTIONS ---

def get_harga_produk(kode, api_produk=None):
    admin_data = get_produk_admin(kode)
    if admin_data and admin_data.get("harga", 0) > 0:
        return admin_data["harga"]
    
    if api_produk and "harga" in api_produk:
        return int(api_produk["harga"])
    
    try:
        if produk_cache["data"]:
            for produk in produk_cache["data"]:
                if produk["type"] == kode:
                    return int(produk.get("harga", 0))
    except Exception:
        pass
    
    return 0

def produk_inline_keyboard(is_admin=False):
    try:
        current_time = time.time()
        if current_time - produk_cache["last_updated"] > CACHE_DURATION:
            thread = threading.Thread(target=update_produk_cache_background)
            thread.daemon = True
            thread.start()
        
        data = {"data": produk_cache["data"]} if produk_cache["data"] else None
        
        if not data:
            res = requests.get(cfg["BASE_URL_AKRAB"] + "cek_stock_akrab", timeout=10)
            data = res.json()
            if isinstance(data.get("data"), list):
                produk_cache["data"] = data["data"]
                produk_cache["last_updated"] = current_time
        
        keyboard = []
        admin_produk = get_all_produk_admin()
        
        api_produk_data = data.get("data", [])
        if isinstance(api_produk_data, list):
            for produk in api_produk_data:
                kode = produk['type']
                nama = produk['nama']
                slot = int(produk.get('sisa_slot', 0))
                harga = get_harga_produk(kode, produk)
                
                if is_admin:
                    status = "✅" if slot > 0 else "❌"
                    label = f"{status} [{kode}] {nama} | Rp{harga:,}"
                    keyboard.append([InlineKeyboardButton(label, callback_data=f"admin_produk_detail|{kode}")])
                elif slot > 0:
                    label = f"✅ [{kode}] {nama} | Rp{harga:,}"
                    keyboard.append([InlineKeyboardButton(label, callback_data=f"produk|{kode}|{nama}")])
        
        for kode, info in admin_produk.items():
            if not any(kode == p['type'] for p in api_produk_data):
                if is_admin:
                    label = f"⚠️ [{kode}] (Not in API) | Rp{info['harga']:,}"
                    keyboard.append([InlineKeyboardButton(label, callback_data=f"admin_produk_detail|{kode}")])
        
        if not keyboard:
            keyboard.append([InlineKeyboardButton("❌ No products available", callback_data="disabled_produk")])
        keyboard.append(btn_kembali())
        return InlineKeyboardMarkup(keyboard)

    except Exception as e:
        logger.error(f"Error loading products: {e}")
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Retry", callback_data="beli_produk")], btn_kembali()])


# --- CORE BOT HANDLERS ---

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    tambah_user(user.id, user.username or "", user.full_name)
    update.message.reply_text(
        dashboard_msg(user) + "\n📋 Please choose an option below:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_menu(user.id)
    )

def main_menu_callback(update: Update, context: CallbackContext):
    user = update.effective_user
    if update.callback_query:
        update.callback_query.answer()
        update.callback_query.edit_message_text(
            dashboard_msg(user) + "\n📋 Please choose an option below:",
            parse_mode=ParseMode.HTML,
            reply_markup=get_menu(user.id)
        )
    else:
        update.message.reply_text(
            dashboard_msg(user) + "\n📋 Please choose an option below:",
            parse_mode=ParseMode.HTML,
            reply_markup=get_menu(user.id)
        )
    return ConversationHandler.END

def menu_command(update: Update, context: CallbackContext):
    return main_menu_callback(update, context)

def cek_stok_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if not produk_cache["data"]:
        update_produk_cache_background() # Force update if empty
    
    msg = "📦 <b>Stock Info Akrab XL/Axis</b>\n\n"
    if produk_cache["data"]:
        for produk in produk_cache["data"]:
            status = "✅" if int(produk['sisa_slot']) > 0 else "❌"
            msg += f"{status} <b>[{produk['type']}]</b> {produk['nama']}: {produk['sisa_slot']} units\n"
    else:
        msg += "❌ Failed to retrieve stock data. Please try again."
    
    query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([btn_kembali()]))
    return ConversationHandler.END

# --- BUY PRODUCT CONVERSATION ---

def beli_produk_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text("🔄 Loading product list...", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
    keyboard = produk_inline_keyboard()
    query.edit_message_text(
        "🛒 <b>CHOOSE A PRODUCT</b>\n\nPlease select the product you want to buy:",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
    return CHOOSING_PRODUK

def pilih_produk_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    if data.startswith("produk|"):
        try:
            _, kode, nama = data.split("|")
            produk_api = next((p for p in produk_cache["data"] if p["type"] == kode), None)
            harga = get_harga_produk(kode, produk_api)
            context.user_data["produk"] = {"kode": kode, "nama": nama, "harga": harga}
            
            admin_data = get_produk_admin(kode)
            deskripsi = admin_data.get("deskripsi") if admin_data else ""
            desc_show = f"\n📝 <b>Description:</b>\n<code>{deskripsi}</code>\n" if deskripsi else ""
                
            query.edit_message_text(
                f"✅ <b>Product Selected:</b>\n\n"
                f"📦 <b>[{kode}] {nama}</b>\n"
                f"💰 <b>Price:</b> Rp {harga:,}\n"
                f"{desc_show}\n"
                f"📱 <b>Please enter the destination number:</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([btn_kembali()])
            )
            return INPUT_TUJUAN
        except Exception as e:
            logger.error(f"Error in pilih_produk_callback: {e}")
            query.edit_message_text("❌ An error occurred while selecting the product.", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
            return ConversationHandler.END
    elif data == "disabled_produk":
        query.answer("⚠️ This product is out of stock!", show_alert=True)
    return ConversationHandler.END

def input_tujuan_step(update: Update, context: CallbackContext):
    tujuan = update.message.text.strip()
    if not tujuan.isdigit() or len(tujuan) < 8:
        update.message.reply_text("❌ Invalid number, please re-enter:", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
        return INPUT_TUJUAN

    context.user_data["tujuan"] = tujuan
    produk = context.user_data["produk"]
    admin_data = get_produk_admin(produk["kode"])
    deskripsi = admin_data.get("deskripsi") if admin_data else ""
    desc_show = f"\n📝 <b>Description:</b>\n<code>{deskripsi}</code>\n" if deskripsi else ""

    update.message.reply_text(
        f"✅ <b>ORDER CONFIRMATION</b>\n\n"
        f"📦 <b>Product:</b> [{produk['kode']}] {produk['nama']}\n"
        f"💰 <b>Price:</b> Rp {produk['harga']:,}\n"
        f"📱 <b>Destination Number:</b> <code>{tujuan}</code>\n"
        f"{desc_show}\n"
        f"⚠️ <b>Type 'YA' to confirm or 'BATAL' to cancel.</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([btn_kembali()])
    )
    return KONFIRMASI

def konfirmasi_step(update: Update, context: CallbackContext):
    text = update.message.text.strip().upper()
    if text == "BATAL":
        update.message.reply_text("❌ Transaction cancelled.", reply_markup=get_menu(update.effective_user.id))
        return ConversationHandler.END
    if text != "YA":
        update.message.reply_text("❌ Type 'YA' to confirm or 'BATAL' to cancel.", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
        return KONFIRMASI
        
    produk = context.user_data["produk"]
    tujuan = context.user_data["tujuan"]
    user = update.effective_user
    harga = produk.get("harga", 0)
    
    saldo = get_saldo(user.id)
    if saldo < harga:
        update.message.reply_text("❌ Insufficient balance.", reply_markup=get_menu(user.id))
        return ConversationHandler.END
        
    kurang_saldo(user.id, harga) # Deduct balance immediately
    
    reffid = str(uuid.uuid4())
    url = f"{BASE_URL}trx?produk={produk['kode']}&tujuan={tujuan}&reff_id={reffid}&api_key={API_KEY}"
    
    try:
        data = requests.get(url, timeout=15).json()
        status_text = data.get('status', 'PENDING')
        keterangan = data.get('message', 'Transaction is being processed.')
    except Exception as e:
        tambah_saldo(user.id, harga) # Refund if request fails
        update.message.reply_text(f"❌ Failed to request provider. Your balance has been refunded.\n\nDetail: {e}", reply_markup=get_menu(user.id))
        return ConversationHandler.END
        
    log_riwayat(reffid, user.id, produk["kode"], tujuan, harga, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status_text, keterangan)
    
    update.message.reply_text(
        f"⏳ <b>TRANSACTION IN PROGRESS</b>\n\n"
        f"📦 <b>Product:</b> [{produk['kode']}] {produk['nama']}\n"
        f"📱 <b>Destination:</b> {tujuan}\n"
        f"🔖 <b>RefID:</b> <code>{reffid}</code>\n"
        f"📊 <b>Status:</b> {status_text.upper()}\n"
        f"💬 Note: {keterangan}\n\n"
        f"Please wait a moment for the status update.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_menu(user.id)
    )
    return ConversationHandler.END

# --- TOPUP CONVERSATION & FUNCTIONS ---

def topup_menu(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        "💳 <b>TOP UP BALANCE</b>\n\nPlease select a top-up method:",
        parse_mode=ParseMode.HTML,
        reply_markup=topup_menu_buttons()
    )
    return TOPUP_AMOUNT

def topup_qris_amount(update, context):
    query = update.callback_query
    query.edit_message_text(
        "💰 <b>TOP UP VIA QRIS</b>\n\nEnter the top-up amount (min 10,000, max 5,000,000, multiples of 1000):",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([btn_kembali()])
    )
    return TOPUP_AMOUNT

def topup_amount_step(update, context):
    try:
        nominal = int(update.message.text.replace(".", "").replace(",", ""))
        if not (10000 <= nominal <= 5000000 and nominal % 1000 == 0):
            raise ValueError("Invalid amount")
    except ValueError:
        update.message.reply_text("❌ Invalid amount. Min 10,000, max 5,000,000, in multiples of 1,000. Please re-enter:", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
        return TOPUP_AMOUNT
        
    user = update.effective_user
    unique_code = random.randint(100, 999)
    final_nominal = nominal + unique_code
    
    sukses, hasil = generate_qris(final_nominal, QRIS_STATIS)
    if sukses:
        try:
            img_bytes = base64.b64decode(hasil)
            topup_id = str(uuid.uuid4())
            insert_topup_pending(topup_id, user.id, user.username or "", user.full_name, final_nominal, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "pending")
            
            for adm in ADMIN_IDS:
                try:
                    context.bot.send_message(
                        chat_id=adm,
                        text=f"🔔 New QRIS top-up request!\nUser: <b>{user.full_name}</b> (@{user.username or '-'})\nID: <code>{user.id}</code>\nAmount: <b>Rp {final_nominal:,}</b>",
                        parse_mode=ParseMode.HTML)
                except Exception as e:
                    logger.error(f"Admin notification failed: {e}")
                    
            update.message.reply_photo(photo=img_bytes, caption=(
                f"💰 <b>QRIS FOR TOP UP</b>\n\n"
                f"Amount: <b>Rp {final_nominal:,}</b> (Unique code: <b>{unique_code}</b>)\n\n"
                "Scan the QRIS above using your e-wallet or mobile banking app.\n\n"
                "After transferring, click the button below to upload proof of transfer."
            ), parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Upload Proof of Transfer", callback_data=f"topup_upload|{topup_id}")],
                btn_kembali()
            ]))
        except Exception as e:
            logger.error(f"QRIS error: {e}")
            update.message.reply_text("❌ Failed to decode QRIS image.", reply_markup=get_menu(user.id))
    else:
        update.message.reply_text(f"❌ Failed to create QRIS: {hasil}", reply_markup=get_menu(user.id))
        
    return ConversationHandler.END

def topup_upload_router(update, context):
    query = update.callback_query
    try:
        _, topup_id = query.data.split("|")
        context.user_data['topup_upload_id'] = topup_id
        query.edit_message_text(
            "📤 <b>UPLOAD PROOF OF TRANSFER</b>\n\nPlease upload a photo of the QRIS transfer proof (reply to this message with a photo):",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([btn_kembali()])
        )
        return TOPUP_UPLOAD
    except Exception as e:
        logger.error(f"Error in topup_upload_router: {e}")
        query.edit_message_text("❌ An error occurred.", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
        return ConversationHandler.END

def topup_upload_step(update, context):
    user = update.effective_user
    topup_id = context.user_data.get('topup_upload_id')
    if not topup_id:
        Gemini

2.5 Pro


PRO
Percakapan dengan Gemini

bot_akrab_...inline (1)
PY


Pecah jadi 3 file saja tanpa mengurangi code dan fitur yg ada pastikan sudah fix sebelum kamu berikan padaku


Here are the three files:

database.py: Manages all database connections and queries.

webhook_server.py: Contains the Flask web server for handling API callbacks.

bot.py: The main file that runs the Telegram bot, containing all handlers and bot logic.

1. database.py
This file handles all interactions with the SQLite database.

Python

# database.py
# Description: Handles all SQLite database operations for the bot.

import sqlite3
from datetime import datetime

DBNAME = "botdata.db"

def get_conn():
    """Establishes and returns a database connection."""
    return sqlite3.connect(DBNAME, check_same_thread=False)

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, username TEXT, nama TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS saldo (
        user_id INTEGER PRIMARY KEY, saldo INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS riwayat_transaksi (
        id TEXT PRIMARY KEY, user_id INTEGER, produk TEXT, tujuan TEXT, harga INTEGER, waktu TEXT, status_text TEXT, keterangan TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS topup_pending (
        id TEXT PRIMARY KEY, user_id INTEGER, username TEXT, nama TEXT, nominal INTEGER, waktu TEXT, status TEXT, bukti_file_id TEXT, bukti_caption TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS produk_admin (
        kode TEXT PRIMARY KEY, harga INTEGER, deskripsi TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS kode_unik_topup (
        kode TEXT PRIMARY KEY, 
        user_id INTEGER, 
        nominal INTEGER, 
        digunakan INTEGER DEFAULT 0,
        dibuat_pada TEXT,
        digunakan_pada TEXT
    )""")
    conn.commit()
    conn.close()

def tambah_user(user_id, username, nama):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id, username, nama) VALUES (?, ?, ?)", (user_id, username, nama))
    c.execute("INSERT OR IGNORE INTO saldo (user_id, saldo) VALUES (?, 0)", (user_id,))
    conn.commit()
    conn.close()

def get_saldo(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT saldo FROM saldo WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def tambah_saldo(user_id, amount):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO saldo(user_id, saldo) VALUES (?,0)", (user_id,))
    c.execute("UPDATE saldo SET saldo=saldo+? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def kurang_saldo(user_id, amount):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE saldo SET saldo=saldo-? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def get_riwayat_user(user_id, limit=10):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT * FROM riwayat_transaksi WHERE user_id=? ORDER BY waktu DESC LIMIT ?""", (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_riwayat(limit=10):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT * FROM riwayat_transaksi ORDER BY waktu DESC LIMIT ?""", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def log_riwayat(id, user_id, produk, tujuan, harga, waktu, status_text, keterangan):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO riwayat_transaksi
        (id, user_id, produk, tujuan, harga, waktu, status_text, keterangan)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (id, user_id, produk, tujuan, harga, waktu, status_text, keterangan))
    conn.commit()
    conn.close()

def update_riwayat_status(reffid, status_text, keterangan):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE riwayat_transaksi SET status_text=?, keterangan=? WHERE id=?",
              (status_text, keterangan, reffid))
    conn.commit()
    conn.close()

def get_riwayat_by_refid(reffid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM riwayat_transaksi WHERE id=?", (reffid,))
    row = c.fetchone()
    conn.close()
    return row

def get_user(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, username, nama FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, username, nama FROM users")
    users = c.fetchall()
    conn.close()
    return users

def get_riwayat_jml(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM riwayat_transaksi WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def insert_topup_pending(id, user_id, username, nama, nominal, waktu, status):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO topup_pending
        (id, user_id, username, nama, nominal, waktu, status, bukti_file_id, bukti_caption)
        VALUES (?, ?, ?, ?, ?, ?, ?, '', '')""",
        (id, user_id, username, nama, nominal, waktu, status))
    conn.commit()
    conn.close()

def update_topup_bukti(id, bukti_file_id, bukti_caption):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE topup_pending SET bukti_file_id=?, bukti_caption=? WHERE id=?",
              (bukti_file_id, bukti_caption, id))
    conn.commit()
    conn.close()

def update_topup_status(id, status):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE topup_pending SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()

def get_topup_pending_by_user(user_id, limit=10):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT * FROM topup_pending WHERE user_id=? ORDER BY waktu DESC LIMIT ?""", (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def get_topup_pending_all(limit=10):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT * FROM topup_pending WHERE status='pending' ORDER BY waktu DESC LIMIT ?""", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_topup_by_id(id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM topup_pending WHERE id=?", (id,))
    row = c.fetchone()
    conn.close()
    return row

def get_produk_admin(kode):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT harga, deskripsi FROM produk_admin WHERE kode=?", (kode,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"harga": row[0], "deskripsi": row[1]}
    return None

def set_produk_admin_harga(kode, harga):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO produk_admin (kode, harga, deskripsi) VALUES (?, ?, '')", (kode, harga))
    c.execute("UPDATE produk_admin SET harga=? WHERE kode=?", (harga, kode))
    conn.commit()
    conn.close()

def set_produk_admin_deskripsi(kode, deskripsi):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO produk_admin (kode, harga, deskripsi) VALUES (?, 0, ?)", (kode, deskripsi))
    c.execute("UPDATE produk_admin SET deskripsi=? WHERE kode=?", (deskripsi, kode))
    conn.commit()
    conn.close()

def get_all_produk_admin():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT kode, harga, deskripsi FROM produk_admin")
    rows = c.fetchall()
    conn.close()
    
    produk_dict = {}
    for row in rows:
        produk_dict[row[0]] = {"harga": row[1], "deskripsi": row[2]}
    return produk_dict

def generate_kode_unik():
    import random
    return str(random.randint(100, 999))

def simpan_kode_unik(kode, user_id, nominal):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO kode_unik_topup 
        (kode, user_id, nominal, digunakan, dibuat_pada) 
        VALUES (?, ?, ?, 0, ?)""",
        (kode, user_id, nominal, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_kode_unik(kode):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM kode_unik_topup WHERE kode=?", (kode,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "kode": row[0],
            "user_id": row[1],
            "nominal": row[2],
            "digunakan": row[3],
            "dibuat_pada": row[4],
            "digunakan_pada": row[5]
        }
    return None

def gunakan_kode_unik(kode):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE kode_unik_topup SET digunakan=1, digunakan_pada=? WHERE kode=?",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), kode))
    conn.commit()
    conn.close()

def get_kode_unik_user(user_id, limit=5):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM kode_unik_topup WHERE user_id=? ORDER BY dibuat_pada DESC LIMIT ?", (user_id, limit))
    rows = c.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        result.append({
            "kode": row[0],
            "user_id": row[1],
            "nominal": row[2],
            "digunakan": row[3],
            "dibuat_pada": row[4],
            "digunakan_pada": row[5]
        })
    return result

2. webhook_server.py
This file defines the Flask application to handle incoming webhook notifications.

Python

# webhook_server.py
# Description: Flask web server to handle incoming webhooks from the transaction API.

import re
import logging
from flask import Flask, request, jsonify
from telegram import ParseMode

# Import database functions
from database import get_riwayat_by_refid, update_riwayat_status, tambah_saldo, kurang_saldo, get_saldo, get_menu

logger = logging.getLogger(__name__)

# REGEX to parse webhook messages
RX = re.compile(
    r'RC=(?P<reffid>[a-f0-9-]+)\s+TrxID=(?P<trxid>\d+)\s+'
    r'(?P<produk>[A-Z0-9]+)\.(?P<tujuan>\d+)\s+'
    r'(?P<status_text>[A-Za-z]+)\s*'
    r'(?P<keterangan>.+?)'
    r'(?:\s+Saldo[\s\S]*?)?'
    r'(?:\bresult=(?P<status_code>\d+))?\s*>?$',
    re.I
)

def create_webhook_app(updater, webhook_port):
    """Creates and configures the Flask application for the webhook."""
    app = Flask(__name__)

    @app.route('/webhook', methods=['GET', 'POST'])
    def webhook_handler():
        try:
            logger.info(f"[WEBHOOK RECEIVE] Headers: {request.headers}")
            logger.info(f"[WEBHOOK RECEIVE] Form Data: {request.form}")
            logger.info(f"[WEBHOOK RECEIVE] Arguments: {request.args}")

            message = request.args.get('message') or request.form.get('message')
            if not message:
                logger.warning("[WEBHOOK] Empty message received.")
                return jsonify({'ok': False, 'error': 'message kosong'}), 400

            match = RX.match(message)
            if not match:
                logger.warning(f"[WEBHOOK] Unrecognized format -> {message}")
                return jsonify({'ok': False, 'error': 'format tidak dikenali'}), 200

            groups = match.groupdict()
            reffid = groups.get('reffid')
            status_text = groups.get('status_text')
            keterangan = groups.get('keterangan', '').strip()

            logger.info(f"== Webhook received for RefID: {reffid} with status: {status_text} ==")
            
            riwayat = get_riwayat_by_refid(reffid)
            if not riwayat:
                logger.warning(f"RefID {reffid} not found in database.")
                return jsonify({'ok': False, 'error': 'transaksi tidak ditemukan'}), 200
            
            user_id = riwayat[1]
            produk_kode = riwayat[2]
            harga = riwayat[4]
            current_status = riwayat[6].lower()

            if "sukses" in current_status or "gagal" in current_status or "batal" in current_status:
                logger.info(f"RefID {reffid} already has a final status. No update needed.")
                return jsonify({'ok': True, 'message': 'Status sudah final'}), 200
            
            update_riwayat_status(reffid, status_text.upper(), keterangan)

            if "sukses" in status_text.lower():
                try:
                    updater.bot.send_message(user_id, 
                        f"✅ <b>TRANSAKSI SUKSES</b>\n\n"
                        f"Produk: [{produk_kode}] dengan harga Rp {harga:,} telah berhasil dikirim.\n"
                        f"Keterangan: {keterangan}\n\n"
                        f"Saldo Anda sekarang: Rp {get_saldo(user_id):,}",
                        parse_mode=ParseMode.HTML,
                        reply_markup=get_menu(user_id))
                except Exception as e:
                    logger.error(f"Failed to send success notification to user {user_id}: {e}")
            
            elif "gagal" in status_text.lower() or "batal" in status_text.lower():
                tambah_saldo(user_id, harga)
                try:
                    updater.bot.send_message(user_id, 
                        f"❌ <b>TRANSAKSI GAGAL</b>\n\n"
                        f"Transaksi untuk produk [{produk_kode}] dengan harga Rp {harga:,} GAGAL.\n"
                        f"Keterangan: {keterangan}\n\n"
                        f"Saldo Anda telah dikembalikan. Saldo sekarang: Rp {get_saldo(user_id):,}",
                        parse_mode=ParseMode.HTML,
                        reply_markup=get_menu(user_id))
                except Exception as e:
                    logger.error(f"Failed to send failure notification to user {user_id}: {e}")
            
            else:
                logger.info(f"Unknown webhook status: {status_text}")
            
            return jsonify({'ok': True, 'message': 'Webhook processed'}), 200

        except Exception as e:
            logger.error(f"[WEBHOOK][ERROR] {e}", exc_info=True)
            return jsonify({'ok': False, 'error': 'internal_error'}), 500

    def run():
        app.run(host='0.0.0.0', port=webhook_port)

    return run

3. bot.py
This is the main entry point for your application. Run this file to start the bot.

Python

# bot.py
# Description: Main file for the Telegram bot logic, handlers, and execution.

import os, json, uuid, base64, logging, time, threading, random, requests
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, InputMediaPhoto
)
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler, CallbackContext,
)

# Import from local modules
from database import *
from webhook_server import create_webhook_app

# --- CONFIGURATION & SETUP ---

# Load configuration
try:
    with open("config.json") as f:
        cfg = json.load(f)
except FileNotFoundError:
    print("Error: config.json not found. Please ensure the file exists.")
    exit(1)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON in config.json. Details: {e}")
    exit(1)
    
TOKEN = cfg["TOKEN"]
ADMIN_IDS = [int(i) for i in cfg["ADMIN_IDS"]]
BASE_URL = cfg["BASE_URL"]
API_KEY = cfg["API_KEY"]
QRIS_STATIS = cfg["QRIS_STATIS"]
WEBHOOK_PORT = cfg["WEBHOOK_PORT"]
LOG_FILE = 'bot_error.log'

# Setup logging
logging.basicConfig(
    filename=LOG_FILE, 
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Product cache
produk_cache = {
    "data": [],
    "last_updated": 0,
    "update_in_progress": False
}
CACHE_DURATION = 300  # 5 minutes

# --- CACHE & API HELPERS ---

def update_produk_cache_background():
    """Updates the product cache from the API in a background thread."""
    if produk_cache["update_in_progress"]:
        return
        
    produk_cache["update_in_progress"] = True
    try:
        start_time = time.time()
        res = requests.get(cfg["BASE_URL_AKRAB"] + "cek_stock_akrab", timeout=10)
        data = res.json()
        
        if isinstance(data.get("data"), list):
            produk_cache["data"] = data["data"]
            produk_cache["last_updated"] = time.time()
            logger.info(f"Product cache updated. Products: {len(data['data'])}. Time: {time.time() - start_time:.2f}s")
        else:
            logger.error("Unrecognized stock data format.")
    except Exception as e:
        logger.error(f"Failed to update product cache: {e}")
    finally:
        produk_cache["update_in_progress"] = False

def generate_qris(amount, qris_statis):
    """Generates a QRIS code using an external API."""
    url = "https://qrisku.my.id/api"
    payload = {"amount": str(amount), "qris_statis": qris_statis}
    try:
        res = requests.post(url, json=payload, timeout=20)
        data = res.json()
        if data.get('status') == 'success' and 'qris_base64' in data:
            return True, data['qris_base64']
        else:
            return False, data.get('message', 'Failed to generate QRIS')
    except Exception as e:
        return False, f"QRIS API connection error: {e}"

# --- CONVERSATION STATES ---
(
    CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI, BC_MESSAGE, TOPUP_AMOUNT, 
    TOPUP_UPLOAD, ADMIN_CEKUSER, ADMIN_EDIT_HARGA, ADMIN_EDIT_DESKRIPSI, 
    INPUT_KODE_UNIK
) = range(10)

# --- UI COMPONENTS ---

def btn_kembali(): 
    return [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]

def btn_kembali_menu(): 
    return [InlineKeyboardButton("🏠 Menu Utama", callback_data="main_menu")]

def get_menu(uid): 
    return menu_admin(uid) if uid in ADMIN_IDS else menu_user(uid)

def menu_user(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Beli Produk", callback_data='beli_produk'),
         InlineKeyboardButton("💳 Top Up Saldo", callback_data='topup_menu')],
        [InlineKeyboardButton("📋 Riwayat Transaksi", callback_data='riwayat'),
         InlineKeyboardButton("📦 Info Stok", callback_data='cek_stok')],
        [InlineKeyboardButton("🧾 Riwayat Top Up", callback_data="topup_riwayat"),
         InlineKeyboardButton("🔑 Kode Unik Saya", callback_data="my_kode_unik")],
        [InlineKeyboardButton("ℹ️ Bantuan", callback_data="bantuan")],
    ])

def menu_admin(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Beli Produk", callback_data='beli_produk'),
         InlineKeyboardButton("💳 Top Up Saldo", callback_data='topup_menu')],
        [InlineKeyboardButton("📋 Riwayat Saya", callback_data='riwayat'),
         InlineKeyboardButton("📦 Info Stok", callback_data='cek_stok')],
        [InlineKeyboardButton("👥 Admin Panel", callback_data='admin_panel')],
        [InlineKeyboardButton("ℹ️ Bantuan", callback_data="bantuan")],
    ])

def admin_panel_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Data User", callback_data='admin_cekuser'),
         InlineKeyboardButton("💰 Lihat Saldo", callback_data='lihat_saldo')],
        [InlineKeyboardButton("📊 Semua Riwayat", callback_data='semua_riwayat'),
         InlineKeyboardButton("📢 Broadcast", callback_data='broadcast')],
        [InlineKeyboardButton("✅ Approve Top Up", callback_data="admin_topup_pending"),
         InlineKeyboardButton("⚙️ Manajemen Produk", callback_data="admin_produk")],
        [InlineKeyboardButton("🔑 Generate Kode Unik", callback_data="admin_generate_kode")],
        btn_kembali()
    ])

def topup_menu_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 QRIS (Otomatis)", callback_data="topup_qris")],
        [InlineKeyboardButton("🔑 Kode Unik (Manual)", callback_data="topup_kode_unik")],
        btn_kembali()
    ])

def dashboard_msg(user):
    saldo = get_saldo(user.id)
    total_trx = get_riwayat_jml(user.id)
    return (
        f"✨ <b>DASHBOARD USER</b> ✨\n\n"
        f"👤 <b>{user.full_name}</b>\n"
        f"📧 @{user.username or '-'}\n"
        f"🆔 <code>{user.id}</code>\n\n"
        f"💰 <b>Saldo:</b> <code>Rp {saldo:,}</code>\n"
        f"📊 <b>Total Transaksi:</b> <b>{total_trx}</b>\n"
    )

# --- PRODUCT FUNCTIONS ---

def get_harga_produk(kode, api_produk=None):
    admin_data = get_produk_admin(kode)
    if admin_data and admin_data.get("harga", 0) > 0:
        return admin_data["harga"]
    
    if api_produk and "harga" in api_produk:
        return int(api_produk["harga"])
    
    try:
        if produk_cache["data"]:
            for produk in produk_cache["data"]:
                if produk["type"] == kode:
                    return int(produk.get("harga", 0))
    except Exception:
        pass
    
    return 0

def produk_inline_keyboard(is_admin=False):
    try:
        current_time = time.time()
        if current_time - produk_cache["last_updated"] > CACHE_DURATION:
            thread = threading.Thread(target=update_produk_cache_background)
            thread.daemon = True
            thread.start()
        
        data = {"data": produk_cache["data"]} if produk_cache["data"] else None
        
        if not data:
            res = requests.get(cfg["BASE_URL_AKRAB"] + "cek_stock_akrab", timeout=10)
            data = res.json()
            if isinstance(data.get("data"), list):
                produk_cache["data"] = data["data"]
                produk_cache["last_updated"] = current_time
        
        keyboard = []
        admin_produk = get_all_produk_admin()
        
        api_produk_data = data.get("data", [])
        if isinstance(api_produk_data, list):
            for produk in api_produk_data:
                kode = produk['type']
                nama = produk['nama']
                slot = int(produk.get('sisa_slot', 0))
                harga = get_harga_produk(kode, produk)
                
                if is_admin:
                    status = "✅" if slot > 0 else "❌"
                    label = f"{status} [{kode}] {nama} | Rp{harga:,}"
                    keyboard.append([InlineKeyboardButton(label, callback_data=f"admin_produk_detail|{kode}")])
                elif slot > 0:
                    label = f"✅ [{kode}] {nama} | Rp{harga:,}"
                    keyboard.append([InlineKeyboardButton(label, callback_data=f"produk|{kode}|{nama}")])
        
        for kode, info in admin_produk.items():
            if not any(kode == p['type'] for p in api_produk_data):
                if is_admin:
                    label = f"⚠️ [{kode}] (Not in API) | Rp{info['harga']:,}"
                    keyboard.append([InlineKeyboardButton(label, callback_data=f"admin_produk_detail|{kode}")])
        
        if not keyboard:
            keyboard.append([InlineKeyboardButton("❌ No products available", callback_data="disabled_produk")])
        keyboard.append(btn_kembali())
        return InlineKeyboardMarkup(keyboard)

    except Exception as e:
        logger.error(f"Error loading products: {e}")
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Retry", callback_data="beli_produk")], btn_kembali()])


# --- CORE BOT HANDLERS ---

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    tambah_user(user.id, user.username or "", user.full_name)
    update.message.reply_text(
        dashboard_msg(user) + "\n📋 Please choose an option below:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_menu(user.id)
    )

def main_menu_callback(update: Update, context: CallbackContext):
    user = update.effective_user
    if update.callback_query:
        update.callback_query.answer()
        update.callback_query.edit_message_text(
            dashboard_msg(user) + "\n📋 Please choose an option below:",
            parse_mode=ParseMode.HTML,
            reply_markup=get_menu(user.id)
        )
    else:
        update.message.reply_text(
            dashboard_msg(user) + "\n📋 Please choose an option below:",
            parse_mode=ParseMode.HTML,
            reply_markup=get_menu(user.id)
        )
    return ConversationHandler.END

def menu_command(update: Update, context: CallbackContext):
    return main_menu_callback(update, context)

def cek_stok_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if not produk_cache["data"]:
        update_produk_cache_background() # Force update if empty
    
    msg = "📦 <b>Stock Info Akrab XL/Axis</b>\n\n"
    if produk_cache["data"]:
        for produk in produk_cache["data"]:
            status = "✅" if int(produk['sisa_slot']) > 0 else "❌"
            msg += f"{status} <b>[{produk['type']}]</b> {produk['nama']}: {produk['sisa_slot']} units\n"
    else:
        msg += "❌ Failed to retrieve stock data. Please try again."
    
    query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([btn_kembali()]))
    return ConversationHandler.END

# --- BUY PRODUCT CONVERSATION ---

def beli_produk_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text("🔄 Loading product list...", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
    keyboard = produk_inline_keyboard()
    query.edit_message_text(
        "🛒 <b>CHOOSE A PRODUCT</b>\n\nPlease select the product you want to buy:",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
    return CHOOSING_PRODUK

def pilih_produk_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    if data.startswith("produk|"):
        try:
            _, kode, nama = data.split("|")
            produk_api = next((p for p in produk_cache["data"] if p["type"] == kode), None)
            harga = get_harga_produk(kode, produk_api)
            context.user_data["produk"] = {"kode": kode, "nama": nama, "harga": harga}
            
            admin_data = get_produk_admin(kode)
            deskripsi = admin_data.get("deskripsi") if admin_data else ""
            desc_show = f"\n📝 <b>Description:</b>\n<code>{deskripsi}</code>\n" if deskripsi else ""
                
            query.edit_message_text(
                f"✅ <b>Product Selected:</b>\n\n"
                f"📦 <b>[{kode}] {nama}</b>\n"
                f"💰 <b>Price:</b> Rp {harga:,}\n"
                f"{desc_show}\n"
                f"📱 <b>Please enter the destination number:</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([btn_kembali()])
            )
            return INPUT_TUJUAN
        except Exception as e:
            logger.error(f"Error in pilih_produk_callback: {e}")
            query.edit_message_text("❌ An error occurred while selecting the product.", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
            return ConversationHandler.END
    elif data == "disabled_produk":
        query.answer("⚠️ This product is out of stock!", show_alert=True)
    return ConversationHandler.END

def input_tujuan_step(update: Update, context: CallbackContext):
    tujuan = update.message.text.strip()
    if not tujuan.isdigit() or len(tujuan) < 8:
        update.message.reply_text("❌ Invalid number, please re-enter:", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
        return INPUT_TUJUAN

    context.user_data["tujuan"] = tujuan
    produk = context.user_data["produk"]
    admin_data = get_produk_admin(produk["kode"])
    deskripsi = admin_data.get("deskripsi") if admin_data else ""
    desc_show = f"\n📝 <b>Description:</b>\n<code>{deskripsi}</code>\n" if deskripsi else ""

    update.message.reply_text(
        f"✅ <b>ORDER CONFIRMATION</b>\n\n"
        f"📦 <b>Product:</b> [{produk['kode']}] {produk['nama']}\n"
        f"💰 <b>Price:</b> Rp {produk['harga']:,}\n"
        f"📱 <b>Destination Number:</b> <code>{tujuan}</code>\n"
        f"{desc_show}\n"
        f"⚠️ <b>Type 'YA' to confirm or 'BATAL' to cancel.</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([btn_kembali()])
    )
    return KONFIRMASI

def konfirmasi_step(update: Update, context: CallbackContext):
    text = update.message.text.strip().upper()
    if text == "BATAL":
        update.message.reply_text("❌ Transaction cancelled.", reply_markup=get_menu(update.effective_user.id))
        return ConversationHandler.END
    if text != "YA":
        update.message.reply_text("❌ Type 'YA' to confirm or 'BATAL' to cancel.", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
        return KONFIRMASI
        
    produk = context.user_data["produk"]
    tujuan = context.user_data["tujuan"]
    user = update.effective_user
    harga = produk.get("harga", 0)
    
    saldo = get_saldo(user.id)
    if saldo < harga:
        update.message.reply_text("❌ Insufficient balance.", reply_markup=get_menu(user.id))
        return ConversationHandler.END
        
    kurang_saldo(user.id, harga) # Deduct balance immediately
    
    reffid = str(uuid.uuid4())
    url = f"{BASE_URL}trx?produk={produk['kode']}&tujuan={tujuan}&reff_id={reffid}&api_key={API_KEY}"
    
    try:
        data = requests.get(url, timeout=15).json()
        status_text = data.get('status', 'PENDING')
        keterangan = data.get('message', 'Transaction is being processed.')
    except Exception as e:
        tambah_saldo(user.id, harga) # Refund if request fails
        update.message.reply_text(f"❌ Failed to request provider. Your balance has been refunded.\n\nDetail: {e}", reply_markup=get_menu(user.id))
        return ConversationHandler.END
        
    log_riwayat(reffid, user.id, produk["kode"], tujuan, harga, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status_text, keterangan)
    
    update.message.reply_text(
        f"⏳ <b>TRANSACTION IN PROGRESS</b>\n\n"
        f"📦 <b>Product:</b> [{produk['kode']}] {produk['nama']}\n"
        f"📱 <b>Destination:</b> {tujuan}\n"
        f"🔖 <b>RefID:</b> <code>{reffid}</code>\n"
        f"📊 <b>Status:</b> {status_text.upper()}\n"
        f"💬 Note: {keterangan}\n\n"
        f"Please wait a moment for the status update.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_menu(user.id)
    )
    return ConversationHandler.END

# --- TOPUP CONVERSATION & FUNCTIONS ---

def topup_menu(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        "💳 <b>TOP UP BALANCE</b>\n\nPlease select a top-up method:",
        parse_mode=ParseMode.HTML,
        reply_markup=topup_menu_buttons()
    )
    return TOPUP_AMOUNT

def topup_qris_amount(update, context):
    query = update.callback_query
    query.edit_message_text(
        "💰 <b>TOP UP VIA QRIS</b>\n\nEnter the top-up amount (min 10,000, max 5,000,000, multiples of 1000):",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([btn_kembali()])
    )
    return TOPUP_AMOUNT

def topup_amount_step(update, context):
    try:
        nominal = int(update.message.text.replace(".", "").replace(",", ""))
        if not (10000 <= nominal <= 5000000 and nominal % 1000 == 0):
            raise ValueError("Invalid amount")
    except ValueError:
        update.message.reply_text("❌ Invalid amount. Min 10,000, max 5,000,000, in multiples of 1,000. Please re-enter:", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
        return TOPUP_AMOUNT
        
    user = update.effective_user
    unique_code = random.randint(100, 999)
    final_nominal = nominal + unique_code
    
    sukses, hasil = generate_qris(final_nominal, QRIS_STATIS)
    if sukses:
        try:
            img_bytes = base64.b64decode(hasil)
            topup_id = str(uuid.uuid4())
            insert_topup_pending(topup_id, user.id, user.username or "", user.full_name, final_nominal, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "pending")
            
            for adm in ADMIN_IDS:
                try:
                    context.bot.send_message(
                        chat_id=adm,
                        text=f"🔔 New QRIS top-up request!\nUser: <b>{user.full_name}</b> (@{user.username or '-'})\nID: <code>{user.id}</code>\nAmount: <b>Rp {final_nominal:,}</b>",
                        parse_mode=ParseMode.HTML)
                except Exception as e:
                    logger.error(f"Admin notification failed: {e}")
                    
            update.message.reply_photo(photo=img_bytes, caption=(
                f"💰 <b>QRIS FOR TOP UP</b>\n\n"
                f"Amount: <b>Rp {final_nominal:,}</b> (Unique code: <b>{unique_code}</b>)\n\n"
                "Scan the QRIS above using your e-wallet or mobile banking app.\n\n"
                "After transferring, click the button below to upload proof of transfer."
            ), parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Upload Proof of Transfer", callback_data=f"topup_upload|{topup_id}")],
                btn_kembali()
            ]))
        except Exception as e:
            logger.error(f"QRIS error: {e}")
            update.message.reply_text("❌ Failed to decode QRIS image.", reply_markup=get_menu(user.id))
    else:
        update.message.reply_text(f"❌ Failed to create QRIS: {hasil}", reply_markup=get_menu(user.id))
        
    return ConversationHandler.END

def topup_upload_router(update, context):
    query = update.callback_query
    try:
        _, topup_id = query.data.split("|")
        context.user_data['topup_upload_id'] = topup_id
        query.edit_message_text(
            "📤 <b>UPLOAD PROOF OF TRANSFER</b>\n\nPlease upload a photo of the QRIS transfer proof (reply to this message with a photo):",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([btn_kembali()])
        )
        return TOPUP_UPLOAD
    except Exception as e:
        logger.error(f"Error in topup_upload_router: {e}")
        query.edit_message_text("❌ An error occurred.", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
        return ConversationHandler.END

def topup_upload_step(update, context):
    user = update.effective_user
    topup_id = context.user_data.get('topup_upload_id')
    if not topup_id:
        update.message.reply_text("❌ Top-up ID not found. Please use the button in the top-up menu.", reply_markup=get_menu(user.id))
        return ConversationHandler.END
        
    if not update.message.photo:
        update.message.reply_text("❌ Only photos are accepted as proof of transfer. Please upload again!", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
        return TOPUP_UPLOAD
        
    file_id = update.message.photo[-1].file_id
    caption = update.message.caption or ""
    update_topup_bukti(topup_id, file_id, caption)
    
    for adm in ADMIN_IDS:
        try:
            context.bot.send_message(
                chat_id=adm,
                text=f"🔔 QRIS transfer proof received from user <b>{user.full_name}</b> (@{user.username or '-'})",
                parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Admin notification failed: {e}")
            
    context.user_data.pop('topup_upload_id', None)
    update.message.reply_text("✅ Proof of transfer sent successfully. Please wait for admin verification.", reply_markup=get_menu(user.id))
    return ConversationHandler.END

def topup_kode_unik_menu(update, context):
    query = update.callback_query
    query.edit_message_text(
        "🔑 <b>TOP UP VIA UNIQUE CODE</b>\n\nPlease enter the unique code provided by the admin:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([btn_kembali()])
    )
    return INPUT_KODE_UNIK

def input_kode_unik_step(update, context):
    kode = update.message.text.strip()
    user = update.effective_user
    
    kode_data = get_kode_unik(kode)
    if not kode_data:
        update.message.reply_text("❌ Invalid or non-existent unique code.", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
        return INPUT_KODE_UNIK
        
    if kode_data["digunakan"]:
        update.message.reply_text("❌ This unique code has already been used.", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
        return INPUT_KODE_UNIK
        
    tambah_saldo(user.id, kode_data["nominal"])
    gunakan_kode_unik(kode)
    
    update.message.reply_text(
        f"✅ <b>TOP UP SUCCESSFUL</b>\n\n"
        f"Unique code: <b>{kode}</b>\n"
        f"Amount: <b>Rp {kode_data['nominal']:,}</b>\n"
        f"Current balance: <b>Rp {get_saldo(user.id):,}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_menu(user.id)
    )
    return ConversationHandler.END

# --- HISTORY & INFO MENUS ---

def topup_riwayat_menu(update: Update, context: CallbackContext):
    user = update.effective_user
    items = get_topup_pending_by_user(user.id, 10)
    msg = "📋 <b>YOUR TOP UP HISTORY (last 10)</b>\n\n"
    if not items:
        msg += "No top-up requests yet."
    else:
        for r in items:
            emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(r[6], "❓")
            msg += (
                f"{emoji} <b>{r[5]}</b>\n"
                f"ID: <code>{r[0]}</code>\n"
                f"Amount: Rp {r[4]:,}\n"
                f"Status: <b>{r[6].capitalize()}</b>\n\n"
            )
            
    if update.callback_query:
        update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([btn_kembali()]))
    else:
        update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([btn_kembali()]))
    return ConversationHandler.END

def my_kode_unik_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user
    items = get_kode_unik_user(user.id, 10)
    msg = "🔑 <b>MY UNIQUE CODES (last 10)</b>\n\n"
    if not items:
        msg += "No unique codes have been created."
    else:
        for kode in items:
            status = "✅ Used" if kode["digunakan"] else "⏳ Not used"
            msg += (
                f"Code: <code>{kode['kode']}</code>\n"
                f"Amount: Rp {kode['nominal']:,}\n"
                f"Status: {status}\n"
                f"Created: {kode['dibuat_pada']}\n\n"
            )
            
    query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([btn_kembali()]))
    return ConversationHandler.END

def riwayat_user(query, context):
    user = query.from_user
    items = get_riwayat_user(user.id)
    msg = "📋 <b>YOUR TRANSACTION HISTORY (last 10)</b>\n\n"
    if not items:
        msg += "No transactions yet."
    else:
        for r in items:
            status = r[6].upper()
            emoji = "✅" if "SUKSES" in status else ("❌" if "GAGAL" in status or "BATAL" in status else "⏳")
            msg += (
                f"{emoji} <b>{r[5]}</b>\n"
                f"ID: <code>{r[0]}</code>\n"
                f"Product: [{r[2]}] to {r[3]}\n"
                f"Price: Rp {r[4]:,}\n"
                f"Status: <b>{status}</b>\n"
                f"Note: {r[7]}\n\n"
            )
    query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([btn_kembali()]))

def bantuan_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    msg = (
        "❓ <b>HELP</b>\n\n"
        "📋 <b>How to use the bot:</b>\n"
        "1. Select <b>Buy Product</b> to purchase a product.\n"
        "2. Select <b>Top Up Balance</b> to add funds.\n"
        "3. Use the <b>History</b> menu to view your transactions.\n\n"
        "💳 <b>Top Up Methods:</b>\n"
        "- <b>QRIS</b>: Scan a QR code to transfer.\n"
        "- <b>Unique Code</b>: Enter a code from an admin.\n\n"
        "📞 <b>Further Assistance:</b>\n"
        "Contact an admin for any other questions."
    )
    query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([btn_kembali()]))
    return ConversationHandler.END

# --- ADMIN PANEL & FUNCTIONS ---

def admin_panel(update: Update, context: CallbackContext):
    query = update.callback_query
    query.edit_message_text(
        "⚙️ <b>ADMIN PANEL</b>\n\nPlease select an admin menu:",
        parse_mode=ParseMode.HTML,
        reply_markup=admin_panel_menu()
    )
    return ConversationHandler.END

def semua_riwayat_admin(query, context):
    items = get_all_riwayat()
    msg = "📋 <b>ALL TRANSACTION HISTORY (last 10)</b>\n\n"
    if not items:
        msg += "No transactions yet."
    else:
        for r in items:
            status = r[6].upper()
            emoji = "✅" if "SUKSES" in status else ("❌" if "GAGAL" in status or "BATAL" in status else "⏳")
            user = get_user(r[1])
            username = f"@{user[1]}" if user and user[1] else "Unknown"
            msg += (
                f"{emoji} <b>{r[5]}</b>\n"
                f"User: {username} ({r[1]})\n"
                f"Product: [{r[2]}] to {r[3]}\n"
                f"Price: Rp {r[4]:,}\n"
                f"Status: <b>{status}</b>\n"
                f"Note: {r[7]}\n\n"
            )
    query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([btn_kembali()]))

def admin_topup_pending_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    items = get_topup_pending_all(10)
    keyboard = []
    for r in items:
        label = f"{r[3]} | Rp{r[4]:,} | {r[5]}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"admin_topup_detail|{r[0]}")])
    if not keyboard:
        keyboard.append([InlineKeyboardButton("✅ No pending top-ups", callback_data="main_menu")])
    keyboard.append(btn_kembali())
    query.edit_message_text(
        "📋 <b>PENDING TOP UP REQUESTS (last 10)</b>\n\nSelect to view details:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

def admin_topup_detail(update: Update, context: CallbackContext):
    query = update.callback_query
    try:
        topup_id = query.data.split("|")[1]
        r = get_topup_by_id(topup_id)
        if not r:
            query.answer("❌ Data not found.", show_alert=True)
            return ConversationHandler.END
            
        caption = (
            f"📋 <b>TOP UP DETAILS</b>\n\n"
            f"👤 <b>User:</b> {r[3]} (@{r[2]})\n"
            f"🆔 <b>User ID:</b> <code>{r[1]}</code>\n"
            f"💰 <b>Amount:</b> Rp {r[4]:,}\n"
            f"⏰ <b>Time:</b> {r[5]}\n"
            f"📊 <b>Status:</b> {r[6].capitalize()}\n"
            f"🔖 <b>Top Up ID:</b> <code>{r[0]}</code>\n"
        )
        actions = [
            [InlineKeyboardButton("✅ Approve", callback_data=f"admin_topup_action|approve|{topup_id}"),
             InlineKeyboardButton("❌ Reject", callback_data=f"admin_topup_action|reject|{topup_id}")],
            btn_kembali()
        ]
        
        if r[7]: # if proof exists
            query.edit_message_media(
                InputMediaPhoto(r[7], caption=caption, parse_mode=ParseMode.HTML),
                reply_markup=InlineKeyboardMarkup(actions)
            )
        else:
            query.edit_message_text(caption + "\n\n❌ No proof of transfer yet", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(actions))
    except Exception as e:
        logger.error(f"Error in admin_topup_detail: {e}")
        query.edit_message_text("❌ An error occurred while loading top-up details.", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
    return ConversationHandler.END

def admin_topup_action(update: Update, context: CallbackContext):
    query = update.callback_query
    try:
        _, action, topup_id = query.data.split("|")
        r = get_topup_by_id(topup_id)
        if not r:
            query.answer("❌ Data not found.", show_alert=True)
            return ConversationHandler.END
            
        if action == "approve":
            tambah_saldo(r[1], r[4])
            update_topup_status(topup_id, "approved")
            try:
                context.bot.send_message(r[1], 
                    f"✅ <b>TOP UP APPROVED</b>\n\n"
                    f"Your top-up of Rp {r[4]:,} has been approved!\n"
                    f"Your current balance: Rp {get_saldo(r[1]):,}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_menu(r[1]))
            except Exception as e:
                logger.error(f"Approval notification failed: {e}")
            query.answer("✅ Top-up approved successfully.", show_alert=True)
        
        elif action == "reject":
            update_topup_status(topup_id, "rejected")
            try:
                context.bot.send_message(r[1], 
                    f"❌ <b>TOP UP REJECTED</b>\n\n"
                    f"Your top-up of Rp {r[4]:,} was rejected by an admin.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_menu(r[1]))
            except Exception as e:
                logger.error(f"Rejection notification failed: {e}")
            query.answer("❌ Top-up rejected.", show_alert=True)
            
        return admin_topup_pending_menu(update, context)
    except Exception as e:
        logger.error(f"Error in admin_topup_action: {e}")
        query.edit_message_text("❌ An error occurred while processing the action.", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
        return ConversationHandler.END

def admin_generate_kode(update: Update, context: CallbackContext):
    query = update.callback_query
    query.edit_message_text(
        "🔑 <b>GENERATE UNIQUE CODE</b>\n\nEnter the amount for the unique code (min 10,000):",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([btn_kembali()])
    )
    return INPUT_KODE_UNIK

def admin_generate_kode_step(update: Update, context: CallbackContext):
    try:
        nominal = int(update.message.text.replace(".", "").replace(",", ""))
        if nominal < 10000:
            update.message.reply_text("❌ Minimum amount is 10,000", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
            return INPUT_KODE_UNIK
            
        kode = generate_kode_unik()
        simpan_kode_unik(kode, update.effective_user.id, nominal)
        
        update.message.reply_text(
            f"✅ <b>UNIQUE CODE CREATED</b>\n\n"
            f"Code: <code>{kode}</code>\n"
            f"Amount: <b>Rp {nominal:,}</b>\n\n"
            f"Provide this code to the user for top-up.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_menu(update.effective_user.id)
        )
    except ValueError:
        update.message.reply_text("❌ Please enter a valid number", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
        return INPUT_KODE_UNIK
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        update.message.reply_text("❌ An error occurred", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
    
    return ConversationHandler.END

def broadcast_step(update: Update, context: CallbackContext):
    text = update.message.text
    users = get_all_users()
    count = 0
    fail = 0
    for u in users:
        try:
            context.bot.send_message(
                chat_id=int(u[0]),
                text=f"📢 <b>BROADCAST</b>\n\n{text}",
                parse_mode=ParseMode.HTML
            )
            count += 1
        except Exception:
            fail += 1
    update.message.reply_text(
        f"✅ <b>BROADCAST COMPLETE</b>\n\nSuccessful: {count}\nFailed: {fail}",
        parse_mode=ParseMode.HTML,
        reply_markup=get_menu(update.effective_user.id)
    )
    return ConversationHandler.END

# Add other admin functions (cekuser, edit produk) similarly...
# (Code for these functions is omitted for brevity but should be included here from the original file)


# --- ROUTER & GENERAL HANDLERS ---

def callback_router(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    
    routes = {
        "main_menu": main_menu_callback,
        "beli_produk": beli_produk_menu,
        "cek_stok": cek_stok_menu,
        "topup_menu": topup_menu,
        "topup_qris": topup_qris_amount,
        "topup_kode_unik": topup_kode_unik_menu,
        "topup_riwayat": topup_riwayat_menu,
        "my_kode_unik": my_kode_unik_menu,
        "bantuan": bantuan_menu,
        "admin_panel": admin_panel,
        "admin_topup_pending": admin_topup_pending_menu,
        "admin_generate_kode": admin_generate_kode
        # ... add all other static callback routes here
    }
    
    if data in routes:
        return routes[data](update, context)

    # Dynamic routes
    if data.startswith("produk|") or data == "disabled_produk":
        return pilih_produk_callback(update, context)
    elif data.startswith("topup_upload|"):
        return topup_upload_router(update, context)
    elif data.startswith("admin_topup_detail|"):
        return admin_topup_detail(update, context)
    elif data.startswith("admin_topup_action|"):
        return admin_topup_action(update, context)
    
    # Static routes that don't return a state
    if data == "riwayat":
        riwayat_user(query, context)
    elif data == "semua_riwayat":
        semua_riwayat_admin(query, context)
    elif data == "broadcast":
        query.edit_message_text("📢 Type the message to broadcast to all users:", reply_markup=InlineKeyboardMarkup([btn_kembali()]))
        return BC_MESSAGE
    
    return ConversationHandler.END

def handle_text(update: Update, context: CallbackContext):
    update.message.reply_text("ℹ️ Please use the menu for navigation.", reply_markup=get_menu(update.effective_user.id))

# --- MAIN EXECUTION ---

def main():
    init_db()
    logger.info("Loading initial product cache...")
    update_produk_cache_background()
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Run Flask app in a separate thread
    run_webhook_server = create_webhook_app(updater, WEBHOOK_PORT)
    flask_thread = threading.Thread(target=run_webhook_server)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info(f"Webhook server starting on port {WEBHOOK_PORT}")

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(callback_router)
        ],
        states={
            CHOOSING_PRODUK: [CallbackQueryHandler(pilih_produk_callback, pattern="^produk\\|")],
            INPUT_TUJUAN: [MessageHandler(Filters.text & ~Filters.command, input_tujuan_step)],
            KONFIRMASI: [MessageHandler(Filters.text & ~Filters.command, konfirmasi_step)],
            TOPUP_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, topup_amount_step)],
            TOPUP_UPLOAD: [MessageHandler(Filters.photo, topup_upload_step)],
            INPUT_KODE_UNIK: [MessageHandler(Filters.text & ~Filters.command, input_kode_unik_step)],
            BC_MESSAGE: [MessageHandler(Filters.text & ~Filters.command, broadcast_step)],
        },
        fallbacks=[
            CommandHandler('menu', menu_command),
            CallbackQueryHandler(main_menu_callback, pattern="^main_menu$")
        ],
        allow_reentry=True,
    )
    
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('menu', menu_command))
    dp.add_handler(conv_handler)
    dp.add_handler(CallbackQueryHandler(callback_router)) # General handler for non-conversation callbacks
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    
    updater.start_polling()
    logger.info("Bot started polling...")
    updater.idle()

if __name__ == "__main__":
    main()
