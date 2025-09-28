import base64
import random
import uuid
import time
from io import BytesIO
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import ConversationHandler
from provider_qris import generate_qris
from PIL import Image

from saldo import tambah_saldo_user
from topup import (
    simpan_topup, update_status_topup, get_topup_by_id,
    get_topup_pending_list
)

TOPUP_NOMINAL = 3

ADMIN_IDS = [7366367635, 6738243352]  # Isi dengan list chat_id admin

QRIS_TEMPLATE_PATH = "qris_template.png"
QRIS_STATIS = "00020101021126610014COM.GO-JEK.WWW01189360091434506469550210G4506469550303UMI51440014ID.CO.QRIS.WWW0215ID10243341364120303UMI5204569753033605802ID5923Amifi Store, Kmb, TLGSR6009BONDOWOSO61056827262070703A01630431E8"

def log_topup_error(error_text):
    with open("topup_error.log", "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_text}\n")

def log_admin_action(admin_id, action, target_id, topup_id, detail=""):
    with open("admin_action.log", "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ADMIN:{admin_id} ACTION:{action} TARGET:{target_id} TOPUP_ID:{topup_id} {detail}\n")

def get_nominal_unik(nominal, min_unik=1, max_unik=99):
    kode_unik = random.randint(min_unik, max_unik)
    return nominal + kode_unik, kode_unik

def make_qris_image(qris_base64, template_path=QRIS_TEMPLATE_PATH):
    try:
        qr_bytes = base64.b64decode(qris_base64)
        qr_img = Image.open(BytesIO(qr_bytes)).convert("RGBA")
        template = Image.open(template_path).convert("RGBA")
        qr_size = (300, 300)
        qr_img = qr_img.resize(qr_size)
        pos = ((template.width - qr_size[0]) // 2, 430)
        template.paste(qr_img, pos, qr_img)
        output = BytesIO()
        template.save(output, format="PNG")
        output.name = "qris_final.png"
        output.seek(0)
        return output
    except Exception as e:
        log_topup_error(f"make_qris_image error: {e}")
        return None

def safe_edit_message(query, new_text, reply_markup=None, parse_mode=None):
    try:
        prev_text = query.message.text if query.message and query.message.text else ""
        prev_markup = query.message.reply_markup if query.message else None
        if prev_text == new_text and str(prev_markup) == str(reply_markup):
            return
        query.edit_message_text(new_text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        if "Message is not modified" in str(e):
            pass
        else:
            log_topup_error(f"safe_edit_message error: {str(e)}")

def topup_callback(update, context):
    query = update.callback_query
    if query: query.answer()
    unique = int(time.time())
    new_text = (
        "💸 Silakan masukkan nominal Top Up (minimal 10.000):\n\n"
        "Contoh: <code>25000</code>\n"
        f"Kode unik: <code>{unique}</code>"
    )
    safe_edit_message(query, new_text, parse_mode="HTML")
    return TOPUP_NOMINAL

def notify_admin_topup(context, user, nominal, total_bayar, kode_unik, topup_id):
    try:
        text = (
            f"💸 <b>TOP UP BARU</b>\n"
            f"User: <code>{user.id}</code> ({user.full_name})\n"
            f"Username: @{user.username}\n"
            f"Nominal: <b>Rp {nominal:,}</b>\n"
            f"Total bayar (kode unik): <b>Rp {total_bayar:,}</b> (unik: <b>{kode_unik:02d}</b>)\n"
            f"TopUp ID: <code>{topup_id}</code>\n"
            f"Waktu: <code>{time.strftime('%Y-%m-%d %H:%M:%S')}</code>\n"
            "🔔 Menunggu user upload bukti transfer.\n"
            "<b>Aksi Admin:</b>"
        )
        buttons = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"topup_approve|{topup_id}|{user.id}"),
                InlineKeyboardButton("❌ Batal", callback_data=f"topup_batal|{topup_id}|{user.id}")
            ]
        ]
        for admin_id in ADMIN_IDS:
            context.bot.send_message(
                chat_id=admin_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode="HTML"
            )
    except Exception as e:
        log_topup_error(f"notify_admin_topup error: {e}")

