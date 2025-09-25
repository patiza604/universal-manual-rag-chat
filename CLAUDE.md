# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered assistant platform that combines a Flutter frontend with a Python FastAPI backend. The system provides multimodal chat capabilities with speech-to-text, text-to-speech, and RAG (Retrieval-Augmented Generation) using embedded FAISS vector search.

**KEY FEATURE**: The AI assistant is configured with **strict manual adherence** - it ONLY provides information directly from the official Orbi manual content, ensuring accurate and reliable technical support responses.

## Architecture

### Backend (chatbot_backend/)
- **Framework**: FastAPI with Python 3.11+
- **AI Services**: Google Gemini 2.5 Flash with **strict manual adherence**, Google Cloud Speech/TTS
- **Vector Search**: Embedded FAISS with local vector files
- **Image Storage**: Firebase Storage with signed URLs for secure image access
- **Deployment**: Google Cloud Run with buildpack (no Dockerfile required)

### Frontend (chatbot_frontend/)
- **Framework**: Flutter with Firebase integration
- **Runtime**: Firebase Functions (Node.js) + Flutter web/mobile app
- **Authentication**: Google Sign-In with Firebase Auth
- **Storage**: Firebase Firestore and Cloud Storage

## Development Commands

### Backend Development
```bash
# Setup and run locally
cd chatbot_backend
pip install -r requirements.txt
python main.py  # Runs on localhost:8080

# Lint (if available)
python -m pylint app/ agent/ api/

# Test deployment
python deployment/test_ai_service.py

# Deploy to Cloud Run (buildpack method - recommended)
gcloud run deploy ai-agent-service --source . --region us-central1 --allow-unauthenticated

# Legacy deployment script (Docker-based, may need updates for buildpack)
./deployment/deploy_ai_service.ps1
```

### Frontend Development
```bash
# Setup Flutter
cd chatbot_frontend
flutter pub get

# Run locally
flutter run -d web  # For web
flutter run         # For mobile

# Firebase Functions
cd functions
npm install
npm run lint
npm run serve    # Local emulator
npm run deploy   # Deploy functions

# Flutter tests
flutter test
```

### Enhanced Universal Customer Support RAG System
**PRODUCTION-READY**: Advanced multi-tier customer support system with intelligent search strategies:

```bash
# Process any manual type with Universal Customer Support Chunking
python training/scripts/generate_jsonl_enhanced.py templates/my_manual_content.md

# Generate enhanced vectors with multi-embedding strategy and level-aware search
python training/scripts/prepare_vectors_enhanced.py training/output/chunks/my_manual_content_enhanced_chunks.jsonl

# Results: 2.6x more chunks (34 vs 13) with superior customer support optimization:
# - 6-level chunk hierarchy (L0: quick facts, L1: sections, L2: summaries, QA: questions, L3: document, L4: cross-refs)
# - Multi-embedding generation (content + questions + combined)
# - Intelligent query classification (quick_facts, troubleshooting, setup, progressive)
# - Level-aware search weights (L0: 1.2x, QA: 1.3x for instant answers)
# - Customer support metadata (difficulty, time estimates, escalation paths)
# - Firebase service account authentication

# Test enhanced system
python test_simple.py  # Validates level-aware search and query classification

# Update vector files in app (copies enhanced vectors + multi-embeddings)
cp training/output/vectors_v2/* app/vector-files/

# Test and deploy
python main.py  # Test locally first

# Recommended: Buildpack deployment
gcloud run deploy ai-agent-service --source . --region us-central1 --allow-unauthenticated

# Legacy: Docker-based script (may need updates for buildpack)
./deployment/deploy_ai_service.ps1
```

