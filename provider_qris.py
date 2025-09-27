import requests

QRIS_API_URL = "https://qrisku.my.id/api"

def generate_qris(amount, qris_statis):
    """
    Generate QRIS dinamis dengan API qrisku.my.id

    Args:
        amount (int or str): Nominal QRIS
        qris_statis (str): String QRIS statis merchant

    Returns:
        dict: dict berisi status, message, dan qris_base64 jika sukses
    """
    payload = {
        "amount": str(amount),
        "qris_statis": qris_statis
    }
    try:
        response = requests.post(
            QRIS_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        return {
            "status": "error",
            "message": f"Exception: {str(e)}"
        }
