import requests
import logging
from config import PROVIDER_API_KEY, PROVIDER_BASE_URL

logger = logging.getLogger(__name__)

def get_produk_list():
    """Ambil daftar produk dari provider"""
    try:
        url = f"{PROVIDER_BASE_URL}/api_v2/list_product"
        params = {
            'api_key': PROVIDER_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'success':
            products = data.get('data', [])
            logger.info(f"Successfully parsed {len(products)} products from provider")
            
            # Format produk sesuai kebutuhan bot
            formatted_products = []
            for product in products:
                formatted_products.append({
                    'kode': product.get('kode', ''),
                    'nama': product.get('nama', ''),
                    'harga': int(product.get('harga', 0)),
                    'kuota': int(product.get('kuota', 0)),
                    'keterangan': product.get('keterangan', ''),
                    'kategori': product.get('kategori', '')
                })
            
            return formatted_products
        else:
            logger.error(f"Provider error: {data.get('message', 'Unknown error')}")
            return []
            
    except Exception as e:
        logger.error(f"Error getting product list: {e}")
        # Fallback ke produk static jika provider down
        return get_fallback_products()

def create_trx(product_code, target, ref_id=None):
    """Buat transaksi baru di provider"""
    try:
        url = f"{PROVIDER_BASE_URL}/api_v2/trx"
        params = {
            'produk': product_code,
            'tujuan': target,
            'reff_id': ref_id,
            'api_key': PROVIDER_API_KEY
        }
        
        logger.info(f"Creating transaction: {product_code} for {target} with ref {ref_id}")
        
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'success':
            result = {
                'success': True,
                'trx_id': data.get('trxid', ''),
                'ref_id': data.get('refid', ref_id),
                'message': data.get('message', 'Transaction created successfully'),
                'data': data.get('data', {})
            }
            logger.info(f"Transaction created successfully: {result}")
            return result
        else:
            error_msg = data.get('message', 'Unknown error from provider')
            logger.error(f"Provider transaction error: {error_msg}")
            return {
                'success': False,
                'message': error_msg,
                'trx_id': '',
                'ref_id': ref_id
            }
            
    except requests.exceptions.Timeout:
        error_msg = "Provider timeout - transaction pending"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'trx_id': '',
            'ref_id': ref_id
        }
    except Exception as e:
        error_msg = f"Error creating transaction: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'trx_id': '',
            'ref_id': ref_id
        }

def check_transaction_status(ref_id):
    """Cek status transaksi by ref_id"""
    try:
        url = f"{PROVIDER_BASE_URL}/api_v2/history"
        params = {
            'api_key': PROVIDER_API_KEY,
            'refid': ref_id
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'success':
            return {
                'success': True,
                'status': data.get('data', {}).get('status', 'unknown'),
                'message': data.get('message', ''),
                'data': data.get('data', {})
            }
        else:
            return {
                'success': False,
                'status': 'error',
                'message': data.get('message', 'Unknown error')
            }
            
    except Exception as e:
        logger.error(f"Error checking transaction status: {e}")
        return {
            'success': False,
            'status': 'error',
            'message': str(e)
        }

def cek_stock_akrab():
    """Cek stock akrab XL/Axis"""
    try:
        url = f"{PROVIDER_BASE_URL}/api_v3/cek_stock_akrab"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except Exception as e:
        logger.error(f"Error checking akrab stock: {e}")
        return {'status': 'error', 'message': str(e)}

def get_fallback_products():
    """Fallback products jika provider down"""
    logger.info("Using fallback products")
    return [
        {
            'kode': 'BPAL1',
            'nama': 'Bonus Akrab L - 1 hari',
            'harga': 10000,
            'kuota': 999,
            'keterangan': 'Bonus Akrab L 1 hari',
            'kategori': 'akrab'
        },
        {
            'kode': 'BPAL11', 
            'nama': 'Bonus Akrab L - 11 hari',
            'harga': 25000,
            'kuota': 999,
            'keterangan': 'Bonus Akrab L 11 hari',
            'kategori': 'akrab'
        },
        # Tambahkan produk lainnya...
    ]