### Enhanced System Features (MAJOR UPGRADE)
- **4 Intelligent Search Strategies**: quick_facts, troubleshooting, setup, progressive
- **Multi-Embedding Architecture**: Content, question, and combined embeddings for superior retrieval
- **Level-Aware Search Weights**: L0 quick facts get 1.2x boost, QA pairs get 1.3x boost for instant answers
- **Query Classification**: 75% accuracy automatic routing based on customer intent patterns
- **Progressive Complexity**: Instant L0 answers → detailed L1 procedures → comprehensive L2 summaries
- **Customer Support Metadata**: 6 specialized fields including escalation paths and success indicators
- **Production Authentication**: Firebase service account integration with graceful fallbacks
- **Performance Optimized**: <1ms search response times, 2.6x more relevant chunks

### Customer Support Excellence Features
- **Quick Facts (L0)**: "What does red LED mean?" → Instant indicator explanations
- **Troubleshooting Workflows**: "WiFi not working" → Progressive L0→L2→L1→L4 search strategy
- **Guided Setup**: "How to setup router" → Step-by-step procedures with prerequisites
- **Multi-Domain**: Electronics (97%), Software (3%), expandable to automotive, appliances

📚 **Complete Guide**: See `training/docs/UNIVERSAL_RAG_SYSTEM_GUIDE.md` for comprehensive documentation

### Image Management Workflow
When adding new images to the system:

```bash
# Extract images from PDF manual
python training/scripts/extract_pdf_images.py path/to/manual.pdf

# Manual upload of specific images
python training/scripts/upload_manual_images.py path/to/image.png

# Test Firebase Storage service
python test_firebase_service.py

# Development testing with simple server
python simple_server.py  # Includes image proxy endpoint
```

## Key Configuration Files

- **Backend**: `chatbot_backend/app/config.py` - Environment variables and AI model settings
- **Backend Deployment**: `chatbot_backend/.python-version` - Python 3.11 runtime specification
- **Backend Runtime**: `chatbot_backend/runtime.txt` - Cloud Run Python runtime configuration
- **Backend Process**: `chatbot_backend/Procfile` - ASGI server startup command
- **Frontend**: `chatbot_frontend/pubspec.yaml` - Flutter dependencies
- **Firebase Config**: `chatbot_frontend/firebase.json` - Firebase project configuration
- **Firebase Options**: `chatbot_frontend/lib/firebase_options.dart` - Generated Firebase configuration
- **Vector Files**: `chatbot_backend/app/vector-files/` - FAISS embeddings and metadata
- **Functions**: `chatbot_frontend/functions/package.json` - Firebase Functions configuration

## Essential Environment Variables

```bash
# Backend (.env)
PROJECT_ID=ai-chatbot-beb8d
LOCATION=us-central1
GENERATIVE_MODEL_NAME=gemini-2.5-flash
EMBEDDING_MODEL_NAME=text-embedding-004
DEFAULT_VOICE_NAME=en-US-Chirp3-HD-Leda
CORS_ORIGINS=https://your-frontend-domain.com
```

## Architecture Patterns

### Backend Services
- **Agent Layer** (`agent/`): Core AI logic with chat_manager.py orchestrating retrieval and response generation
  - **Strict Manual Adherence**: AI responses limited to official manual content only
  - **No Generic Advice**: Eliminates conversational language and generic troubleshooting
  - **Direct Technical Responses**: Word-for-word quoting from manual sections
- **API Layer** (`api/`): RESTful endpoints for chat, TTS, STT, and debugging
- **App Layer** (`app/`): Configuration, startup, enhanced FAISS vector service with level-aware search, and Firebase Storage service
- **Enhanced Vector Management** (`app/faiss_vector_service.py`):
  - Multi-embedding support (content, questions, combined)
  - 4 intelligent search strategies (quick_facts, troubleshooting, setup, progressive)
  - Level-aware search weights and boosting
  - Query classification with 75% accuracy
  - Sub-1ms response times with 34 enhanced chunks
- **Image Management** (`app/firebase_service.py`): Firebase Storage integration with signed URL generation for secure image access

