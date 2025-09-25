# api/routes_debug.py - Secured debug endpoints
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from audio.clean_text import clean_for_tts
from google.cloud import texttospeech
from app.security import get_admin_key, check_rate_limit
import importlib.metadata
import base64
import os

router = APIRouter()

@router.get("/headers")
def headers_debug(response: Response):
    response.headers["X-Debug"] = "CORS test passed"
    return {"ok": True}

@router.options("/{rest_of_path:path}")
async def preflight_handler():
    return Response(status_code=204)

@router.get("/library-version")
async def get_library_version():
    try:
        version = importlib.metadata.version("google-cloud-aiplatform")
        return {"google_cloud_aiplatform_version": version}
    except importlib.metadata.PackageNotFoundError:
        return {"error": "google-cloud-aiplatform not found in environment"}
    except Exception as e:
        return {"error": f"Failed to get version: {str(e)}"}

@router.get("/tts-status")
async def check_tts_status(req: Request):
    """Check TTS service status"""
    return {
        "tts_client_initialized": req.app.state.tts_client is not None,
        "embedding_model": req.app.state.embedding_model is not None,
        "generative_model": req.app.state.generative_model is not None,
        "chat_manager": req.app.state.chat_manager is not None,
        "faiss_service": req.app.state.faiss_service is not None,
    }

