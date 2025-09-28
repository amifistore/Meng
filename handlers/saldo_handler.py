from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext, ConversationHandler
from utils import get_user_saldo, tambah_user_saldo, load_riwayat
from markup import get_menu, is_admin

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
    # ... (isi fungsi, sama seperti sebelumnya)

def tambah_saldo_by_userid_input(update: Update, context: CallbackContext):
    # ... (isi fungsi, sama seperti sebelumnya)

# =============== FLOW 2: Tambah Saldo by Username ===============
def tambah_saldo_by_username_start(update: Update, context: CallbackContext):
    # ... (isi fungsi, sama seperti sebelumnya)

def tambah_saldo_by_username_input(update: Update, context: CallbackContext):
    # ... (isi fungsi, sama seperti sebelumnya)

# =============== FLOW 3: Pilih User dari Daftar ===============
def tambah_saldo_choose_user_start(update: Update, context: CallbackContext):
    # ... (isi fungsi, sama seperti sebelumnya)

def tambah_saldo_choose_user_input(update: Update, context: CallbackContext):
    # ... (isi fungsi, sama seperti sebelumnya)

# =============== Step Input Nominal (Common for all flows) ===============
def tambah_saldo_nominal_input(update: Update, context: CallbackContext):
    # ... (isi fungsi, sama seperti sebelumnya)

# =============== Alias untuk main.py ===============
tambah_saldo_callback = tambah_saldo_choose_user_start