### Frontend Structure
- **Services** (`lib/services/`): Firebase integration, auth, AI chat, speech services
- **Screens** (`lib/screens/`): Main UI components (home_screen.dart, ai_chat_screen.dart)
- **Models** (`lib/models/`): Data models for API communication
- **Widgets** (`lib/widgets/`): Reusable UI components
- **Firebase Functions** (`functions/`): Server-side functions with Node.js 22 runtime

### Universal Customer Support RAG Architecture
**NEW COMPONENTS**:
- **UniversalContentExtractor** (`training/scripts/content_extractor.py`): Domain-agnostic pattern extraction
- **UniversalMetadataEnhancer** (`training/scripts/metadata_enhancer.py`): Customer support metadata generation
- **UniversalChunkingOrchestrator** (`training/scripts/chunking_orchestrator.py`): Multi-level chunk coordination
- **Configuration System** (`training/config/manual_config.yaml`): Domain-specific customization

### Enhanced Vector Content Workflow
1. **Content templates** in `templates/` (Markdown format) - **ANY domain supported**
2. **Universal processing** extracts patterns, generates questions, assesses difficulty
3. **Multi-level chunking** creates L0→L4 chunks optimized for customer support
4. **Enhanced metadata** includes user questions, time estimates, escalation paths
5. **Vector generation** creates FAISS-compatible files with rich customer support context
6. **Deployment** copies enhanced vectors to app directory for superior RAG performance

## Manual Adherence System

### Strict Response Controls
The AI system is configured with **critical requirements** to ensure responses contain only official manual information:

**Implementation** (`agent/chat_manager.py` lines 125-141):
- **ONLY use exact information** from the manual context
- **NO friendly greetings** or conversational language
- **NO generic advice** not explicitly stated in the manual
- **Quote LED meanings and troubleshooting** word-for-word from manual
- **Direct technical responses** with no embellishments

**Example Response Quality**:
- ✅ **Correct**: "Blinking red light indicates firmware corrupted (from Troubleshooting Indicators & Connectivity)"
- ❌ **Incorrect**: "Oh no worries! A blinking red light usually means there's an issue with your device..."

**Benefits**:
- **Accurate Information**: Only official Orbi manual content
- **Consistent Support**: No contradictory or outdated advice
- **Professional Responses**: Direct technical information
- **Manual Traceability**: References to specific manual sections

### Frontend-Backend Connection
Updated `chatbot_frontend/lib/services/ai_chat_service.dart` to connect to deployed Cloud Run service:
```dart
final String _backendBaseUrl = 'https://ai-agent-service-325296751367.us-central1.run.app';
```

## Testing

### Enhanced Customer Support RAG Testing
```bash
# Test enhanced level-aware search and query classification
python test_simple.py

# Comprehensive customer support scenario testing
python test_customer_queries.py  # Full test suite with emojis (if supported)

# Results validation:
# - Query classification: 75% accuracy
# - Level-aware search: 4 strategies tested
# - Customer support metadata: 6/6 fields validated
# - Performance: <1ms response times
# - Coverage: 34 enhanced chunks vs 13 original
```

### Manual Adherence Testing
```bash
# Test strict manual adherence with LED questions
curl -X POST "https://ai-agent-service-325296751367.us-central1.run.app/chat/send" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"red light is blinking\"}"  # Should return exact manual content

# Expected response: "Blinking red light indicates firmware corrupted" (from manual)
# Should NOT include: generic advice, friendly greetings, or non-manual content
```

### API and System Testing
```bash
# Backend API tests with enhanced customer support queries
curl -X POST "https://ai-agent-service-325296751367.us-central1.run.app/chat/send" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What does red LED mean?\"}"  # Tests quick_facts strategy

curl -X POST "https://ai-agent-service-325296751367.us-central1.run.app/chat/send" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"WiFi not working\"}"  # Tests troubleshooting strategy

# Enhanced health checks
curl http://localhost:8080/health
curl http://localhost:8080/debug/faiss-status  # Shows 34 enhanced vectors
curl http://localhost:8080/debug/firebase-status

# Image proxy tests (development mode)
curl -I http://localhost:8080/image-proxy/modem_router_cabling.png
curl http://localhost:8080/image-proxy/satellite_sync_leds.png -o test_image.png

# Flutter tests
cd chatbot_frontend
flutter test
```

