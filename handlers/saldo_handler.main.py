from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext, ConversationHandler
from utils import get_user_saldo, tambah_user_saldo, load_riwayat
from markup import get_menu, is_admin

# STATE untuk ConversationHandler
INPUT_SALDO_USERID, INPUT_SALDO_USERNAME, INPUT_SALDO_CHOOSE_USER, INPUT_SALDO_NOMINAL = range(4)


def lihat_saldo_callback(update: Update, context: CallbackContext):
    user = update.callback_query.from_user
    update.callback_query.answer()
    saldo = get_user_saldo(user.id)
    msg = f"💰 Saldo Anda saat ini: <b>Rp {saldo:,}</b>"
    update.callback_query.edit_message_text(
        msg,
        parse_mode="HTML",
        reply_markup=get_menu(user.id)
    )

# =============== FLOW 1: Tambah Saldo by User ID ===============
def tambah_saldo_by_userid_start(update: Update, context: CallbackContext):
    user = update.callback_query.from_user
    update.callback_query.answer()
    if not is_admin(user.id):
        update.callback_query.edit_message_text(
            "❌ Akses hanya untuk admin.",
            parse_mode="HTML",
            reply_markup=get_menu(user.id)
        )
        return ConversationHandler.END
    update.callback_query.edit_message_text(
        "🆔 Masukkan User ID Telegram yang ingin ditambah saldo:",
        parse_mode="HTML"
    )
    return INPUT_SALDO_USERID

def tambah_saldo_by_userid_input(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if not text.isdigit():
        update.message.reply_text("❌ Format User ID tidak valid. Masukkan angka User ID Telegram:", parse_mode="HTML")
        return INPUT_SALDO_USERID
    context.user_data['tambah_saldo_user_id'] = int(text)
    update.message.reply_text(
        "💵 Masukkan nominal saldo yang ingin ditambahkan:",
        parse_mode="HTML"
    )
    return INPUT_SALDO_NOMINAL

# =============== FLOW 2: Tambah Saldo by Username ===============
def tambah_saldo_by_username_start(update: Update, context: CallbackContext):
    user = update.callback_query.from_user
    update.callback_query.answer()
    if not is_admin(user.id):
        update.callback_query.edit_message_text(
            "❌ Akses hanya untuk admin.",
            parse_mode="HTML",
            reply_markup=get_menu(user.id)
        )
        return ConversationHandler.END
    update.callback_query.edit_message_text(
        "👤 Masukkan username Telegram user (tanpa @):",
        parse_mode="HTML"
    )
    return INPUT_SALDO_USERNAME

def tambah_saldo_by_username_input(update: Update, context: CallbackContext):
    username = update.message.text.strip().replace('@', '')
    all_riwayat = load_riwayat()
    found_user_id = None
    for user_id, trans_list in all_riwayat.items():
        for trx in trans_list:
            if trx.get("username", "").lower() == username.lower():
                found_user_id = int(user_id)
                break
        if found_user_id:
            break
    if not found_user_id:
        update.message.reply_text(
            "❌ Username tidak ditemukan di riwayat transaksi.\nPastikan user pernah bertransaksi.",
            parse_mode="HTML"
        )
        return INPUT_SALDO_USERNAME
    context.user_data['tambah_saldo_user_id'] = found_user_id
    update.message.reply_text(
        f"User ditemukan: <code>{username}</code> (ID: <code>{found_user_id}</code>)\nMasukkan nominal saldo yang ingin ditambahkan:",
        parse_mode="HTML"
    )
    return INPUT_SALDO_NOMINAL

# =============== FLOW 3: Pilih User dari Daftar ===============
def tambah_saldo_choose_user_start(update: Update, context: CallbackContext):
    user = update.callback_query.from_user
    update.callback_query.answer()
    if not is_admin(user.id):
        update.callback_query.edit_message_text(
            "❌ Akses hanya untuk admin.",
            parse_mode="HTML",
            reply_markup=get_menu(user.id)
        )
        return ConversationHandler.END
    all_riwayat = load_riwayat()
    keyboard = []
    for user_id, trans_list in all_riwayat.items():
        username = trans_list[-1].get("username", "unknown") if trans_list else "unknown"
        keyboard.append([InlineKeyboardButton(f"{username} ({user_id})", callback_data=f"chooseuser|{user_id}")])
    if not keyboard:
        update.callback_query.edit_message_text(
            "❌ Tidak ada user yang pernah bertransaksi.",
            parse_mode="HTML",
            reply_markup=get_menu(user.id)
        )
        return ConversationHandler.END
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(
        "👤 Pilih user yang ingin ditambah saldonya:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return INPUT_SALDO_CHOOSE_USER

def tambah_saldo_choose_user_input(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data
    if data.startswith("chooseuser|"):
        user_id = int(data.split("|")[1])
        context.user_data['tambah_saldo_user_id'] = user_id
        query.edit_message_text(
            f"User terpilih: <code>{user_id}</code>\nMasukkan nominal saldo yang ingin ditambahkan:",
            parse_mode="HTML"
        )
        return INPUT_SALDO_NOMINAL
    query.edit_message_text("❌ Pilihan tidak valid.", parse_mode="HTML")
    return ConversationHandler.END

# =============== Step Input Nominal (Common for all flows) ===============
def tambah_saldo_nominal_input(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if not text.replace(".", "").replace(",", "").isdigit():
        update.message.reply_text("❌ Format nominal tidak valid. Masukkan nominal angka:", parse_mode="HTML")
        return INPUT_SALDO_NOMINAL
    nominal = int(text.replace(".", "").replace(",", ""))
    user_id = context.user_data.get('tambah_saldo_user_id')
    tambah_user_saldo(user_id, nominal)
    saldo = get_user_saldo(user_id)
    update.message.reply_text(
        f"✅ Saldo user <code>{user_id}</code> berhasil ditambah Rp {nominal:,}!\nSaldo sekarang: <b>Rp {saldo:,}</b>",
        parse_mode="HTML"
    )
    context.user_data.clear()
    return ConversationHandler.END
