#!/usr/bin/env python3
"""
Simple test script to verify Firebase Storage image access
"""

import os
import sys
from google.cloud import storage
from google.oauth2 import service_account

def test_firebase_images():
    """Test Firebase Storage image access"""
    print("Testing Firebase Storage image access...")

    # Initialize Firebase Storage
    key_path = "gcp-keys/ai-chatbot-472322-firebase-storage.json"
    if not os.path.exists(key_path):
        print(f"ERROR: Service account key not found: {key_path}")
        return False

    try:
        credentials = service_account.Credentials.from_service_account_file(key_path)
        client = storage.Client(credentials=credentials)
        bucket_name = "ai-chatbot-472322.firebasestorage.app"
        bucket = client.bucket(bucket_name)

        print(f"Connected to bucket: {bucket_name}")

        # List images in ai_images/manual001/ folder
        blobs = list(bucket.list_blobs(prefix="ai_images/manual001/"))
        print(f"Found {len(blobs)} images:")

        for blob in blobs:
            print(f"  - {blob.name} ({blob.size} bytes)")

            # Generate signed URL
            try:
                from datetime import timedelta
                signed_url = blob.generate_signed_url(
                    version='v4',
                    expiration=timedelta(hours=1),
                    method='GET'
                )
                print(f"    Signed URL: {signed_url[:100]}...")

            except Exception as e:
                print(f"    Error generating signed URL: {e}")

        return len(blobs) > 0

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_firebase_images()
    if success:
        print("\nSUCCESS: Firebase Storage images are accessible!")
    else:
        print("\nFAILED: Could not access Firebase Storage images")
    sys.exit(0 if success else 1)