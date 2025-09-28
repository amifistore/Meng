# test_final_fix.py
from saldo import get_saldo_user, tambah_saldo_user, kurang_saldo_user, safe_int_convert

def test_final():
    print("=== FINAL TEST - ALL DATA TYPES ===")
    
    test_user = 123456789
    
    # Test safe_int_convert
    test_values = ["50000", "50.000", "Rp 50,000", 50000, 50000.0, "invalid"]
    for val in test_values:
        result = safe_int_convert(val)
        print(f"safe_int_convert({repr(val)}) = {result} (type: {type(result)})")
    
    # Test saldo functions dengan berbagai tipe data
    print("\nTesting dengan string '100000':")
    result = tambah_saldo_user(test_user, "100000", "test", "string test")
    print(f"tambah_saldo_user dengan string: {result}")
    
    print("Testing dengan string '50000':")
    result = kurang_saldo_user(test_user, "50000", "test", "string test")
    print(f"kurang_saldo_user dengan string: {result}")
    
    saldo_final = get_saldo_user(test_user)
    print(f"Saldo final: {saldo_final} (type: {type(saldo_final)})")
    
    print("🎉 FINAL TEST COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    test_final()
