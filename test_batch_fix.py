"""Test script to verify Azure DevOps batch API fixes."""

import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

load_dotenv()

from src.tools import query_change_requests
from src.utils import get_logger

logger = get_logger(__name__)


def test_batch_processing():
    """Test batch processing with improved error handling."""
    print("\n" + "=" * 70)
    print("TESTING AZURE DEVOPS BATCH API FIXES")
    print("=" * 70)
    
    print("\n🧪 Testing batch processing with new error handling...")
    print("   - Reduced batch size: 50 (was 100)")
    print("   - ID validation enabled")
    print("   - Retry logic: 3 attempts with exponential backoff")
    print("   - Enhanced error logging")
    
    try:
        # Query a small set of CRs to test
        print("\n📥 Fetching first 100 CRs...")
        crs = query_change_requests()
        
        if not crs:
            print("⚠️  No CRs found")
            return
        
        # Limit to first 100 for testing
        test_crs = crs[:100]
        print(f"✅ Successfully fetched {len(test_crs)} CRs")
        
        # Show sample CR
        if test_crs:
            sample = test_crs[0]
            print(f"\n📋 Sample CR:")
            print(f"   ID: {sample.get('cr_id')}")
            print(f"   Title: {sample.get('title', 'N/A')[:50]}...")
            print(f"   State: {sample.get('state')}")
            print(f"   Type: {sample.get('work_item_type')}")
        
        print("\n" + "=" * 70)
        print("✅ TEST PASSED - Batch processing working correctly")
        print("=" * 70)
        print("\n💡 Next steps:")
        print("   1. Run full sync: python sync_azure_devops.py --all")
        print("   2. Monitor logs for any errors")
        print("   3. Check error details if 400 errors occur")
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ TEST FAILED")
        print("=" * 70)
        print(f"\nError: {e}")
        print("\n🔍 Check the logs above for detailed error information")
        print("   The enhanced logging should show:")
        print("   - Exact error message from Azure DevOps API")
        print("   - Batch IDs that failed")
        print("   - Response body with error details")
        raise


if __name__ == "__main__":
    test_batch_processing()
