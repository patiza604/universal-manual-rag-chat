# AI Assistant Platform

> **Advanced AI-powered assistant for any manual with embedded vector search and multi-modal responses.**

## 🚀 Quick Backend Redeployment Commands

For future backend updates, use these commands from the chatbot_backend directory:

```bash
# Quick redeploy (recommended)
./deployment/deploy_ai_service.ps1

# Or manual deployment
gcloud run deploy ai-agent-service \
  --source . \
  --project ai-chatbot-472322 \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 80 \
  --min-instances 1 \
  --max-instances 10
```

## 🏗️ Architecture Overview

This platform combines multiple AI services into a unified system:

- **🤖 Generative AI**: Google Gemini 2.5 Flash for intelligent responses
- **🔍 Vector Search**: Embedded FAISS for fast document retrieval
- **🎤 Speech-to-Text**: Google Cloud Speech API
- **🔊 Text-to-Speech**: Google Cloud TTS with premium voices
- **📚 RAG System**: Retrieval-Augmented Generation with manual content
- **🖼️ Multi-modal**: Text and image responses from equipment manuals

## ⚡ Quick Start

### Prerequisites

- **Python 3.11+**
- **Google Cloud SDK** configured with Application Default Credentials
- **Buildpack Configuration Files** (`.python-version`, `runtime.txt`, `Procfile`)
- **Vector Files** in `app/vector-files/`
- **Service Account** with proper IAM permissions

### Local Development

1. **Clone and Setup**
   ```bash
   git clone <repository>
   cd chatbot_backend
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Verify Vector Files**
   ```bash
   ls -la app/vector-files/
   # Should contain:
   #     - embeddings_enhanced.npy
   #     - metadata_enhanced.pkl
   #     - index_to_id_enhanced.pkl
   ```

4. **Run Locally**
   ```bash
   python main.py
   # Service runs on http://localhost:8080
   ```

### Production Deployment

#### Deploy Backend to Cloud Run

1. **Deploy with Buildpacks**
   ```bash
   # Deploy using source code (buildpack deployment)
   gcloud run deploy ai-agent-service \
       --source . \
       --region us-central1 \
       --allow-unauthenticated \
       --service-account ai-agent-runner@ai-chatbot-472322.iam.gserviceaccount.com \
       --set-env-vars "PROJECT_ID=ai-chatbot-472322,LOCATION=us-central1,IS_LOCAL=false,LOCAL_VECTOR_FILES_PATH=app/vector-files,FAISS_INDEX_TYPE=IVF,CORS_ORIGINS=https://ai-chatbot-472322.web.app,DEBUG_MODE=true,LOG_QUERIES=false,EMBEDDING_QUANT=10,FIREBASE_STORAGE_BUCKET=ai-chatbot-472322.appspot.com" \
       --memory 4Gi \
       --cpu 2 \
       --max-instances 10 \
       --timeout 300 \
       --platform managed \
       --project ai-chatbot-472322
   ```

2. **Alternative: Use PowerShell Script**
   ```powershell
   .\deployment\deploy_ai_service.ps1
   ```

3. **Test Deployment**
   ```bash
   # Health check
   curl https://ai-agent-service-325296751367.us-central1.run.app/health

   # Test chat API
   curl -X POST https://ai-agent-service-325296751367.us-central1.run.app/chat/send \
       -H 'Content-Type: application/json' \
       -d '{"message": "What is on page 22?"}'
   ```

## 📁 Project Structure

```
chatbot_backend/
├── app/                                                    # Core application
│   ├── config.py                                          # Configuration management
│   ├── startup.py                                         # FastAPI app & service initialization
│   ├── faiss_vector_service.py                           # Embedded vector search
│   └── vector-files/                                     # Local vector data
├── agent/                                                 # AI components
│   ├── chat_manager.py                                   # Main chat logic
│   ├── retrieval.py                                     # Document retrieval
│   └── embedding.py                                     # Text embeddings
├── api/                                                   # HTTP endpoints
│   ├── routes_chat.py                                   # Chat API
│   ├── routes_tts.py                                   # Text-to-Speech API
│   └── routes_stt.py                                   # Speech-to-Text API
├── deployment/                                           # Deployment scripts
└── training/                                             # Vector preparation tools
```

## ⚙️ Configuration

### Environment Variables

```bash
# Core Settings - UPDATED for new project
PROJECT_ID=ai-chatbot-472322
LOCATION=us-central1
IS_LOCAL=false

# AI Models
GENERATIVE_MODEL_NAME=gemini-2.5-flash
EMBEDDING_MODEL_NAME=text-embedding-004
EMBEDDING_QUANT=10

# FAISS Settings
LOCAL_VECTOR_FILES_PATH=app/vector-files
FAISS_INDEX_TYPE=IVF

