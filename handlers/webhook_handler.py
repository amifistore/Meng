# webhook_handler.py
import logging
import re
from riwayat import update_order_status

logger = logging.getLogger(__name__)

def parse_webhook_message(message):
    """Parse webhook message dari provider"""
    # Regex sesuai dokumentasi provider
    pattern = r'RC=(?P<reffid>[a-f0-9-]+)\s+TrxID=(?P<trxid>\d+)\s+(?P<produk>[A-Z0-9]+)\.(?P<tujuan>\d+)\s+(?P<status_text>[A-Za-z]+)\s*(?P<keterangan>.+?)(?:\s+Saldo[\s\S]*?)?(?:\bresult=(?P<status_code>\d+))?\s*>?$'
    
    match = re.match(pattern, message, re.IGNORECASE)
    if not match:
        logger.error(f"Webhook format tidak dikenali: {message}")
        return None
    
    groups = match.groupdict()
    
    # Normalize status
    status_code = groups.get('status_code')
    if status_code is None:
        if 'sukses' in groups.get('status_text', '').lower():
            status_code = '0'
        elif 'gagal' in groups.get('status_text', '').lower() or 'batal' in groups.get('status_text', '').lower():
            status_code = '1'
    
    return {
        'ref_id': groups.get('reffid'),
        'trx_id': groups.get('trxid'),
        'product': groups.get('produk'),
        'target': groups.get('tujuan'),
        'status_text': groups.get('status_text'),
        'status_code': status_code,
        'keterangan': groups.get('keterangan', '').strip()
    }

async def handle_webhook(message):
    """Handle incoming webhook dari provider"""
    try:
        parsed_data = parse_webhook_message(message)
        if not parsed_data:
            return {'success': False, 'error': 'Format tidak dikenali'}
        
        logger.info(f"📨 Webhook received: {parsed_data}")
        
        # Update status order di database
        status_map = {
            '0': 'success',
            '1': 'failed'
        }
        
        new_status = status_map.get(parsed_data['status_code'], 'pending')
        
        # Update di riwayat_order table
        update_result = await update_order_status(
            parsed_data['ref_id'],
            new_status,
            parsed_data['trx_id'],
            parsed_data['keterangan']
        )
        
        if new_status == 'success':
            logger.info(f"✅ Order {parsed_data['ref_id']} SUCCESS")
            # TODO: Notify user via Telegram
        elif new_status == 'failed':
            logger.info(f"❌ Order {parsed_data['ref_id']} FAILED")
            # TODO: Refund saldo dan notify user
            
        return {
            'success': True,
            'parsed': parsed_data,
            'updated': update_result
        }
        
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return {'success': False, 'error': str(e)}
