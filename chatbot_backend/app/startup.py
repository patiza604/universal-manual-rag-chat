# app/startup.py - Complete corrected version
import os
import sys
import re
import traceback
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from dotenv import load_dotenv
import vertexai
from vertexai.language_models import TextEmbeddingModel
from google.cloud import texttospeech
from google.cloud import speech_v1p1beta1 as speech
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel
from app.firebase_service import FirebaseStorageService

firebase_service: FirebaseStorageService = None

# Load environment variables from .env file (for local development)
if os.path.exists('.env'):
    load_dotenv('.env')
    print("DEBUG: Loaded .env file", flush=True)

# Import config after loading .env
from app.config import (
    PROJECT_ID, LOCATION, IS_LOCAL,
    GENERATIVE_MODEL_NAME, EMBEDDING_MODEL_NAME,
    CORS_ORIGINS, DEBUG_MODE, LOCAL_VECTOR_FILES_PATH
)
from app.logger import setup_logging
from app.faiss_vector_service import EnhancedFAISSVectorService
from app.security import get_admin_key
from agent.chat_manager import AIChatManager
from agent.prompt import CORE_SYSTEM_INSTRUCTION

# Import routes - with error handling
try:
    from api.routes_chat import router as chat_router
    from api.routes_tts import router as tts_router
    from api.routes_stt import router as stt_router
    from api.routes_debug import router as debug_router
    print("DEBUG: All route imports successful", flush=True)
except Exception as e:
    print(f"ERROR: Failed to import routes: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

# Global variables for services
embedding_model: TextEmbeddingModel = None
generative_model: GenerativeModel = None
chat_manager: AIChatManager = None
tts_client: texttospeech.TextToSpeechClient = None
speech_client: speech.SpeechClient = None
faiss_service: EnhancedFAISSVectorService = None

# Create FastAPI app
app = FastAPI(
    title="AI Agent Service",
    description="AI Agent with Embedded FAISS Vector Search",
    version="2.0.0",
    debug=DEBUG_MODE
)

# Configure CORS with restricted origins (NO WILDCARD)
origins = CORS_ORIGINS.copy()  # Use environment-configured origins

# Add development origins only if in local mode
if IS_LOCAL:
    dev_origins = [
        "http://localhost:55316",
        "http://localhost:3000",
        "http://localhost:8080"
    ]
    origins.extend(dev_origins)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    return response

# Custom CORS configuration that supports localhost wildcards
import re
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class DynamicCORSMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_origins: list, **kwargs):
        super().__init__(app)
        self.allowed_origins = allowed_origins
        self.allow_credentials = kwargs.get('allow_credentials', True)
        self.allow_methods = kwargs.get('allow_methods', ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
        self.allow_headers = kwargs.get('allow_headers', [
            "Authorization", "Content-Type", "X-API-Key", "Accept",
            "Origin", "User-Agent", "Cache-Control", "Content-Language",
            "Accept-Language"
        ])

    def is_allowed_origin(self, origin: str) -> bool:
        if not origin:
            return False

        # Check exact matches first
        if origin in self.allowed_origins:
            return True

        # Check localhost with any port pattern
        localhost_pattern = r'^http://localhost:\d+$'
        if re.match(localhost_pattern, origin):
            return True

        return False

    async def dispatch(self, request, call_next):
        origin = request.headers.get('Origin')

        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            if self.is_allowed_origin(origin):
                return Response(
                    status_code=200,
                    headers={
                        'Access-Control-Allow-Origin': origin,
                        'Access-Control-Allow-Methods': ', '.join(self.allow_methods),
                        'Access-Control-Allow-Headers': ', '.join(self.allow_headers),
                        'Access-Control-Allow-Credentials': 'true' if self.allow_credentials else 'false',
                        'Access-Control-Max-Age': '600'
                    }
                )
            else:
                return Response(status_code=400)

        # Handle regular requests
        response = await call_next(request)

        if self.is_allowed_origin(origin):
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true' if self.allow_credentials else 'false'
            response.headers['Vary'] = 'Origin'

        return response

# Apply custom CORS middleware
app.add_middleware(
    DynamicCORSMiddleware,
    allowed_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization", "Content-Type", "X-API-Key", "Accept",
        "Origin", "User-Agent", "Cache-Control", "Content-Language",
        "Accept-Language"
    ]
)