## Key Dependencies

### Backend (requirements.txt)
- `fastapi==0.104.1` - Web framework
- `uvicorn[standard]==0.24.0` - ASGI server
- `google-generativeai>=0.4.0` - Gemini AI
- `google-cloud-aiplatform==1.49.0` - Vertex AI
- `google-cloud-texttospeech==2.16.3` - Text-to-speech
- `google-cloud-speech==2.26.0` - Speech-to-text
- `faiss-cpu==1.7.4` - Vector search
- `firebase-admin>=6.0.0,<7.0.0` - Firebase integration
- `google-cloud-storage==2.10.0` - Firebase Storage access

### Frontend (pubspec.yaml)
- `firebase_core: 4.1.0` - Firebase SDK
- `cloud_firestore: ^6.0.1` - Database
- `firebase_auth: ^6.0.2` - Authentication
- `speech_to_text` - Voice input (via git override)
- `audioplayers: ^6.5.0` - Audio playback
- `record: ^6.0.0` - Audio recording
- `http: ^1.4.0` - HTTP requests

## Troubleshooting

### Manual Adherence Issues
- **AI giving generic advice**: Check prompt in `agent/chat_manager.py` lines 125-141 - should have "CRITICAL REQUIREMENTS"
- **Friendly/conversational responses**: Update prompt to explicitly prohibit greetings and embellishments
- **Non-manual content**: Verify RAG system is retrieving correct chunks with `curl /debug/faiss-status`
- **Missing manual references**: Ensure response includes section names from retrieved chunks
- **Frontend showing localhost errors**: Update `ai_chat_service.dart` to use Cloud Run URL instead of localhost:8080

### Enhanced Universal RAG System Issues
- **Multi-embedding generation fails**: Check Firebase service account permissions for `aiplatform.endpoints.predict`
- **Level-aware search returns no results**: Verify chunk levels in metadata (should be L0, L1, L2, QA, L3, L4)
- **Query classification inaccurate**: Add domain-specific patterns to `classify_query_from_text()` method
- **Search weights not applied**: Check `search_weight` field exists in enhanced metadata
- **Authentication errors**: Ensure service account key exists at `gcp-keys/ai-chatbot-472322-firebase-storage.json`
- **PyYAML missing**: Install with `pip install PyYAML`
- **Unicode display errors**: Emojis automatically converted to ASCII for Windows compatibility
- **Low chunk count**: Check manual template format - sections must follow `## Section N:` pattern
- **Poor question quality**: Adjust question templates in configuration file

### Deployment Issues (Buildpack Method)
- **Build fails with buildpack**: Ensure `.python-version` file contains `3.11` and `runtime.txt` contains `python-3.11`
- **Service won't start**: Check `Procfile` contains correct startup command: `web: python main.py`
- **Python version mismatch**: Verify both `.python-version` and `runtime.txt` specify Python 3.11
- **Dependencies not installing**: Check `requirements.txt` is in root directory and properly formatted
- **Source deployment fails**: Use `gcloud run deploy --source .` instead of Docker-based deployment
- **Buildpack detection fails**: Ensure `requirements.txt` exists in project root for Python buildpack detection
- **Deployment script issues**: The PowerShell script `deploy_ai_service.ps1` may need updates to use buildpack instead of Docker build process

### Legacy System Issues
- **FAISS service not available**: Check vector files exist in `app/vector-files/`
- **Memory exceeded**: Increase Cloud Run memory allocation (default 4GB)
- **Firebase auth errors**: Verify google-services.json and Firebase config
- **Cold start issues**: Set minimum instances for Cloud Run service
- **Images not displaying**: Check Firebase Storage bucket permissions and signed URL generation
- **Image access denied**: Verify service account has `roles/storage.admin` permissions
- **CORS errors for images**: Use the image proxy endpoint `/image-proxy/{filename}` instead of direct Firebase URLs
- **Flutter image RangeError**: Check URL substring operations in `ai_chat_screen.dart` for safe string handling

