import requests
import json
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
        import uuid
        if not reff_id:
            # Gunakan UUID versi panjang untuk tracking, best practice
            reff_id = str(uuid.uuid4())
        url = f"{BASE_URL}/trx"
        params = {
            "produk": produk,
            "tujuan": tujuan,
            "reff_id": reff_id,
            "api_key": API_KEY
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # Kembalikan reff_id agar bisa di-track di database internal
        data["reff_id"] = reff_id
        return data
    except Exception as e:
        print("Error create_trx:", e)
        return {"status": "error", "message": str(e)}

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
        # Jika endpoint akrab tidak butuh API_KEY, hapus params di bawah
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return resp.text
    except Exception as e:
        print("Error cek_stock_akrab:", e)
        return {"status": "error", "message": str(e)}