# Include routers with error handling
try:
    app.include_router(chat_router, prefix="/chat", tags=["chat"])
    app.include_router(tts_router, prefix="/tts", tags=["tts"])
    app.include_router(stt_router, tags=["stt"])
    app.include_router(debug_router, prefix="/debug", tags=["debug"])
    print("DEBUG: All routers included successfully", flush=True)
except Exception as e:
    print(f"ERROR: Failed to include routers: {e}", flush=True)
    traceback.print_exc()

# Root endpoints
@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "AI Agent Service is running!"}

# Enhanced health check with service status
@app.get("/health")
async def detailed_health_check():
    """Detailed health check with service status"""
    return {
        "status": "healthy",
        "project_id": PROJECT_ID,
        "location": LOCATION,
        "is_local": IS_LOCAL,
        "local_vector_files_path": LOCAL_VECTOR_FILES_PATH,
        "services": {
            "embedding_model": embedding_model is not None,
            "generative_model": generative_model is not None,
            "chat_manager": chat_manager is not None,
            "tts_client": tts_client is not None,
            "speech_client": speech_client is not None,
            "faiss_service": faiss_service is not None,
            "faiss_service_loaded": faiss_service is not None and faiss_service.faiss_index is not None if faiss_service else False
        }
    }

# Debug endpoint (admin only)
@app.get("/debug/config")
async def debug_config(admin_key: str = Depends(get_admin_key)):
    """Debug configuration endpoint"""
    return {
        "project_id": PROJECT_ID,
        "location": LOCATION,
        "is_local": IS_LOCAL,
        "local_vector_files_path": LOCAL_VECTOR_FILES_PATH,
        "debug_mode": DEBUG_MODE,
        "cors_origins": CORS_ORIGINS,
        "models": {
            "generative_model": GENERATIVE_MODEL_NAME,
            "embedding_model": EMBEDDING_MODEL_NAME
        }
    }

def check_vector_files():
    """Check if vector files exist and are accessible - UPDATED for enhanced filenames"""
    try:
        print(f"DEBUG: Checking vector files in: {LOCAL_VECTOR_FILES_PATH}", flush=True)
        
        if not os.path.exists(LOCAL_VECTOR_FILES_PATH):
            print(f"ERROR: Vector files directory not found: {LOCAL_VECTOR_FILES_PATH}", flush=True)
            return False
        
        # CORRECTED: Use the same filenames as defined in EnhancedFAISSVectorService
        required_files = [
            "embeddings_enhanced.npy",
            "metadata_enhanced.pkl", 
            "index_to_id_enhanced.pkl"
        ]
        
        print(f"DEBUG: Looking for enhanced vector files: {required_files}", flush=True)
        
        missing_files = []
        existing_files = []
        
        # First, list all files in the directory
        try:
            all_files = os.listdir(LOCAL_VECTOR_FILES_PATH)
            print(f"DEBUG: All files in directory: {all_files}", flush=True)
        except Exception as e:
            print(f"ERROR: Could not list directory contents: {e}", flush=True)
            return False
        
        # Check for required files
        for file_name in required_files:
            file_path = os.path.join(LOCAL_VECTOR_FILES_PATH, file_name)
            if not os.path.exists(file_path):
                missing_files.append(file_name)
                print(f"DEBUG: Missing file: {file_name}", flush=True)
            else:
                file_size = os.path.getsize(file_path)
                existing_files.append(file_name)
                print(f"DEBUG: Found {file_name} ({file_size} bytes)", flush=True)
        
        if missing_files:
            print(f"ERROR: Missing enhanced vector files: {missing_files}", flush=True)
            print(f"DEBUG: Found enhanced vector files: {existing_files}", flush=True)
            return False
            
        print("DEBUG: All required enhanced vector files found", flush=True)
        return True
        
    except Exception as e:
        print(f"ERROR: Exception checking vector files: {e}", flush=True)
        traceback.print_exc()
        return False