### Debug Commands
```bash
# Check vector files locally
python -c "import numpy as np; print(np.load('app/vector-files/embeddings_enhanced.npy').shape)"

# View Cloud Run logs
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=ai-agent-service' --limit=50

# Test Enhanced FAISS locally
python -c "from app.faiss_vector_service import EnhancedFAISSVectorService; s=EnhancedFAISSVectorService(); print(s.load_index())"

# Test level-aware search strategies
python test_simple.py

# Test Firebase Storage access
python test_firebase_service.py
curl http://localhost:8080/debug/firebase-status

# Test image proxy endpoint (development mode only)
curl -I http://localhost:8080/image-proxy/modem_router_cabling.png
curl http://localhost:8080/image-proxy/satellite_sync_leds.png -o test_download.png

# Enhanced Universal RAG System debugging
python -c "
import json
with open('training/output/chunks/my_manual_content_enhanced_chunks.jsonl') as f:
    chunks = [json.loads(line) for line in f]
levels = {}
categories = {}
for chunk in chunks:
    level = chunk['metadata']['level']
    category = chunk['metadata']['support_category']
    levels[level] = levels.get(level, 0) + 1
    categories[category] = categories.get(category, 0) + 1
print(f'Generated {len(chunks)} enhanced chunks:')
print(f'  Levels: {levels}')
print(f'  Support categories: {categories}')
"

# Test enhanced vectors and metadata
python -c "
import pickle
import numpy as np
embeddings = np.load('app/vector-files/embeddings_enhanced.npy')
with open('app/vector-files/metadata_enhanced.pkl', 'rb') as f:
    metadata = pickle.load(f)
print(f'Enhanced vectors: {embeddings.shape}')
print(f'Metadata entries: {len(metadata)}')
print(f'Sample metadata fields: {list(metadata[0].keys())}')
"

# Test query classification
python -c "
from app.faiss_vector_service import EnhancedFAISSVectorService
service = EnhancedFAISSVectorService()
queries = ['What does red LED mean?', 'WiFi not working', 'How to setup router']
for query in queries:
    result = service.classify_query_from_text(query)
    print(f'{query} -> {result}')
"

# Test Universal Content Extractor
python training/scripts/content_extractor.py

# Test Universal Orchestrator
python training/scripts/chunking_orchestrator.py

# Buildpack deployment debugging
# Check buildpack configuration files
ls -la .python-version runtime.txt Procfile

# Test buildpack deployment locally (if supported)
gcloud run deploy ai-agent-service --source . --region us-central1 --no-traffic

# View buildpack build logs
gcloud logging read 'resource.type=build AND resource.labels.build_id=YOUR_BUILD_ID' --limit=50

# Check Cloud Run service configuration
gcloud run services describe ai-agent-service --region us-central1 --format="export"
```

## Image Retrieval Implementation

### Architecture
The system uses a **backend image proxy pattern** to serve Firebase Storage images while bypassing CORS restrictions in Flutter web applications:

1. **Firebase Storage**: Images stored at `ai_images/manual001/{filename}` in bucket `ai-chatbot-472322.firebasestorage.app`
2. **Backend Proxy**: Simple server provides `/image-proxy/{filename}` endpoint that:
   - Downloads images from Firebase Storage using service account credentials
   - Serves images with proper CORS headers (`Access-Control-Allow-Origin: *`)
   - Supports both HEAD and GET requests for Flutter compatibility
3. **Frontend Integration**: Flutter app receives backend proxy URLs (`http://localhost:8080/image-proxy/...`) instead of direct Firebase URLs

