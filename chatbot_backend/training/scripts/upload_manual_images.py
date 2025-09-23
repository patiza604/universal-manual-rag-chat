#!/usr/bin/env python3
"""
Manual Image Upload Script

If the automatic PDF extraction doesn't work perfectly, use this script to
manually upload images to Firebase Storage with the correct names.
"""

import os
import sys
from pathlib import Path
import logging
from typing import Dict

try:
    from google.cloud import storage
except ImportError as e:
    print(f"Missing Firebase packages: {e}")
    print("Please install: pip install google-cloud-storage")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ManualImageUploader:
    """Upload images manually to Firebase Storage"""

    def __init__(self, bucket_name: str = "ai-chatbot-472322.firebasestorage.app"):
        self.bucket_name = bucket_name
        self.storage_client = None
        self.bucket = None
        self._initialize_firebase()

        # Expected images mapping - using correct ai_images/manual001/ path
        self.firebase_paths = {
            "orbi_router_front_back.png": "ai_images/manual001/orbi_router_front_back.png",
            "orbi_satellite_front_back.png": "ai_images/manual001/orbi_satellite_front_back.png",
            "modem_router_cabling.png": "ai_images/manual001/modem_router_cabling.png",
            "satellite_sync_leds.png": "ai_images/manual001/satellite_sync_leds.png",
            "label_qr_example.png": "ai_images/manual001/label_qr_example.png",
            "internet_setup_wizard.png": "ai_images/manual001/internet_setup_wizard.png",
            "ap_mode_settings.png": "ai_images/manual001/ap_mode_settings.png",
            "firmware_update_satellite_router.png": "ai_images/manual001/firmware_update_satellite_router.png",
            "wan_aggregation_diagram.png": "ai_images/manual001/wan_aggregation_diagram.png",
            "login_orbilogin_com.png": "ai_images/manual001/login_orbilogin_com.png",
            "led_quick_reference_table.png": "ai_images/manual001/led_quick_reference_table.png",
            "factory_reset_button.png": "ai_images/manual001/factory_reset_button.png",
            "tech_specs_tables.png": "ai_images/manual001/tech_specs_tables.png"
        }

    def _initialize_firebase(self):
        """Initialize Firebase Storage client"""
        try:
            logger.info("Initializing Firebase Storage client...")

            # Try to use service account key file
            key_paths = [
                "gcp-keys/ai-chatbot-472322-firebase-storage.json",
                "gcp-keys/ai-chatbot-beb8d-firebase-adminsdk-fbsvc-c2ce8b36f1.json",
                "gcp-keys/service-account-key.json"
            ]

            credentials = None
            for key_path in key_paths:
                if os.path.exists(key_path):
                    logger.info(f"Using service account key: {key_path}")
                    from google.oauth2 import service_account
                    credentials = service_account.Credentials.from_service_account_file(key_path)
                    break

            if credentials:
                self.storage_client = storage.Client(credentials=credentials)
            else:
                logger.info("No service account key found, using default credentials")
                self.storage_client = storage.Client()

            self.bucket = self.storage_client.bucket(self.bucket_name)

            if self.bucket.exists():
                logger.info(f"✅ Connected to Firebase bucket: {self.bucket_name}")
            else:
                logger.error(f"❌ Bucket {self.bucket_name} does not exist")
                self.bucket = None

        except Exception as e:
            logger.error(f"❌ Failed to initialize Firebase Storage: {e}")
            self.storage_client = None
            self.bucket = None

    def upload_image(self, local_path: str, target_filename: str) -> bool:
        """Upload a single image to Firebase Storage"""
        if not self.bucket:
            logger.error("Firebase Storage not available")
            return False

        if target_filename not in self.firebase_paths:
            logger.error(f"Unknown target filename: {target_filename}")
            logger.info(f"Available options: {list(self.firebase_paths.keys())}")
            return False

        if not os.path.exists(local_path):
            logger.error(f"Local file not found: {local_path}")
            return False

        try:
            firebase_path = self.firebase_paths[target_filename]
            blob = self.bucket.blob(firebase_path)

            logger.info(f"Uploading {local_path} -> {firebase_path}")

            # Determine content type
            content_type = 'image/png'
            if local_path.lower().endswith('.jpg') or local_path.lower().endswith('.jpeg'):
                content_type = 'image/jpeg'

            with open(local_path, 'rb') as f:
                blob.upload_from_file(f, content_type=content_type)

            # Set metadata
            blob.metadata = {
                'original_filename': os.path.basename(local_path),
                'target_filename': target_filename,
                'uploaded_manually': 'true'
            }
            blob.patch()

            logger.info(f"✅ Upload successful: {firebase_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return False

    def upload_directory(self, directory_path: str) -> Dict[str, bool]:
        """Upload all matching images from a directory"""
        if not os.path.exists(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return {}

        results = {}
        image_extensions = {'.png', '.jpg', '.jpeg'}

        # Find all image files in directory
        for file_path in Path(directory_path).iterdir():
            if file_path.suffix.lower() in image_extensions:
                filename = file_path.name

                # Try to match to expected filenames
                for target_filename in self.firebase_paths:
                    target_base = target_filename.replace('.png', '')
                    file_base = filename.lower().replace('.png', '').replace('.jpg', '').replace('.jpeg', '')

                    # Simple matching - you can make this more sophisticated
                    if target_base.lower() in file_base or file_base in target_base.lower():
                        logger.info(f"Potential match: {filename} -> {target_filename}")
                        success = self.upload_image(str(file_path), target_filename)
                        results[target_filename] = success
                        break

        return results

    def list_uploaded_images(self):
        """List all uploaded images in the manual001/ folder"""
        if not self.bucket:
            logger.error("Firebase Storage not available")
            return

        try:
            blobs = self.bucket.list_blobs(prefix="ai_images/manual001/")
            uploaded_images = []

            for blob in blobs:
                uploaded_images.append({
                    'name': blob.name,
                    'size': blob.size,
                    'created': blob.time_created
                })

            if uploaded_images:
                logger.info(f"Found {len(uploaded_images)} images in Firebase Storage:")
                for img in uploaded_images:
                    logger.info(f"  {img['name']} ({img['size']} bytes)")
            else:
                logger.info("No images found in ai_images/manual001/ folder")

            return uploaded_images

        except Exception as e:
            logger.error(f"Error listing images: {e}")
            return []

def main():
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Upload single image: python upload_manual_images.py <image_path> <target_filename>")
        print("  Upload directory: python upload_manual_images.py --directory <directory_path>")
        print("  List uploaded: python upload_manual_images.py --list")
        print("")
        print("Target filenames:")
        uploader = ManualImageUploader()
        for filename in uploader.firebase_paths:
            print(f"  {filename}")
        sys.exit(1)

    uploader = ManualImageUploader()

    if sys.argv[1] == "--list":
        uploader.list_uploaded_images()

    elif sys.argv[1] == "--directory":
        if len(sys.argv) != 3:
            print("Error: --directory requires a directory path")
            sys.exit(1)

        directory_path = sys.argv[2]
        results = uploader.upload_directory(directory_path)

        successful = sum(results.values())
        total = len(results)
        print(f"\nUploaded {successful}/{total} images")

    else:
        if len(sys.argv) != 3:
            print("Error: Single image upload requires <image_path> <target_filename>")
            sys.exit(1)

        image_path = sys.argv[1]
        target_filename = sys.argv[2]

        success = uploader.upload_image(image_path, target_filename)
        if success:
            print(f"Successfully uploaded {target_filename}")
        else:
            print(f"Failed to upload {target_filename}")

if __name__ == "__main__":
    main()