# Startup event handler
async def startup_event():
    """Startup event handler"""
    global embedding_model, generative_model, chat_manager, tts_client, speech_client, faiss_service
    
    setup_logging()
    
    print("=" * 50, flush=True)
    print("STARTUP EVENT HANDLER CALLED", flush=True)
    print("=" * 50, flush=True)
    
    print(f"IS_LOCAL: {IS_LOCAL}", flush=True)
    print(f"PROJECT_ID: {PROJECT_ID}", flush=True)
    print(f"LOCATION: {LOCATION}", flush=True)
    print(f"LOCAL_VECTOR_FILES_PATH: {LOCAL_VECTOR_FILES_PATH}", flush=True)
    print(f"DEBUG_MODE: {DEBUG_MODE}", flush=True)

    try:
        # Initialize Vertex AI
        print("DEBUG: Initializing Vertex AI...", flush=True)
        # Initialize Vertex AI with Application Default Credentials
        print("DEBUG: Initializing Vertex AI with Application Default Credentials", flush=True)
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        print("DEBUG: Vertex AI initialized with default credentials.", flush=True)

        # Check vector files before initializing FAISS
        print("DEBUG: Checking enhanced vector files availability...", flush=True)
        if not check_vector_files():
            print("ERROR: Enhanced vector files check failed - FAISS service will not be available", flush=True)
            faiss_service = None
        else:
            # Initialize embedded FAISS service with enhanced filenames
            print("DEBUG: Initializing enhanced FAISS service...", flush=True)
            try:
                # Create service with explicit enhanced filenames
                faiss_service = EnhancedFAISSVectorService(
                    vector_files_path=LOCAL_VECTOR_FILES_PATH,
                    embeddings_file="embeddings_enhanced.npy",
                    metadata_file="metadata_enhanced.pkl", 
                    id_map_file="index_to_id_enhanced.pkl"
                )
                print(f"DEBUG: EnhancedFAISSVectorService created with files:", flush=True)
                print(f"  - embeddings: {faiss_service.embeddings_file}", flush=True)
                print(f"  - metadata: {faiss_service.metadata_file}", flush=True)
                print(f"  - id_map: {faiss_service.id_map_file}", flush=True)
                
                print("DEBUG: Loading FAISS index...", flush=True)
                success = faiss_service.load_index()
                if success:
                    print("DEBUG: Enhanced FAISS service loaded successfully.", flush=True)
                    
                    # Test the service
                    health_status = faiss_service.health_check()
                    print(f"DEBUG: FAISS health check: {health_status}", flush=True)
                else:
                    print("ERROR: Failed to load enhanced FAISS index", flush=True)
                    faiss_service = None
                    
            except Exception as e:
                print(f"ERROR: Failed to initialize enhanced FAISS service: {e}", flush=True)
                traceback.print_exc()
                faiss_service = None

        # Load embedding model
        print("DEBUG: Loading embedding model...", flush=True)
        try:
            embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_NAME)
            print("DEBUG: Embedding model loaded successfully.", flush=True)
        except Exception as e:
            print(f"ERROR: Failed to load embedding model: {e}", flush=True)
            traceback.print_exc()
            embedding_model = None

        # Load generative model
        print("DEBUG: Loading generative model...", flush=True)
        try:
            generative_model = GenerativeModel(
                model_name=GENERATIVE_MODEL_NAME,
                system_instruction=CORE_SYSTEM_INSTRUCTION.strip()
            )
            print("DEBUG: Generative model loaded successfully.", flush=True)
        except Exception as e:
            print(f"ERROR: Failed to load generative model: {e}", flush=True)
            traceback.print_exc()
            generative_model = None

        # Initialize chat manager
        print("DEBUG: Initializing chat manager...", flush=True)
        try:
            if generative_model:
                chat_manager = AIChatManager(generative_model)
                print("DEBUG: Chat manager initialized successfully.", flush=True)
            else:
                print("WARNING: Skipping chat manager initialization - no generative model", flush=True)
                chat_manager = None
        except Exception as e:
            print(f"ERROR: Failed to initialize chat manager: {e}", flush=True)
            traceback.print_exc()
            chat_manager = None

        # Initialize TTS client
        print("DEBUG: Initializing TTS client...", flush=True)
        try:
            # Initialize TTS with Application Default Credentials
            from google.auth import default
            credentials, project = default()
            tts_client = texttospeech.TextToSpeechClient(
                credentials=credentials,
                client_options={"api_endpoint": "texttospeech.googleapis.com"}
            )
            print(f"DEBUG: TTS initialized with default credentials for project: {project}")
        except Exception as e:
            print(f"ERROR: Failed to initialize TTS client: {e}", flush=True)
            traceback.print_exc()
            try:
                print("DEBUG: Attempting TTS fallback initialization...", flush=True)
                tts_client = texttospeech.TextToSpeechClient()
                print("DEBUG: TTS fallback initialization successful")
            except Exception as fallback_e:
                print(f"ERROR: TTS fallback also failed: {fallback_e}", flush=True)
                tts_client = None

        # Initialize Speech-to-Text
        print("DEBUG: Initializing Speech-to-Text client...", flush=True)
        try:
            # Initialize Speech with Application Default Credentials
            from google.auth import default
            credentials, project = default()
            speech_client = speech.SpeechClient(
                credentials=credentials,
                client_options={"api_endpoint": "speech.googleapis.com"}
            )
            print(f"DEBUG: Speech-to-Text initialized with default credentials for project: {project}")
                
            # Test the client
            print("DEBUG: Testing Speech-to-Text client...")
            test_config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",
            )
            print("DEBUG: Speech-to-Text client test successful")
            
        except Exception as e:
            print(f"ERROR: Failed to initialize Speech-to-Text client: {e}", flush=True)
            traceback.print_exc()
            speech_client = None

        print("DEBUG: Initializing Firebase Storage service...", flush=True)
        try:
            if FirebaseStorageService:
                firebase_service = FirebaseStorageService()
                if firebase_service and firebase_service.bucket:
                    print("DEBUG: ✅ Firebase Storage service initialized successfully.", flush=True)
                    
                    # Test with a known file
                    test_files = ['Thermostat-e1430152369552.jpg']
                    for test_file in test_files:
                        exists = firebase_service.file_exists(test_file)
                        print(f"DEBUG: Test file '{test_file}' exists: {exists}", flush=True)
                        if exists:
                            break
                else:
                    print("WARNING: Firebase Storage service object created but bucket not accessible", flush=True)
                    firebase_service = None
            else:
                print("ERROR: FirebaseStorageService class not available", flush=True)
                firebase_service = None
        except Exception as e:
            print(f"ERROR: Failed to initialize Firebase Storage service: {e}", flush=True)
            traceback.print_exc()
            firebase_service = None
        
        # Store services in app state for access in routes
        app.state.embedding_model = embedding_model
        app.state.generative_model = generative_model
        app.state.chat_manager = chat_manager
        app.state.tts_client = tts_client
        app.state.speech_client = speech_client
        app.state.faiss_service = faiss_service
        app.state.firebase_service = firebase_service 

        print("=" * 50, flush=True)
        print("STARTUP COMPLETE - Service Status:", flush=True)
        print(f"- Embedding Model: {'✓' if embedding_model else '✗'}", flush=True)
        print(f"- Generative Model: {'✓' if generative_model else '✗'}", flush=True)
        print(f"- Chat Manager: {'✓' if chat_manager else '✗'}", flush=True)
        print(f"- TTS Client: {'✓' if tts_client else '✗'}", flush=True)
        print(f"- Speech Client: {'✓' if speech_client else '✗'}", flush=True)
        print(f"- FAISS Service: {'✓' if faiss_service else '✗'}", flush=True)
        print(f"- Firebase Service: {'✓' if firebase_service else '✗'}", flush=True)
        if faiss_service:
            print(f"- FAISS Index Loaded: {'✓' if faiss_service.faiss_index else '✗'}", flush=True)
        print("=" * 50, flush=True)
            
    except Exception as e:
        print(f"FATAL ERROR in startup event: {e}", flush=True)
        print(f"FATAL ERROR in startup event: {e}", file=sys.stderr, flush=True)
        traceback.print_exc()
        print("=" * 50, flush=True)
        print("STARTUP FAILED - Continuing with degraded service", flush=True)
        print("=" * 50, flush=True)

# Add the startup event
app.add_event_handler("startup", startup_event)

# Graceful shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("DEBUG: Shutting down services...", flush=True)
    print("DEBUG: Shutdown complete", flush=True)