@router.get("/faiss-status")
async def check_faiss_status(req: Request, admin_key: str = Depends(get_admin_key)):
    """Check FAISS service status and performance metrics"""
    check_rate_limit(admin_key)
    faiss_service = req.app.state.faiss_service

    if not faiss_service:
        return {"status": "not_available", "error": "FAISS service not initialized"}

    try:
        health_check = faiss_service.health_check()
        return {
            "status": "healthy",
            "health_check": health_check,
            "index_type": type(faiss_service.faiss_index).__name__ if faiss_service.faiss_index else None,
            "vector_files_path": faiss_service.vector_files_path,
            "has_dynamic_search": hasattr(faiss_service, 'search_dynamic')
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/faiss-test-search")
async def test_faiss_search(req: Request):
    """Test FAISS search performance with sample query"""
    import time
    import numpy as np

    faiss_service = req.app.state.faiss_service

    if not faiss_service:
        raise HTTPException(status_code=500, detail="FAISS service not available")

    try:
        # Generate test embedding
        test_embedding = np.random.rand(768).tolist()

        # Measure search time
        start_time = time.time()
        results = faiss_service.search(test_embedding, k=5)
        search_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        return {
            "status": "success",
            "search_time_ms": round(search_time, 2),
            "results_count": len(results),
            "sample_result": {
                "id": results[0]["id"] if results else None,
                "similarity_score": results[0]["similarity_score"] if results else None,
                "title": results[0].get("title", "") if results else None
            } if results else None
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/test-real-search")
async def test_real_search(req: Request):
    """Test search with real query and return full content"""
    try:
        body = await req.json()
        query = body.get("query", "blinking red LED")

        # Get services
        embedding_model = req.app.state.embedding_model
        faiss_service = req.app.state.faiss_service

        if not embedding_model or not faiss_service:
            raise HTTPException(status_code=500, detail="Required services not available")

        # Generate embedding for query
        response = embedding_model.embed_content(query)
        query_embedding = response.embedding

        # Search FAISS
        results = faiss_service.search_dynamic(
            query_embedding=query_embedding,
            query_type="simple",
            estimated_chunks=5
        )

        # Return detailed results
        return {
            "status": "success",
            "query": query,
            "results_count": len(results),
            "results": [
                {
                    "id": r.get("id"),
                    "content": r.get("content", "")[:500] + "..." if len(r.get("content", "")) > 500 else r.get("content", ""),
                    "title": r.get("title"),
                    "similarity_score": r.get("similarity_score")
                } for r in results
            ]
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/tts-test")
async def test_tts(req: Request):
    """Test TTS with a simple message"""
    tts_client = req.app.state.tts_client
    
    if not tts_client:
        raise HTTPException(status_code=500, detail="TTS service not available.")
    
    test_text = "Hello! This is a test of the AI Agent text-to-speech system. I'm ready to help with your questions."
    cleaned_text = clean_for_tts(test_text)
    
    try:
        synthesis_input = texttospeech.SynthesisInput(text=cleaned_text)
        voice_params = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Chirp3-HD-Leda"
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config
        )
        
        audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
        
        return {
            "success": True,
            "original_text": test_text,
            "cleaned_text": cleaned_text,
            "voice_used": "en-US-Chirp3-HD-Leda",
            "audio_size_bytes": len(response.audio_content),
            "audio_base64": audio_base64
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/clean-text-test")
async def test_text_cleaning():
    """Test the text cleaning function"""
    test_texts = [
        "Hello! This is a *test* of the **cleaning** function.",
        "Here are some `code snippets` and [links](http://example.com).",
        "### Headers and _emphasis_ text with ***multiple*** formatting.",
        "Special characters: @#$%^&*()_+[]{}|\\:;\"'<>?/",
        "Multiple    spaces   and...ellipsis..."
    ]
    
    results = []
    for text in test_texts:
        cleaned = clean_for_tts(text)
        results.append({
            "original": text,
            "cleaned": cleaned
        })
    
    return {"test_results": results}

@router.get("/initialization-status")
async def check_initialization_status(req: Request, admin_key: str = Depends(get_admin_key)):
    """Check if all services are properly initialized"""
    check_rate_limit(admin_key)
    try:
        chat_manager = getattr(req.app.state, 'chat_manager', None)
        embedding_model = getattr(req.app.state, 'embedding_model', None)
        generative_model = getattr(req.app.state, 'generative_model', None)
        tts_client = getattr(req.app.state, 'tts_client', None)
        speech_client = getattr(req.app.state, 'speech_client', None)
        faiss_service = getattr(req.app.state, 'faiss_service', None)
        
        return {
            "is_local": getattr(req.app.state, "is_local", False),
            "project_id": getattr(req.app.state, "project_id", "N/A"),
            "location": getattr(req.app.state, "location", "N/A"),
            "embedding_model_initialized": embedding_model is not None,
            "generative_model_initialized": generative_model is not None,
            "tts_client_initialized": tts_client is not None,
            "speech_client_initialized": speech_client is not None,
            "chat_manager_initialized": chat_manager is not None,
            "chat_manager_model_ready": chat_manager._model is not None if chat_manager else False,
            "chat_manager_chat_ready": chat_manager._chat is not None if chat_manager else False,
            "faiss_service_initialized": faiss_service is not None,
            "faiss_index_loaded": faiss_service.faiss_index is not None if faiss_service else False,
        }
    except Exception as e:
        return {
            "error": f"Failed to check initialization status: {str(e)}",
            "status": "error"
        }

@router.get("/startup-check")
async def startup_check():
    """Simple check that doesn't depend on lifespan initialization"""
    from app.config import IS_LOCAL, PROJECT_ID, LOCATION
    return {
        "status": "FastAPI app is running",
        "is_local": IS_LOCAL,
        "project_id": PROJECT_ID,
        "location": LOCATION,
        "timestamp": "2025-01-27T12:00:00Z"
    }

@router.get("/faiss-status")
async def check_faiss_status(req: Request):
    """Check embedded FAISS service status"""
    try:
        faiss_service = getattr(req.app.state, 'faiss_service', None)
        
        if faiss_service is None:
            return {
                "status": "not_initialized",
                "error": "FAISS service not found in app state"
            }
        
        # Get health check from FAISS service
        health_data = faiss_service.health_check()
        return health_data
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
    
# api/routes_debug.py - Add file check endpoint
@router.get("/vector-files-check")
async def check_vector_files_debug():
    """Check if vector files are available"""
    from app.config import LOCAL_VECTOR_FILES_PATH
    import os
    
    try:
        result = {
            "vector_path": LOCAL_VECTOR_FILES_PATH,
            "path_exists": os.path.exists(LOCAL_VECTOR_FILES_PATH),
            "files": {},
            "all_files": []
        }
        
        if os.path.exists(LOCAL_VECTOR_FILES_PATH):
            # List all files in directory
            for item in os.listdir(LOCAL_VECTOR_FILES_PATH):
                item_path = os.path.join(LOCAL_VECTOR_FILES_PATH, item)
                if os.path.isfile(item_path):
                    result["all_files"].append({
                        "name": item,
                        "size": os.path.getsize(item_path)
                    })
            
            # Check specific enhanced files
            enhanced_files = [
                "embeddings_enhanced.npy",
                "metadata_enhanced.pkl", 
                "index_to_id_enhanced.pkl"
            ]
            
            for filename in enhanced_files:
                filepath = os.path.join(LOCAL_VECTOR_FILES_PATH, filename)
                result["files"][filename] = {
                    "exists": os.path.exists(filepath),
                    "size": os.path.getsize(filepath) if os.path.exists(filepath) else 0
                }
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "vector_path": LOCAL_VECTOR_FILES_PATH
        }
    
# api/routes_debug.py - Add image debugging endpoint
@router.get("/debug-images")
async def debug_images(req: Request):
    """Debug image data in FAISS metadata"""
    faiss_service = req.app.state.faiss_service
    
    if not faiss_service:
        return {"error": "FAISS service not available"}
    
    try:
        # Get a few sample chunks with images
        sample_chunks = []
        image_chunks = []
        
        for i, metadata_item in enumerate(faiss_service.metadata[:20]):  # Check first 20 items
            if isinstance(metadata_item, dict):
                # Check for any image-related fields
                image_fields = {}
                for key, value in metadata_item.items():
                    if 'image' in key.lower():
                        image_fields[key] = value
                
                if image_fields:
                    image_chunks.append({
                        'index': i,
                        'image_fields': image_fields,
                        'content_preview': metadata_item.get('content', '')[:100]
                    })
        
        return {
            "total_chunks": len(faiss_service.metadata),
            "chunks_with_images": len(image_chunks),
            "sample_image_chunks": image_chunks[:5],  # First 5 chunks with images
            "image_field_names": list(set().union(*[chunk['image_fields'].keys() for chunk in image_chunks]))
        }
        
    except Exception as e:
        return {"error": str(e)}
    
   
# api/routes_debug.py - Add test endpoint for Firebase signed URLs
@router.get("/test-firebase-signed-url")
async def test_firebase_signed_url(filename: str, req: Request):
    """Test Firebase signed URL generation with proper format"""
    firebase_service = req.app.state.firebase_service
    
    if not firebase_service:
        return {"error": "Firebase service not available"}
    
    try:
        # Build full path
        full_path = f"ai_images/manual001/{filename}"
        
        # Check service status
        status = firebase_service.get_service_status()
        
        # Check if file exists
        exists = firebase_service.file_exists(full_path)
        
        result = {
            "filename": filename,
            "full_path": full_path,
            "file_exists": exists,
            "service_status": status
        }
        
        if exists:
            # Generate signed URL
            signed_url = firebase_service.generate_signed_url(full_path)
            result["signed_url"] = signed_url
            
            if signed_url:
                # Test the signed URL
                try:
                    import requests
                    test_response = requests.head(signed_url, timeout=5)
                    result["url_test"] = {
                        "status_code": test_response.status_code,
                        "accessible": test_response.status_code == 200
                    }
                except Exception as test_error:
                    result["url_test"] = {
                        "error": str(test_error),
                        "accessible": False
                    }
        else:
            result["error"] = "File does not exist in storage"
            
            # List available files for debugging
            try:
                available_files = firebase_service.list_files("ai_images/manual001/")
                result["available_files"] = available_files[:10]  # First 10 files
            except Exception as list_error:
                result["list_error"] = str(list_error)
        
        return result
    
    except Exception as e:
        return {
            "filename": filename,
            "error": str(e)
        }
    
# api/routes_debug.py - Test the new Firebase service
@router.get("/test-firebase-download-url")
async def test_firebase_download_url(filename: str, req: Request):
    """Test Firebase download URL generation like Flutter"""
    firebase_service = req.app.state.firebase_service
    
    if not firebase_service:
        return {"error": "Firebase service not available"}
    
    try:
        # Test the download URL generation
        download_url = firebase_service.generate_signed_url(filename)
        
        result = {
            "filename": filename,
            "service_status": firebase_service.get_service_status(),
            "file_exists": firebase_service.file_exists(filename),
            "download_url": download_url
        }
        
        # Test the URL if generated
        if download_url:
            try:
                import requests
                response = requests.head(download_url, timeout=5)
                result["url_test"] = {
                    "status_code": response.status_code,
                    "accessible": response.status_code == 200,
                    "headers": dict(response.headers)
                }
            except Exception as test_error:
                result["url_test"] = {"error": str(test_error)}
        
        return result
        
    except Exception as e:
        return {"error": str(e)}
    
    # api/routes_debug.py - Add comprehensive file listing endpoint
@router.get("/debug-firebase-files")
async def debug_firebase_files(req: Request):
    """Debug what files actually exist in Firebase Storage"""
    firebase_service = req.app.state.firebase_service
    
    if not firebase_service:
        return {"error": "Firebase service not available"}
    
    try:
        result = {
            "service_status": firebase_service.get_service_status(),
            "file_listings": {}
        }
        
        # Check different possible paths
        paths_to_check = [
            "",  # Root
            "ai_images/",
            "ai_images/manual001/",
            "manual001/",
            "images/",
            "Thermostat-e1430152369552.jpg"  # Direct filename
        ]
        
        for path in paths_to_check:
            try:
                files = firebase_service.list_files(path)
                result["file_listings"][path or "root"] = files[:20]  # First 20 files
            except Exception as e:
                result["file_listings"][path or "root"] = f"Error: {str(e)}"
        
        # Also try to check if the file exists with different path variations
        filename_variations = [
            "Thermostat-e1430152369552.jpg",
            "ai_images/Thermostat-e1430152369552.jpg.png",
            "ai_images/manual001/Thermostat-e1430152369552.jpg.png",
            "manual001/Thermostat-e1430152369552.jpg.png",
            "images/Thermostat-e1430152369552.jpg.png"
        ]
        
        result["file_existence_checks"] = {}
        for variation in filename_variations:
            try:
                exists = firebase_service.file_exists(variation)
                result["file_existence_checks"][variation] = exists
            except Exception as e:
                result["file_existence_checks"][variation] = f"Error: {str(e)}"
        
        return result
        
    except Exception as e:
        return {"error": str(e)}
    
    # api/routes_debug.py - Add bucket browsing
@router.get("/browse-firebase-storage")
async def browse_firebase_storage(prefix: str = "", req: Request = None):
    """Browse Firebase Storage contents"""
    firebase_service = req.app.state.firebase_service
    
    if not firebase_service:
        return {"error": "Firebase service not available"}
    
    try:
        files = firebase_service.list_files(prefix)
        
        # Group files by directory structure
        directories = set()
        file_list = []
        
        for file_path in files:
            file_list.append({
                "path": file_path,
                "filename": file_path.split('/')[-1],
                "directory": '/'.join(file_path.split('/')[:-1]) if '/' in file_path else "root"
            })
            
            # Extract directory structure
            parts = file_path.split('/')
            for i in range(1, len(parts)):
                directories.add('/'.join(parts[:i]))
        
        return {
            "prefix": prefix,
            "total_files": len(file_list),
            "directories": sorted(list(directories)),
            "files": file_list[:50],  # First 50 files
            "sample_paths": [f["path"] for f in file_list[:10]]
        }
        
    except Exception as e:
        return {"error": str(e)}
    
# api/routes_debug.py - Simple file browser
@router.get("/list-firebase-files")
async def list_firebase_files(prefix: str = "", req: Request = None):
    """List files in Firebase Storage to find the actual structure"""
    firebase_service = req.app.state.firebase_service
    
    if not firebase_service:
        return {"error": "Firebase service not available"}
    
    try:
        files = firebase_service.list_files(prefix)
        
        # Look for Thermostat-e1430152369552.jpg specifically
        thermostat_files = [f for f in files if 'thermostat-e1430152369552.jpg' in f.lower()]
        screen_files = [f for f in files if 'main_screen_layout' in f.lower()]
        
        return {
            "prefix": prefix,
            "total_files": len(files),
            "all_files": files[:50],  # First 50 files
            "thermostat_files": thermostat_files,
            "screen_layout_files": screen_files,
            "image_files": [f for f in files if any(f.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg'])][:20]
        }
        
    except Exception as e:
        return {"error": str(e)}
    
# api/routes_debug.py - Enhanced file listing
@router.get("/debug-all-firebase-files")
async def debug_all_firebase_files(req: Request):
    """Debug all files in Firebase Storage"""
    firebase_service = req.app.state.firebase_service
    
    if not firebase_service:
        return {"error": "Firebase service not available"}
    
    try:
        # Check service status first
        status = firebase_service.get_service_status()
        
        result = {
            "service_status": status,
            "directories": {}
        }
        
        # Check multiple directories
        directories_to_check = [
            "",  # Root
            "ai_images/",
            "ai_images/manual001/", 
            "images/",
            "manual001/",
            "uploads/",
            "assets/"
        ]
        
        for directory in directories_to_check:
            try:
                files = firebase_service.list_files(directory)
                result["directories"][directory or "root"] = {
                    "file_count": len(files),
                    "files": files[:20],  # First 20 files
                    "png_files": [f for f in files if f.lower().endswith('.png')][:10],
                    "thermostat_files": [f for f in files if 'thermostat' in f.lower()],
                    "led_files": [f for f in files if 'led' in f.lower()]
                }
            except Exception as e:
                result["directories"][directory or "root"] = {"error": str(e)}
        
        # Also try to find files that contain our target names
        target_files = ['Thermostat-e1430152369552.jpg', 'main_screen_layout.png']
        result["file_search"] = {}
        
        for target in target_files:
            result["file_search"][target] = {
                "exists_check": firebase_service.file_exists(target),
                "path_variations": []
            }
            
            # Try each directory
            for directory in directories_to_check:
                full_path = f"{directory}{target}".replace("//", "/")
                try:
                    if firebase_service.bucket:
                        blob = firebase_service.bucket.blob(full_path)
                        exists = blob.exists()
                        result["file_search"][target]["path_variations"].append({
                            "path": full_path,
                            "exists": exists
                        })
                except Exception as e:
                    result["file_search"][target]["path_variations"].append({
                        "path": full_path,
                        "error": str(e)
                    })
        
        return result
        
    except Exception as e:
        return {"error": str(e)}
    
# api/routes_debug.py - Simple bucket test
@router.get("/test-firebase-bucket")
async def test_firebase_bucket(req: Request):
    """Test Firebase bucket access"""
    firebase_service = req.app.state.firebase_service
    
    if not firebase_service:
        return {"error": "Firebase service not available"}
    
    try:
        if not firebase_service.bucket:
            return {"error": "Bucket not initialized"}
        
        # Test bucket existence
        bucket_exists = firebase_service.bucket.exists()
        
        # Try to list just a few files from root
        try:
            blobs = list(firebase_service.bucket.list_blobs(max_results=10))
            files = [blob.name for blob in blobs]
        except Exception as list_error:
            files = f"Error listing: {list_error}"
        
        # Try to access a known file path manually
        test_paths = [
            "Thermostat-e1430152369552.jpg.png",
            "ai_images/manual001/Thermostat-e1430152369552.jpg.png",
            "images/Thermostat-e1430152369552.jpg"
        ]
        
        path_tests = {}
        for path in test_paths:
            try:
                blob = firebase_service.bucket.blob(path)
                path_tests[path] = blob.exists()
            except Exception as e:
                path_tests[path] = f"Error: {e}"
        
        return {
            "bucket_exists": bucket_exists,
            "bucket_name": firebase_service.bucket.name,
            "sample_files": files,
            "path_tests": path_tests
        }
        
    except Exception as e:
        return {"error": str(e)}
    
# api/routes_debug.py - Test different bucket names
@router.get("/test-bucket-names")
async def test_bucket_names(req: Request):
    """Test different bucket name formats"""
    try:
        from google.cloud import storage
        from google.oauth2 import service_account
        from app.config import IS_LOCAL

        # Initialize client with Application Default Credentials
        client = storage.Client()
        
        # Test different bucket names
        bucket_names_to_test = [
            "ai-chatbot-beb8d",
            "ai-chatbot-beb8d.appspot.com",
            "ai-chatbot-beb8d.firebasestorage.app"
        ]
        
        results = {}
        
        for bucket_name in bucket_names_to_test:
            try:
                bucket = client.bucket(bucket_name)
                exists = bucket.exists()
                
                files = []
                if exists:
                    try:
                        blobs = list(bucket.list_blobs(max_results=5))
                        files = [blob.name for blob in blobs]
                    except Exception as list_error:
                        files = f"List error: {list_error}"
                
                results[bucket_name] = {
                    "exists": exists,
                    "sample_files": files
                }
                
            except Exception as e:
                results[bucket_name] = {
                    "error": str(e)
                }
        
        return results
        
    except Exception as e:
        return {"error": str(e)}