# Audio Settings
DEFAULT_VOICE_NAME=en-US-Chirp3-HD-Leda
DEFAULT_LANGUAGE_CODE=en-US

# Security - UPDATED for new URLs
DEBUG_MODE=false
LOG_QUERIES=false
CORS_ORIGINS=https://ai-chatbot-472322.web.app
FIREBASE_STORAGE_BUCKET=ai-chatbot-472322.appspot.com
```

### Service Account Configuration

The application uses Application Default Credentials with a dedicated service account:

```bash
# Service Account: ai-agent-runner@ai-chatbot-472322.iam.gserviceaccount.com
# Required IAM roles:
# - roles/aiplatform.user               (Vertex AI/Gemini)
# - roles/ml.developer                  (ML services)
# - roles/speech.client                 (Speech services)
# - roles/firebase.admin                (Firebase integration)
# - roles/storage.admin                 (Firebase Storage)
# - roles/logging.logWriter            (Cloud Logging)
```

## 🔄 Updating and Redeploying Backend

### For Code Changes

1. **Test Locally First**
   ```bash
   python main.py
   # Test on http://localhost:8080
   ```

2. **Deploy to Production**
   ```bash
   cd chatbot_backend

   # Deploy updated service with buildpacks
   gcloud run deploy ai-agent-service \
       --source . \
       --region us-central1 \
       --project ai-chatbot-472322
   ```

3. **Verify Deployment**
   ```bash
   # Health check
   curl https://ai-agent-service-325296751367.us-central1.run.app/health

   # Test functionality
   curl -X POST https://ai-agent-service-325296751367.us-central1.run.app/chat/send \
       -H 'Content-Type: application/json' \
       -d '{"message": "test message"}'
   ```

### For Environment Variable Updates

```bash
# Update environment variables without rebuilding
gcloud run services update ai-agent-service \
  --region us-central1 \
  --update-env-vars "DEBUG_MODE=false,LOG_QUERIES=true" \
  --project ai-chatbot-472322
```

### For Scaling Adjustments

```bash
# Update resource allocation
gcloud run services update ai-agent-service \
  --region us-central1 \
  --memory 6Gi \
  --cpu 4 \
  --max-instances 20 \
  --min-instances 1 \
  --project ai-chatbot-472322
```

## 📊 Vector Management

### Understanding Vector Files

The system uses three core files for vector search:

1. **`embeddings_enhanced.npy`** - Numerical vector representations
2. **`metadata_enhanced.pkl`** - Text content and metadata
3. **`index_to_id_enhanced.pkl`** - Index mapping

### Updating Vector Content

#### Complete Manual Content Processing Workflow

**Phase 1: Content Preparation**

1. **Fill Out Template**
   ```bash
   cp templates/manual_input_template.md templates/my_manual_content.md
   # Edit templates/my_manual_content.md with your content
   ```

2. **Process Content**
   ```bash
   # Generate enhanced chunks
   python training/scripts/generate_jsonl_enhanced.py templates/my_manual_content.md

   # Create vector files
   python training/scripts/prepare_vectors_enhanced.py training/output/chunks/my_manual_content_enhanced_chunks.jsonl
   ```

3. **Update App and Deploy**
   ```bash
   # Copy new vectors to app
   .\deployment\update_vectors.ps1

   # Test locally
   python main.py

   # Deploy to production with buildpacks
   gcloud run deploy ai-agent-service \
       --source . \
       --region us-central1 \
       --project ai-chatbot-472322
   ```

## 🧪 Testing

### Automated Testing

```bash
# Full deployment test
python deployment/test_ai_service.py

# Health check only
curl https://ai-agent-service-325296751367.us-central1.run.app/health

# Debug information
curl https://ai-agent-service-325296751367.us-central1.run.app/debug/startup-check
```

### Manual API Testing

#### Basic Chat
```bash
curl -X POST https://ai-agent-service-325296751367.us-central1.run.app/chat/send \
      -H 'Content-Type: application/json' \
      -d '{"message": "What is on page 22?"}'
```

#### Chat with TTS
```bash
curl -X POST https://ai-agent-service-325296751367.us-central1.run.app/chat/send-with-tts \
      -H 'Content-Type: application/json' \
      -d '{
              "message": "What is on page 22",
              "include_audio": true,
              "voice_name": "en-US-Chirp3-HD-Leda",
              "language_code": "en-US"
      }'
```

## 📈 Monitoring & Debugging

### Service Health

```bash
# Check all services
curl https://ai-agent-service-325296751367.us-central1.run.app/health

# Check FAISS specifically
curl https://ai-agent-service-325296751367.us-central1.run.app/debug/faiss-status

# Check initialization
curl https://ai-agent-service-325296751367.us-central1.run.app/debug/startup-check
```

### Cloud Logging

```bash
# View recent logs
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=ai-agent-service' --limit=50 --project=ai-chatbot-472322

