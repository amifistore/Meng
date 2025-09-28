from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext, ConversationHandler
from saldo import get_saldo_user, tambah_saldo_user, get_riwayat_saldo
from markup import get_menu, is_admin

# State untuk ConversationHandler
INPUT_SALDO_USERID, INPUT_SALDO_USERNAME, INPUT_SALDO_CHOOSE_USER, INPUT_SALDO_NOMINAL = range(4)

def lihat_saldo_callback(update: Update, context: CallbackContext):
    user = update.callback_query.from_user
    update.callback_query.answer()
    saldo = get_saldo_user(user.id)
    msg = f"💰 Saldo Anda saat ini: <b>Rp {saldo:,}</b>"
    update.callback_query.edit_message_text(
        msg,
        parse_mode="HTML",
        reply_markup=get_menu(user.id)
    )

# =============== FLOW: Pilih User dari Daftar (default) ===============
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
    # Ambil user-user yang pernah transaksi dari riwayat saldo DB
    riwayat_user = {}
    for row in get_riwayat_saldo(None, admin_mode=True):
        riwayat_user[row[1]] = True
    keyboard = []
    for user_id in riwayat_user.keys():
        keyboard.append([InlineKeyboardButton(f"UserID: {user_id}", callback_data=f"chooseuser|{user_id}")])
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

def tambah_saldo_nominal_input(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if not text.replace(".", "").replace(",", "").isdigit():
        update.message.reply_text("❌ Format nominal tidak valid. Masukkan nominal angka:", parse_mode="HTML")
        return INPUT_SALDO_NOMINAL
    nominal = int(text.replace(".", "").replace(",", ""))
    user_id = context.user_data.get('tambah_saldo_user_id')
    tambah_saldo_user(user_id, nominal, tipe="admin", keterangan="Tambah saldo manual admin")
    saldo = get_saldo_user(user_id)
    update.message.reply_text(
        f"✅ Saldo user <code>{user_id}</code> berhasil ditambah Rp {nominal:,}!\nSaldo sekarang: <b>Rp {saldo:,}</b>",
        parse_mode="HTML"
    )
    context.user_data.clear()
    return ConversationHandler.END

# =============== Penting: ALIAS UNTUK MAIN.PY ===============
tambah_saldo_callback = tambah_saldo_choose_user_start
