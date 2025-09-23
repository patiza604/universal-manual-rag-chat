#!/usr/bin/env python3
"""
Test the Firebase service specifically to ensure it can find and generate signed URLs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.firebase_service import FirebaseStorageService

def test_firebase_service():
    """Test Firebase service signed URL generation"""
    print("Testing Firebase Storage Service...")

    # Initialize service
    service = FirebaseStorageService()

    if not service.bucket:
        print("ERROR: Firebase service not initialized")
        return False

    print(f"Connected to bucket: {service.bucket.name}")

    # Test files that should exist
    test_files = [
        "internet_setup_wizard.png",
        "login_orbilogin_com.png",
        "modem_router_cabling.png",
        "satellite_sync_leds.png"
    ]

    success_count = 0

    for filename in test_files:
        print(f"\nTesting: {filename}")

        # Check if file exists
        exists = service.file_exists(filename)
        print(f"  File exists: {exists}")

        if exists:
            # Generate signed URL
            signed_url = service.generate_signed_url(filename)
            if signed_url:
                print(f"  SUCCESS: Signed URL generated: {signed_url[:80]}...")
                success_count += 1
            else:
                print(f"  FAILED: Failed to generate signed URL")
        else:
            print(f"  FAILED: File not found")

    print(f"\nResults: {success_count}/{len(test_files)} files successfully processed")
    return success_count == len(test_files)

if __name__ == "__main__":
    success = test_firebase_service()
    if success:
        print("\nSUCCESS: Firebase service is working correctly!")
    else:
        print("\nFAILED: Firebase service has issues")
    sys.exit(0 if success else 1)