# debug_comparison.py
import traceback
import sys

def debug_comparison():
    """Debug untuk menemukan sumber error perbandingan"""
    try:
        # Test semua kemungkinan sumber error
        from saldo import get_saldo_user, kurang_saldo_user, tambah_saldo_user
        
        test_user = 123456789
        
        print("=== DEBUGGING COMPARISON ERROR ===")
        
        # Test 1: get_saldo_user
        saldo = get_saldo_user(test_user)
        print(f"1. get_saldo_user: {saldo} (type: {type(saldo)})")
        
        # Test 2: tambah_saldo_user dengan string
        print("2. Testing tambah_saldo_user dengan string '50000'...")
        result = tambah_saldo_user(test_user, "50000", "test", "debug")
        print(f"   Result: {result}")
        
        # Test 3: kurang_saldo_user dengan string
        print("3. Testing kurang_saldo_user dengan string '20000'...")
        result = kurang_saldo_user(test_user, "20000", "test", "debug")
        print(f"   Result: {result}")
        
        print("✅ All tests passed - no comparison error")
        
    except Exception as e:
        print(f"❌ Error found: {e}")
        print("🔍 Stack trace:")
        traceback.print_exc()

if __name__ == "__main__":
    debug_comparison()
