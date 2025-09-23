import os
import logging
from typing import Optional
from datetime import datetime, timedelta
from google.cloud import storage
from google.oauth2 import service_account
from app.config import IS_LOCAL
import google.auth
from google.auth.transport import requests

logger = logging.getLogger(__name__)

class FirebaseStorageService:
    """Firebase Storage service for ai-chatbot-472322"""

    def __init__(self):
        self.client = None
        self.bucket = None
        self._initialize_storage()

    def _initialize_storage(self):
        """Initialize Google Cloud Storage client with confirmed bucket"""
        try:
            # Try to use service account key file first
            key_paths = [
                "gcp-keys/ai-chatbot-472322-firebase-storage.json",
                "gcp-keys/ai-chatbot-beb8d-firebase-adminsdk-fbsvc-c2ce8b36f1.json",
                "gcp-keys/service-account-key.json"
            ]

            credentials = None
            for key_path in key_paths:
                if os.path.exists(key_path):
                    logger.info(f"Using service account key: {key_path}")
                    credentials = service_account.Credentials.from_service_account_file(key_path)
                    break

            if credentials:
                self.client = storage.Client(credentials=credentials)
            else:
                logger.info("No service account key found, using Application Default Credentials")
                self.client = storage.Client()

            bucket_name = "ai-chatbot-472322.firebasestorage.app"
            logger.info(f"Using bucket: {bucket_name}")
            self.bucket = self.client.bucket(bucket_name)

            if self.bucket.exists():
                logger.info("✅ Bucket initialized successfully")
                # Debug: List some files to confirm access
                blobs = list(self.bucket.list_blobs(prefix="ai_images/manual001/", max_results=5))
                files = [blob.name for blob in blobs]
                logger.info(f"📁 Sample files in 'ai_images/manual001/': {files}")
            else:
                logger.error(f"❌ Bucket {bucket_name} does not exist or is inaccessible")
                self.bucket = None

        except Exception as e:
            logger.error(f"❌ Failed to initialize Firebase Storage: {e}")
            import traceback
            traceback.print_exc()
            self.client = None
            self.bucket = None

    def generate_signed_url(self, file_path_or_gcs_uri: str, expiration_hours: int = 24) -> Optional[str]:
        """Generate v2 signed URL using access token"""
        if not self.bucket:
            logger.error("❌ Firebase Storage bucket not initialized")
            return None

        try:
            filename = file_path_or_gcs_uri.strip().lstrip('/')
            if '/' in filename:
                filename = filename.split('/')[-1]

            logger.info(f"🔍 Trying to find file: {filename}")
            primary_path = f"ai_images/manual001/{filename}"
            logger.info(f"🔍 Trying primary path: {primary_path}")
            blob = self.bucket.blob(primary_path)
            if blob.exists():
                # Use v4 signing which works with service account credentials
                download_url = blob.generate_signed_url(
                    version='v4',
                    expiration=timedelta(hours=expiration_hours),
                    method='GET'
                )
                logger.info(f"✅ Found file at path: {primary_path}. Generated v4 signed URL: {download_url}")
                return download_url
            else:
                logger.debug(f"❌ File not found at: {primary_path}")

            # Debug listing
            logger.info("🔍 Listing files for debugging...")
            blobs = list(self.bucket.list_blobs(prefix="ai_images/manual001/", max_results=10))
            files = [blob.name for blob in blobs]
            logger.info(f"📁 Files in 'ai_images/manual001/': {files}")
            similar = [f for f in files if filename.lower() in f.lower()]
            if similar:
                logger.info(f"✅ Found similar files: {similar}")

            logger.warning(f"❌ File not found: {filename}")
            return None

        except Exception as e:
            logger.error(f"❌ Error generating signed URL: {e}")
            import traceback
            traceback.print_exc()
            return None

    def file_exists(self, file_path_or_gcs_uri: str) -> bool:
        """Check if file exists"""
        if not self.bucket:
            return False

        try:
            filename = file_path_or_gcs_uri.strip().lstrip('/')
            if '/' in filename:
                filename = filename.split('/')[-1]
            path = f"ai_images/manual001/{filename}"
            blob = self.bucket.blob(path)
            exists = blob.exists()
            logger.info(f"✅ File exists at {path}: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            return False

    def list_files(self, prefix: str = "") -> list:
        """List files in storage"""
        if not self.bucket:
            return []

        try:
            blobs = self.bucket.list_blobs(prefix=prefix, max_results=100)
            files = [blob.name for blob in blobs]
            logger.info(f"📁 Files in '{prefix}': {files}")
            return files
        except Exception as e:
            logger.error(f"Error listing files with prefix '{prefix}': {e}")
            return []