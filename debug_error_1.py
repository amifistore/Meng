# debug_error_1.py
import logging
import traceback

# Setup logging untuk debug
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def debug_all_modules():
    """Test semua module untuk menemukan error"""
    print("=== DEBUGGING ERROR CODE 1 ===")
    
    modules_to_test = [
        'saldo',
        'riwayat', 
        'topup',
        'markup',
        'provider'
    ]
    
    for module_name in modules_to_test:
        try:
            print(f"\n🔍 Testing {module_name}...")
            module = __import__(module_name)
            print(f"✅ {module_name} imported successfully")
            
            # Test fungsi utama jika ada
            if module_name == 'saldo':
                from saldo import get_saldo_user
                result = get_saldo_user(123456789)
                print(f"✅ saldo.get_saldo_user: {result}")
                
            elif module_name == 'riwayat':
                from riwayat import get_riwayat_user
                result = get_riwayat_user(123456789)
                print(f"✅ riwayat.get_riwayat_user: {len(result)} records")
                
        except Exception as e:
            print(f"❌ Error in {module_name}: {e}")
            traceback.print_exc()
    
    print("\n=== DEBUG COMPLETED ===")

if __name__ == "__main__":
    debug_all_modules()
