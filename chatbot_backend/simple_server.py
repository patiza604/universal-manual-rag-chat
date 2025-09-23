#!/usr/bin/env python3
"""
Simple backend server for testing connectivity and image serving
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
import sys
import os
import io

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Orbi ChatBot API - Simple Test Server")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "healthy", "message": "Simple Orbi ChatBot API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "firebase": "not tested in simple mode",
            "ai": "not available in simple mode"
        }
    }

@app.post("/chat/send")
async def send_chat_message(request: dict):
    """Simple chat endpoint that returns a mock response with image"""
    message = request.get("message", "")

    # Mock response with image based on message content
    response_parts = []

    if "connect" in message.lower() or "router" in message.lower():
        # Use backend proxy to avoid CORS issues
        image_filename = 'modem_router_cabling.png'

        response_parts = [
            {
                "type": "text",
                "content": "To connect your Orbi router, follow these steps:\n1. Connect your modem to the router's Internet port\n2. Plug in the power adapter\n3. Wait for the LED to show solid white\n\nRefer to the diagram below for proper cable connections."
            },
            {
                "type": "image",
                "uri": f"http://localhost:8080/image-proxy/{image_filename}",
                "alt": "Router connection diagram showing modem connected to Internet port"
            }
        ]
    elif "led" in message.lower() or "light" in message.lower():
        # Use backend proxy to avoid CORS issues
        image_filename = 'satellite_sync_leds.png'

        response_parts = [
            {
                "type": "text",
                "content": "The Orbi router has different LED indicators:\n• Solid white: Normal operation\n• Pulsing white: Booting or sync in progress\n• Solid magenta: No Internet connection\n• Off: Normal operation (front LED)\n\nFor satellite LEDs:\n• Blue: Good connection\n• Amber: Fair connection\n• Magenta: Failed to sync"
            },
            {
                "type": "image",
                "uri": f"http://localhost:8080/image-proxy/{image_filename}",
                "alt": "LED status indicators for router and satellite"
            }
        ]
    elif "setup" in message.lower() or "login" in message.lower():
        # Use backend proxy to avoid CORS issues
        image_filename = 'internet_setup_wizard.png'

        response_parts = [
            {
                "type": "text",
                "content": "To access the Orbi setup:\n1. Connect to the Orbi WiFi network\n2. Open a web browser\n3. Go to orbilogin.com\n4. Follow the setup wizard\n\nThe first time you access the router, the installation assistant will guide you through the setup process."
            },
            {
                "type": "image",
                "uri": f"http://localhost:8080/image-proxy/{image_filename}",
                "alt": "Orbi setup wizard interface"
            }
        ]
    else:
        response_parts = [
            {
                "type": "text",
                "content": f"I received your message: '{message}'\n\nThis is a simple test server. For full AI responses, please ensure all Google Cloud services are properly configured.\n\nTry asking about:\n• How to connect the router\n• LED light meanings\n• Setup and login process"
            }
        ]

    return {
        "response": {
            "parts": response_parts
        }
    }

@app.post("/chat/send-with-tts")
async def send_chat_message_with_tts(request: dict):
    """Chat endpoint with TTS (mock implementation)"""
    # Get regular chat response
    chat_response = await send_chat_message(request)

    # Add mock TTS data
    return {
        **chat_response,
        "audio_generated": False,
        "audio_data": None,
        "tts_note": "TTS not available in simple test server"
    }

@app.get("/debug/firebase-status")
async def firebase_status():
    """Check Firebase service status"""
    try:
        from app.firebase_service import FirebaseStorageService

        service = FirebaseStorageService()
        if service.bucket:
            # Test a few images
            test_images = [
                "internet_setup_wizard.png",
                "modem_router_cabling.png",
                "satellite_sync_leds.png"
            ]

            results = {}
            for img in test_images:
                exists = service.file_exists(img)
                url = service.generate_signed_url(img) if exists else None
                results[img] = {
                    "exists": exists,
                    "has_signed_url": url is not None,
                    "signed_url": url[:100] + "..." if url else None
                }

            return {
                "firebase_status": "connected",
                "bucket": service.bucket.name,
                "images": results
            }
        else:
            return {"firebase_status": "not connected", "error": "Bucket not initialized"}

    except Exception as e:
        return {"firebase_status": "error", "error": str(e)}

@app.get("/image-proxy/{filename}")
@app.head("/image-proxy/{filename}")
async def image_proxy(filename: str):
    """Proxy endpoint to serve Firebase Storage images and bypass CORS"""
    try:
        from app.firebase_service import FirebaseStorageService

        firebase_service = FirebaseStorageService()
        if not firebase_service.bucket:
            raise HTTPException(status_code=500, detail="Firebase Storage not available")

        # Get the image blob directly
        blob = firebase_service.bucket.blob(f"ai_images/manual001/{filename}")

        if not blob.exists():
            raise HTTPException(status_code=404, detail="Image not found")

        # Download image data
        image_data = blob.download_as_bytes()

        # Determine content type
        content_type = "image/png"
        if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            content_type = "image/jpeg"

        return StreamingResponse(
            io.BytesIO(image_data),
            media_type=content_type,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "*",
            }
        )

    except Exception as e:
        print(f"ERROR: Image proxy failed for {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch image: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"Starting Simple Orbi ChatBot API on port {port}")
    print(f"Health check: http://localhost:{port}/health")
    print(f"Firebase test: http://localhost:{port}/debug/firebase-status")

    uvicorn.run(app, host="0.0.0.0", port=port)