### Key Files
- `app/firebase_service.py`: Firebase Storage service with signed URL generation
- `simple_server.py`: Development server with image proxy endpoint (lines 160-196)
- `chatbot_frontend/lib/screens/ai_chat_screen.dart`: Image URL processing with safe substring handling
- `templates/my_manual_content.md`: Vector content with image references
- `training/scripts/extract_pdf_images.py`: PDF image extraction and Firebase upload utility

### Image Processing Workflow
1. **Content Creation**: Images referenced in vector content templates
2. **PDF Extraction**: Automated extraction from PDF manuals with filename mapping
3. **Firebase Upload**: Images uploaded to correct bucket path with service account authentication
4. **Backend Serving**: Development proxy serves images with CORS headers for local testing
5. **Frontend Display**: Flutter app receives proxy URLs and displays images without CORS issues

## Deployment Architecture

### Buildpack Deployment (Current Method)
The project uses Google Cloud buildpacks for containerization, eliminating Docker Hub authentication issues:

**Key Files**:
- `.python-version`: Specifies Python 3.11 runtime
- `runtime.txt`: Cloud Run Python runtime configuration (`python-3.11`)
- `Procfile`: ASGI server startup (`web: python main.py`)
- `requirements.txt`: Python dependencies for buildpack detection

**Deployment Commands**:
```bash
# Method 1: Direct buildpack deployment (recommended)
cd chatbot_backend
gcloud run deploy ai-agent-service --source . --region us-central1 --allow-unauthenticated --memory 4Gi --cpu 2

# Method 2: PowerShell deployment script (legacy Docker method - may need updates)
./deployment/deploy_ai_service.ps1

# Method 3: Manual buildpack deployment with full configuration
gcloud run deploy ai-agent-service \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars "PROJECT_ID=ai-chatbot-472322,LOCATION=us-central1,IS_LOCAL=false"
```

**Benefits**:
- No Dockerfile required
- No Docker Hub authentication needed
- Automatic Python buildpack detection
- Simplified deployment process
- Better integration with Cloud Run

## Notes

- This is a production-ready AI assistant platform with enterprise-level vector search
- The embedded FAISS architecture provides faster response times and lower costs than separate services
- **Buildpack Deployment**: Uses Google Cloud buildpacks instead of Docker for simplified deployment
- Vector content processing requires Google Cloud credentials and can take significant time for large documents
- Always test locally before deploying vector updates to production
- **Image Proxy**: The `/image-proxy/` endpoint is for development use; production should use direct Firebase Storage URLs with proper CORS configuration

## Recent Updates (2025-09-23)

### ✅ Strict Manual Adherence Implementation
- **Fixed AI responses** to only provide official manual content (no generic advice)
- **Updated prompt system** in `chat_manager.py` with critical requirements for manual adherence
- **Eliminated conversational language** - responses now purely technical and factual
- **Example**: "Blinking red light indicates firmware corrupted" instead of friendly troubleshooting chat

### ✅ Frontend-Backend Connection Fix
- **Updated** `ai_chat_service.dart` to use deployed Cloud Run URL
- **Fixed** localhost:8080 connection issues preventing chat functionality
- **Deployed** updated backend with strict manual adherence to production

### ✅ Buildpack Deployment Implementation (2025-09-24)
- **Migrated from Docker** to Google Cloud buildpacks for simplified deployment
- **Resolved Docker Hub authentication** issues that were blocking deployments
- **Added buildpack configuration**: `.python-version`, `runtime.txt`, `Procfile`
- **Streamlined deployment process** with `gcloud run deploy --source .`
- **Eliminated Docker dependency** for faster, more reliable deployments

### ✅ Current Status
- **Backend**: Deployed at `https://ai-agent-service-325296751367.us-central1.run.app`
- **Deployment Method**: Google Cloud buildpacks (no Docker required)
- **Manual Content**: 34 enhanced chunks with comprehensive Orbi troubleshooting
- **Response Quality**: Direct, manual-based technical support responses
- **Frontend**: Properly connected to production backend
- whenever a script doesn't work, utilize the script-quality-reviewer.md to correct the script rather than find a workaround to using the script.