def topup_nominal_step(update, context):
    try:
        text = ""
        if update.message and update.message.text:
            text = update.message.text.strip()
        else:
            log_topup_error("topup_nominal_step: update.message or text is None")
            update.message.reply_text("❌ Format nominal tidak valid. Masukkan angka:")
            return TOPUP_NOMINAL

        try:
            nominal = int(text.replace(".", "").replace(",", ""))
        except Exception as ve:
            log_topup_error(f"Nominal format error: {str(ve)}")
            update.message.reply_text("❌ Format nominal tidak valid. Masukkan angka:")
            return TOPUP_NOMINAL

        if nominal < 10000:
            update.message.reply_text("❌ Nominal minimal 10.000. Masukkan kembali nominal:")
            return TOPUP_NOMINAL

        total_bayar, kode_unik = get_nominal_unik(nominal)
        try:
            resp = generate_qris(total_bayar, QRIS_STATIS)
        except Exception as e:
            log_topup_error(f"generate_qris error: {str(e)}")
            update.message.reply_text(f"❌ Error generate QRIS: {str(e)}")
            return ConversationHandler.END

        if resp.get("status") != "success":
            log_topup_error(f"QRIS failed: {resp}")
            update.message.reply_text(f"❌ Gagal generate QRIS: {resp.get('message', 'Unknown error')}")
            return ConversationHandler.END

        qris_base64 = resp.get("qris_base64")
        msg = (
            f"💰 Silakan lakukan pembayaran Top Up sebesar <b>Rp {total_bayar:,}</b>\n"
            f"(Nominal unik: <b>{kode_unik:02d}</b>)\n"
            "Scan QRIS berikut (aktif 15 menit).\n\n"
            "Setelah bayar, kirim bukti transfer dan tunggu konfirmasi admin."
        )
        # Kirim QRIS ke user
        if qris_base64:
            try:
                img = make_qris_image(qris_base64)
                if img:
                    update.message.reply_photo(photo=img, caption=msg, parse_mode="HTML")
                else:
                    try:
                        qr_bytes = base64.b64decode(qris_base64)
                        bio = BytesIO(qr_bytes)
                        bio.name = "qris.png"
                        bio.seek(0)
                        update.message.reply_photo(photo=bio, caption=msg, parse_mode="HTML")
                    except Exception as e:
                        log_topup_error(f"Error decode QRIS: {str(e)}")
                        update.message.reply_text(f"❌ Error decode QRIS: {str(e)}")
            except Exception as e:
                log_topup_error(f"Send QRIS image error: {str(e)}")
                update.message.reply_text(f"❌ Error kirim gambar QRIS: {str(e)}")
        else:
            log_topup_error("QRIS base64 kosong")
            update.message.reply_text(msg + "\n❌ QRIS tidak tersedia", parse_mode="HTML")

        # === Simpan ke database ===
        topup_id = str(uuid.uuid4())
        simpan_topup(topup_id, update.effective_user.id, nominal, status="pending")
        # === NOTIFIKASI ADMIN + TOMBOL ===
        notify_admin_topup(
            context,
            update.effective_user,
            nominal,
            total_bayar,
            kode_unik,
            topup_id,
        )

    except Exception as e:
        log_topup_error(f"topup_nominal_step error: {str(e)}")
        try:
            update.message.reply_text(f"❌ Error: {str(e)}")
        except Exception:
            pass
    return ConversationHandler.END

def admin_topup_callback(update, context):
    query = update.callback_query
    query.answer()
    data = query.data
    admin_id = query.from_user.id

    if data.startswith("topup_approve|"):
        _, topup_id, user_id = data.split("|")
        t = get_topup_by_id(topup_id)
        if t and t['status'] == "pending":
            tambah_saldo_user(t['user_id'], t['nominal'], tipe="topup", keterangan=f"TOPUP {topup_id}")
            update_status_topup(topup_id, "approved", admin_id)
            query.edit_message_text("✅ Top Up telah di-approve admin.", parse_mode="HTML")
            try:
                context.bot.send_message(
                    chat_id=int(user_id),
                    text=f"✅ Top Up kamu telah diapprove admin! Saldo masuk Rp {t['nominal']:,}.",
                    parse_mode="HTML"
                )
            except Exception as e:
                log_topup_error(f"ERROR kirim ke user: {e}")
        else:
            query.edit_message_text("❌ Top Up tidak ditemukan atau sudah diproses.", parse_mode="HTML")

    elif data.startswith("topup_batal|"):
        _, topup_id, user_id = data.split("|")
        t = get_topup_by_id(topup_id)
        if t and t['status'] == "pending":
            update_status_topup(topup_id, "canceled", admin_id)
            query.edit_message_text("❌ Top Up dibatalkan oleh admin.", parse_mode="HTML")
            try:
                context.bot.send_message(
                    chat_id=int(user_id),
                    text=f"❌ Top Up kamu dibatalkan admin. Silakan ulangi jika ingin coba lagi.",
                    parse_mode="HTML"
                )
            except Exception as e:
                log_topup_error(f"ERROR kirim ke user: {e}")
        else:
            query.edit_message_text("❌ Top Up tidak ditemukan atau sudah diproses.", parse_mode="HTML")

def admin_topup_list_callback(update, context):
    query = update.callback_query
    user = query.from_user
    query.answer()

    if user.id not in ADMIN_IDS:
        query.edit_message_text("❌ Kamu bukan admin.")
        return

    topup_list = get_topup_pending_list()

    if not topup_list:
        query.edit_message_text("Tidak ada transaksi top up pending.")
        return

    msg = "<b>🧾 Daftar Pending Top Up User:</b>\nPilih transaksi untuk approve/batal.\n\n"
    keyboard = []
    for t in topup_list:
        label = f"{t.get('id','-')} | Rp {t.get('nominal',0):,} | UserID: {t.get('user_id','-')}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"admin_topup_detail|{t['id']}")])
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_admin")])
    query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

def admin_topup_detail_callback(update, context):
    query = update.callback_query
    topup_id = query.data.split("|")[1]
    t = get_topup_by_id(topup_id)
    if not t:
        query.edit_message_text("❌ Top up tidak ditemukan.")
        return
    msg = (
        f"<b>💸 Detail Top Up</b>\n"
        f"ID: <code>{t.get('id')}</code>\n"
        f"User: <code>{t.get('user_id')}</code>\n"
        f"Nominal: <b>Rp {t.get('nominal'):,}</b>\n"
        f"Waktu: <code>{t.get('waktu')}</code>\n"
        f"Status: <b>{t.get('status','pending')}</b>\n\n"
        "Aksi admin:"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Approve", callback_data=f"topup_approve|{topup_id}|{t.get('user_id')}"),
         InlineKeyboardButton("❌ Cancel", callback_data=f"topup_batal|{topup_id}|{t.get('user_id')}")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="riwayat_topup_admin")]
    ]
    query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