# Filter for errors
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=ai-agent-service AND severity>=ERROR' --limit=20 --project=ai-chatbot-472322

# Real-time logs
gcloud logging tail 'resource.type=cloud_run_revision AND resource.labels.service_name=ai-agent-service' --project=ai-chatbot-472322
```

## 🔐 Security

### Authentication

- **Service Account**: `ai-agent-runner@ai-chatbot-472322.iam.gserviceaccount.com`
- **Credentials**: Application Default Credentials (no key files)
- **Public Endpoints**: `/health`, `/debug/*`
- **Protected**: All chat and audio endpoints (CORS-protected)

### Data Security

- **Vector Files**: Embedded in container (not in external storage)
- **Credentials**: Service account with minimal required permissions
- **CORS**: Configured for specific frontend origin
- **Content Safety**: Google's safety filters enabled

## 📊 Scaling

### Resource Configuration

```yaml
# Current Cloud Run Configuration
Memory: 4GB                                # For FAISS index in memory
CPU: 2 cores                              # For embedding and inference
Max Instances: 10                         # Horizontal scaling
Timeout: 300s                             # Long enough for complex queries
Min Instances: 0                          # Cost optimization
```

### Performance Tuning

1. **FAISS Index Type**
   - `Flat`: Exact search, slower, smaller datasets
   - `IVF`: Approximate search, faster, larger datasets

2. **Embedding Quantity**
   - `EMBEDDING_QUANT=5`: Faster, less context
   - `EMBEDDING_QUANT=15`: Slower, more context

## 🛠️ Troubleshooting

### Common Issues

#### "FAISS service not available"
```bash
# Check if vector files exist
ls -la app/vector-files/

# Check initialization logs
gcloud logging read 'resource.type=cloud_run_revision AND textPayload:"FAISS"' --limit=10 --project=ai-chatbot-472322
```

#### "Memory exceeded"
```bash
# Increase Cloud Run memory
gcloud run services update ai-agent-service \
      --memory 6Gi \
      --region us-central1 \
      --project ai-chatbot-472322
```

#### Cold Start Issues
```bash
# Set minimum instances
gcloud run services update ai-agent-service \
      --min-instances 1 \
      --region us-central1 \
      --project ai-chatbot-472322
```

#### Buildpack Configuration Issues
```bash
# Verify buildpack configuration files exist
ls -la .python-version runtime.txt Procfile

# Check Python version compatibility
cat .python-version
cat runtime.txt

# Verify Procfile syntax
cat Procfile
```

#### "Source deployment failed"
```bash
# Check for missing configuration files
# Ensure these files exist in your project root:
# - .python-version (contains: 3.11)
# - runtime.txt (contains: python-3.11)
# - Procfile (contains: web: uvicorn main:app --host 0.0.0.0 --port $PORT)

# Check deployment logs for specific errors
gcloud logging read 'resource.type=build' --limit=20 --project=ai-chatbot-472322
```

### Debug Commands

```bash
# Test vector files locally
python -c "
import numpy as np
import pickle
embeddings = np.load('app/vector-files/embeddings_enhanced.npy')
with open('app/vector-files/metadata_enhanced.pkl', 'rb') as f:
    metadata = pickle.load(f)
print(f'Embeddings: {embeddings.shape}')
print(f'Metadata: {len(metadata)} items')
"

# Test FAISS locally
python -c "
from app.faiss_vector_service import LocalFAISSVectorService
service = LocalFAISSVectorService()
success = service.load_index()
print(f'FAISS loaded: {success}')
if success:
    print(service.health_check())
"
```

## 🌐 Production URLs

- **Backend API**: `https://ai-agent-service-325296751367.us-central1.run.app`
- **Frontend**: `https://ai-chatbot-472322.web.app`
- **Goo gle Cloud Console**: `https://console.cloud.google.com/run?project=ai-chatbot-472322`
- **Firebase Console**: `https://console.firebase.google.com/project/ai-chatbot-472322`

## 🔄 Migration Notes

**Project Migration**: `ai-chatbot-beb8d` → `ai-chatbot-472322`

**Key Changes Made:**
- ✅ Updated all project IDs and URLs
- ✅ Switched to Application Default Credentials
- ✅ Created new service account with proper IAM roles
- ✅ Updated CORS configuration for new frontend domain
- ✅ Verified all AI services integration
- ✅ Updated Firebase Storage bucket references

## 📞 Support

- **Technical Issues**: Check troubleshooting section above
- **API Documentation**: See deployed service at `/health` endpoint
- **Deployment Issues**: Check Cloud Run logs
- **Vector Updates**: Follow vector management guide above

---

**Version**: 2.2.0 (Updated to Buildpack Deployment)
**Last Updated**: 2025-09-24
**Status**: ✅ Fully Operational with Buildpack Deployment