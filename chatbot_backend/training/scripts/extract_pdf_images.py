#!/usr/bin/env python3
"""
PDF Image Extraction and Firebase Upload Script

This script extracts images from a PDF manual and uploads them to Firebase Storage
with the specific filenames referenced in my_manual_content.md.
"""

import os
import sys
import json
from pathlib import Path
import tempfile
from typing import List, Dict, Any, Optional
import logging

# PDF and image processing
try:
    import fitz  # PyMuPDF
    from PIL import Image
    import io
except ImportError as e:
    print(f"Missing required packages: {e}")
    print("Please install: pip install PyMuPDF Pillow")
    sys.exit(1)

# Firebase
try:
    from google.cloud import storage
    from google.oauth2 import service_account
except ImportError as e:
    print(f"Missing Firebase packages: {e}")
    print("Please install: pip install google-cloud-storage")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFImageExtractor:
    """Extract images from PDF and upload to Firebase Storage"""

    def __init__(self, bucket_name: str = "ai-chatbot-472322.firebasestorage.app"):
        self.bucket_name = bucket_name
        self.storage_client = None
        self.bucket = None
        self._initialize_firebase()

        # Expected images from my_manual_content.md
        self.expected_images = {
            "orbi_router_front_back.png": {
                "description": "Front and rear view of Orbi router showing ring LED on front and labeled back panel",
                "firebase_path": "manual001/orbi_router_front_back.png",
                "section": "overview_hardware_leds_001",
                "pages": [6, 7, 8]  # Likely pages to find this image
            },
            "orbi_satellite_front_back.png": {
                "description": "Front and rear view of Orbi satellite showing Satellite LED on front and labeled back panel",
                "firebase_path": "manual001/orbi_satellite_front_back.png",
                "section": "overview_hardware_leds_001",
                "pages": [6, 7, 8, 9]
            },
            "modem_router_cabling.png": {
                "description": "Diagram showing modem connected via Ethernet to Orbi router Internet port",
                "firebase_path": "manual001/modem_router_cabling.png",
                "section": "install_connect_router_002",
                "pages": [11, 12]
            },
            "satellite_sync_leds.png": {
                "description": "Satellite front LED ring illustrating Blue, Amber, Magenta states",
                "firebase_path": "manual001/satellite_sync_leds.png",
                "section": "place_sync_satellite_003",
                "pages": [12, 13]
            },
            "label_qr_example.png": {
                "description": "Sample router and satellite labels with SSID, password, QR code",
                "firebase_path": "manual001/label_qr_example.png",
                "section": "connect_to_network_access_004",
                "pages": [14, 15, 16]
            },
            "internet_setup_wizard.png": {
                "description": "Browser screenshot of Orbi setup wizard showing automatic connection detection",
                "firebase_path": "manual001/internet_setup_wizard.png",
                "section": "internet_setup_web_005",
                "pages": [17, 18, 19]
            },
            "ap_mode_settings.png": {
                "description": "Settings page illustrating AP mode toggle and IP assignment options",
                "firebase_path": "manual001/ap_mode_settings.png",
                "section": "ap_mode_ip_settings_006",
                "pages": [71, 72]
            },
            "firmware_update_satellite_router.png": {
                "description": "Two panels showing satellite firmware update selection and router firmware update screen",
                "firebase_path": "manual001/firmware_update_satellite_router.png",
                "section": "manage_network_advanced_007",
                "pages": [80, 85, 90]
            },
            "wan_aggregation_diagram.png": {
                "description": "Diagram showing modem → router Internet port + Port 1 aggregated",
                "firebase_path": "manual001/wan_aggregation_diagram.png",
                "section": "wired_backhaul_aggregation_008",
                "pages": [7, 8, 10, 11, 12, 13]
            },
            "login_orbilogin_com.png": {
                "description": "Browser address bar with orbilogin.com and Orbi login page fields",
                "firebase_path": "manual001/login_orbilogin_com.png",
                "section": "web_admin_login_basics_009",
                "pages": [17, 18]
            },
            "led_quick_reference_table.png": {
                "description": "Consolidated table mapping router/satellite LEDs to meanings and actions",
                "firebase_path": "manual001/led_quick_reference_table.png",
                "section": "troubleshooting_leds_010",
                "pages": [8, 9, 10, 11, 118, 119, 120]
            },
            "factory_reset_button.png": {
                "description": "Back panel close-up showing Reset button and Power LED behavior",
                "firebase_path": "manual001/factory_reset_button.png",
                "section": "factory_settings_011",
                "pages": [128, 129, 130]
            },
            "tech_specs_tables.png": {
                "description": "Extract-style table image with ports, power, dimensions, and operating environment",
                "firebase_path": "manual001/tech_specs_tables.png",
                "section": "technical_specs_012",
                "pages": [132, 133]
            }
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

    def extract_images_from_pdf(self, pdf_path: str, output_dir: str = None) -> List[Dict[str, Any]]:
        """Extract all images from PDF with metadata"""
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="orbi_manual_images_")

        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Extracting images from PDF: {pdf_path}")
        logger.info(f"Output directory: {output_dir}")

        extracted_images = []

        try:
            # Open PDF
            pdf_document = fitz.open(pdf_path)
            logger.info(f"PDF opened successfully. Pages: {len(pdf_document)}")

            image_counter = 0

            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                image_list = page.get_images(full=True)

                if image_list:
                    logger.info(f"Page {page_num + 1}: Found {len(image_list)} images")

                for img_index, img in enumerate(image_list):
                    try:
                        # Get image data
                        xref = img[0]
                        pix = fitz.Pixmap(pdf_document, xref)

                        # Convert to PNG if not already
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_data = pix.tobytes("png")
                        else:  # CMYK, convert to RGB first
                            pix1 = fitz.Pixmap(fitz.csRGB, pix)
                            img_data = pix1.tobytes("png")
                            pix1 = None

                        # Save image with metadata
                        image_counter += 1
                        filename = f"page_{page_num + 1:03d}_img_{img_index + 1:02d}.png"
                        filepath = os.path.join(output_dir, filename)

                        with open(filepath, "wb") as f:
                            f.write(img_data)

                        # Get image dimensions
                        with Image.open(io.BytesIO(img_data)) as pil_img:
                            width, height = pil_img.size

                        extracted_images.append({
                            "filename": filename,
                            "filepath": filepath,
                            "page": page_num + 1,
                            "image_index": img_index + 1,
                            "width": width,
                            "height": height,
                            "size_bytes": len(img_data),
                            "xref": xref
                        })

                        logger.info(f"  Saved: {filename} ({width}x{height}, {len(img_data)} bytes)")

                        pix = None

                    except Exception as e:
                        logger.error(f"Error extracting image {img_index + 1} from page {page_num + 1}: {e}")
                        continue

            pdf_document.close()
            logger.info(f"✅ Extraction complete. Total images: {len(extracted_images)}")
            return extracted_images

        except Exception as e:
            logger.error(f"❌ Error processing PDF: {e}")
            return []

    def analyze_and_match_images(self, extracted_images: List[Dict[str, Any]]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Analyze extracted images and match them to expected images"""
        logger.info("Analyzing extracted images to match with expected images...")

        matches = {}

        for expected_name, expected_info in self.expected_images.items():
            logger.info(f"\nLooking for: {expected_name}")
            logger.info(f"  Description: {expected_info['description']}")
            logger.info(f"  Expected pages: {expected_info['pages']}")

            # Find candidate images from expected pages
            candidates = []
            for img in extracted_images:
                if img['page'] in expected_info['pages']:
                    candidates.append(img)

            if candidates:
                logger.info(f"  Found {len(candidates)} candidate(s) on expected pages")

                # For now, select the largest image from expected pages
                # In a more sophisticated version, we could use image analysis
                best_candidate = max(candidates, key=lambda x: x['width'] * x['height'])
                matches[expected_name] = best_candidate
                logger.info(f"  ✅ Matched: {best_candidate['filename']} ({best_candidate['width']}x{best_candidate['height']})")
            else:
                logger.warning(f"  ❌ No candidates found on expected pages")
                matches[expected_name] = None

        return matches

    def upload_matched_images(self, matches: Dict[str, Optional[Dict[str, Any]]]) -> Dict[str, bool]:
        """Upload matched images to Firebase Storage"""
        if not self.bucket:
            logger.error("Firebase Storage not available")
            return {}

        upload_results = {}

        for expected_name, image_info in matches.items():
            if image_info is None:
                logger.warning(f"Skipping {expected_name} - no match found")
                upload_results[expected_name] = False
                continue

            try:
                # Get Firebase path
                firebase_path = self.expected_images[expected_name]['firebase_path']

                # Upload to Firebase Storage
                blob = self.bucket.blob(firebase_path)

                logger.info(f"Uploading {expected_name} -> {firebase_path}")

                with open(image_info['filepath'], 'rb') as f:
                    blob.upload_from_file(f, content_type='image/png')

                # Set metadata
                blob.metadata = {
                    'original_filename': image_info['filename'],
                    'source_page': str(image_info['page']),
                    'description': self.expected_images[expected_name]['description'],
                    'section': self.expected_images[expected_name]['section'],
                    'width': str(image_info['width']),
                    'height': str(image_info['height'])
                }
                blob.patch()

                logger.info(f"✅ Uploaded successfully: {firebase_path}")
                upload_results[expected_name] = True

            except Exception as e:
                logger.error(f"❌ Failed to upload {expected_name}: {e}")
                upload_results[expected_name] = False

        return upload_results

    def process_pdf_manual(self, pdf_path: str) -> Dict[str, Any]:
        """Complete workflow: extract, match, and upload images"""
        logger.info(f"🚀 Starting PDF manual processing: {pdf_path}")

        # Step 1: Extract all images
        extracted_images = self.extract_images_from_pdf(pdf_path)
        if not extracted_images:
            return {"success": False, "error": "No images extracted from PDF"}

        # Step 2: Match images to expected files
        matches = self.analyze_and_match_images(extracted_images)

        # Step 3: Upload matched images
        upload_results = self.upload_matched_images(matches)

        # Summary
        total_expected = len(self.expected_images)
        successful_uploads = sum(upload_results.values())

        result = {
            "success": True,
            "total_extracted": len(extracted_images),
            "total_expected": total_expected,
            "successful_matches": len([m for m in matches.values() if m is not None]),
            "successful_uploads": successful_uploads,
            "upload_results": upload_results,
            "matches": {k: v['filename'] if v else None for k, v in matches.items()}
        }

        logger.info(f"\n🎉 Processing complete!")
        logger.info(f"   Extracted: {result['total_extracted']} images")
        logger.info(f"   Expected: {result['total_expected']} images")
        logger.info(f"   Matched: {result['successful_matches']} images")
        logger.info(f"   Uploaded: {result['successful_uploads']} images")

        return result

def main():
    """Main function for command line usage"""
    if len(sys.argv) != 2:
        print("Usage: python extract_pdf_images.py <path_to_pdf>")
        print("Example: python extract_pdf_images.py orbi_manual.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    # Create extractor and process PDF
    extractor = PDFImageExtractor()
    result = extractor.process_pdf_manual(pdf_path)

    if result["success"]:
        print(f"\nSuccess! Uploaded {result['successful_uploads']}/{result['total_expected']} images to Firebase Storage")

        # Show which images were uploaded
        for img_name, uploaded in result["upload_results"].items():
            status = "SUCCESS" if uploaded else "FAILED"
            print(f"  {status}: {img_name}")
    else:
        print(f"Failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()