import requests
import json
import uuid
from config import API_KEY, BASE_URL, BASE_URL_AKRAB

def list_product():
    try:
        url = f"{BASE_URL}/list_product"
        params = {"api_key": API_KEY}
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # Sesuaikan dengan struktur response, jika ada "data"
        return data.get("data", data) if isinstance(data, dict) else []
    except Exception as e:
        print("Error list_product:", e)
        return []

def create_trx(produk, tujuan, reff_id=None):
    try:
        if not reff_id:
            reff_id = str(uuid.uuid4())
            
        url = f"{BASE_URL}/trx"
        params = {
            "produk": produk,
            "tujuan": tujuan,
            "reff_id": reff_id,  # ✅ DIPERBAIKI: reff_id bukan reff_id
            "api_key": API_KEY
        }
        
        print(f"[DEBUG] Request to provider: {params}")  # Log untuk debug
        
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        # ✅ VALIDASI RESPONSE STRUCTURE
        if not isinstance(data, dict):
            raise ValueError("Response dari provider bukan format JSON yang valid")
            
        # ✅ TAMBAHKAN FIELD YANG DIPERLUKAN
        data["reff_id"] = reff_id  # Pastikan reff_id ada di response
        
        print(f"[DEBUG] Provider response: {data}")  # Log response
        
        return data
        
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "Timeout: Provider tidak merespons", "reff_id": reff_id}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "Koneksi gagal ke provider", "reff_id": reff_id}
    except requests.exceptions.HTTPError as e:
        return {"status": "error", "message": f"HTTP Error: {e}", "reff_id": reff_id}
    except Exception as e:
        print(f"Error create_trx: {e}")
        return {"status": "error", "message": str(e), "reff_id": reff_id}

def history(refid):
    try:
        url = f"{BASE_URL}/history"
        params = {
            "api_key": API_KEY,
            "refid": refid
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data
    except Exception as e:
        print("Error history:", e)
        return {"status": "error", "message": str(e)}

def cek_stock_akrab():
    try:
        url = f"{BASE_URL_AKRAB}/cek_stock_akrab"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return resp.text
    except Exception as e:
        print("Error cek_stock_akrab:", e)
        return {"status": "error", "message": str(e)}
