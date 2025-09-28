# webhook_server.py
# Description: Flask web server to handle incoming webhooks from the transaction API.

import re
import logging
from flask import Flask, request, jsonify
from telegram import ParseMode

# Import database functions
from database import get_riwayat_by_refid, update_riwayat_status, tambah_saldo, kurang_saldo, get_saldo
from markup import get_menu

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

            info_text, markup = get_menu(user_id)

            if "sukses" in status_text.lower():
                try:
                    updater.bot.send_message(
                        user_id, 
                        f"✅ <b>TRANSAKSI SUKSES</b>\n\n"
                        f"Produk: [{produk_kode}] dengan harga Rp {harga:,} telah berhasil dikirim.\n"
                        f"Keterangan: {keterangan}\n\n"
                        f"Saldo Anda sekarang: Rp {get_saldo(user_id):,}",
                        parse_mode=ParseMode.HTML,
                        reply_markup=markup
                    )
                except Exception as e:
                    logger.error(f"Failed to send success notification to user {user_id}: {e}")
            
            elif "gagal" in status_text.lower() or "batal" in status_text.lower():
                tambah_saldo(user_id, harga)
                try:
                    updater.bot.send_message(
                        user_id, 
                        f"❌ <b>TRANSAKSI GAGAL</b>\n\n"
                        f"Transaksi untuk produk [{produk_kode}] dengan harga Rp {harga:,} GAGAL.\n"
                        f"Keterangan: {keterangan}\n\n"
                        f"Saldo Anda telah dikembalikan. Saldo sekarang: Rp {get_saldo(user_id):,}",
                        parse_mode=ParseMode.HTML,
                        reply_markup=markup
                    )
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
