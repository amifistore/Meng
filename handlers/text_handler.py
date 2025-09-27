from telegram import ParseMode
from markup import get_menu, is_admin
from provider import history
from utils import get_user_saldo, set_user_saldo

def handle_text(update, context):
    if context.user_data:
        return
    text = update.message.text.strip()
    user = update.effective_user
    isadmin = is_admin(user.id)

    # CEK STATUS TRANSAKSI
    if text.startswith("CEK|"):
        try:
            refid = text.split("|", 1)[1].strip()
            if not refid:
                update.message.reply_text("❌ RefID tidak boleh kosong.", reply_markup=get_menu(user.id))
                return
            data = history(refid)
            if not data:
                update.message.reply_text("❌ Gagal cek status transaksi.", reply_markup=get_menu(user.id))
                return
            msg = f"🔍 Status transaksi <code>{refid}</code>:\n\n"
            for k, v in data.items():
                msg += f"<b>{k}</b>: {v}\n"
            update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
        except Exception as e:
            update.message.reply_text(f"❌ Error cek status: {str(e)}", reply_markup=get_menu(user.id))

    # ADMIN: TAMBAH SALDO USER SENDIRI
    elif text.startswith("TAMBAH|") and isadmin:
        try:
            tambah_text = text.split("|", 1)[1].strip()
            if not tambah_text:
                update.message.reply_text("❌ Nilai tidak boleh kosong.", reply_markup=get_menu(user.id))
                return
            tambah = int(tambah_text)
            saldo = get_user_saldo(user.id) + tambah
            set_user_saldo(user.id, saldo)
            update.message.reply_text(f"✅ Saldo ditambah. Saldo kamu sekarang: <b>Rp {saldo:,}</b>", parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
        except ValueError:
            update.message.reply_text("❌ Format nilai tidak valid.", reply_markup=get_menu(user.id))
        except Exception as e:
            update.message.reply_text(f"❌ Error: {str(e)}", reply_markup=get_menu(user.id))

    # ADMIN: TAMBAH SALDO USER LAIN (format TAMBAH|user_id|jumlah)
    elif text.startswith("TAMBAH|") and isadmin and "|" in text:
        try:
            parts = text.split("|")
            if len(parts) == 3:
                target_id = parts[1].strip()
                tambah = int(parts[2].strip())
                from utils import set_user_saldo, get_user_saldo
                saldo = get_user_saldo(target_id) + tambah
                set_user_saldo(target_id, saldo)
                update.message.reply_text(f"✅ Saldo user <code>{target_id}</code> ditambah. Saldo sekarang: <b>Rp {saldo:,}</b>", parse_mode=ParseMode.HTML, reply_markup=get_menu(user.id))
                return
        except ValueError:
            update.message.reply_text("❌ Format nilai tidak valid.", reply_markup=get_menu(user.id))
        except Exception as e:
            update.message.reply_text(f"❌ Error: {str(e)}", reply_markup=get_menu(user.id))

    # Perintah tidak dikenali
    else:
        update.message.reply_text(
            "❌ Perintah tidak dikenali. Gunakan menu di bawah.", 
            reply_markup=get_menu(user.id)
        )
