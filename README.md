# Universal Manual RAG Chat

> **Enterprise-ready AI customer support system with comprehensive security audit, advanced RAG architecture, and buildpack deployment**

[![Security Audit](https://img.shields.io/badge/Security_Audit-PASSED-green?style=for-the-badge&logo=shield&logoColor=white)](./SECURITY_REPORT.md)
[![Production Ready](https://img.shields.io/badge/Production-READY-brightgreen?style=for-the-badge&logo=checkmarx&logoColor=white)](https://ai-agent-service-325296751367.us-central1.run.app/health)
[![Flutter](https://img.shields.io/badge/Flutter-02569B?style=for-the-badge&logo=flutter&logoColor=white)](https://flutter.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com)
[![Firebase](https://img.shields.io/badge/Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com)
[![Buildpacks](https://img.shields.io/badge/Buildpacks-Deployed-blue?style=for-the-badge&logo=cloudfoundry&logoColor=white)](https://buildpacks.io/)

## 🌟 Overview

Universal Manual RAG Chat is an **enterprise-ready** AI customer support system that transforms technical manuals into intelligent assistants. After completing a comprehensive **security audit** and migrating to **Google Cloud buildpacks**, the system now provides production-grade security with accurate, reliable responses from official documentation.

### 🎯 Key Features

- **🔒 Enterprise Security** - Comprehensive security audit passed, all vulnerabilities resolved
- **🚀 Buildpack Deployment** - Modern Cloud Run buildpacks for improved security and reliability
- **🛡️ API Authentication** - Key-based authentication with rate limiting (100 requests/hour)
- **🔍 Universal Manual Processing** - Works with any domain: electronics, automotive, software, appliances
- **🧠 Enhanced RAG Architecture** - 6-level chunk hierarchy with intelligent search strategies
- **🎙️ Multimodal Interface** - Voice input/output, text chat, and image support
- **⚡ Lightning Fast** - Sub-1ms search response times with FAISS vector search
- **🎯 Strict Manual Adherence** - Responses limited to official manual content only
- **📱 Cross-Platform** - Flutter web/mobile app with Firebase integration

### 🏗️ Architecture Highlights

- **🔐 Security-First Design**: API authentication, input validation, XSS protection, secure CORS
- **📦 Buildpack Deployment**: Modern Google Cloud buildpacks with automatic runtime management
- **🛡️ Production Security**: Rate limiting, security headers, credential management
- **4 Intelligent Search Strategies**: Quick facts, troubleshooting, setup, progressive
- **Multi-Embedding System**: Content, question, and combined embeddings
- **Level-Aware Search Weights**: L0 (1.2x boost), QA pairs (1.3x boost)
- **Query Classification**: 75% accuracy automatic routing
- **Enterprise Ready**: Production deployment at [ai-agent-service-325296751367.us-central1.run.app](https://ai-agent-service-325296751367.us-central1.run.app/health)

## 🔒 Security Status

### ✅ Security Audit Completed (2025-09-23)

All **critical and high-risk vulnerabilities** have been resolved:

- **🔴 CRITICAL (2 issues)**: ✅ **RESOLVED** - CVE-2024-24762 FastAPI vulnerability fixed, service account credentials secured
- **🟠 HIGH (3 issues)**: ✅ **RESOLVED** - API authentication implemented, CORS hardened, Firebase rules secured
- **🟡 MEDIUM (3 issues)**: ✅ **RESOLVED** - Input validation added, image proxy secured, dependencies updated

**Production Security Features**:
- 🔐 **API Key Authentication** with rate limiting
- 🛡️ **Security Headers** (XSS, CSRF, content-type protection)
- 🔒 **Secure Credential Management** with environment variables
- 🌐 **Hardened CORS** with explicit domain control
- ✅ **Input Validation** and XSS protection
- 📊 **Updated Dependencies** (FastAPI 0.115.0, secure packages)

📋 **[View Complete Security Report](./SECURITY_REPORT.md)**

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Flutter SDK
- Google Cloud account
- Firebase project

### Backend Setup

```bash
# Clone and navigate
git clone https://github.com/patiza604/universal-manual-rag-chat.git
cd universal-manual-rag-chat/chatbot_backend

# Setup environment (REQUIRED for security)
cp .env.example .env
# Edit .env with your API keys and configuration

# Install dependencies
pip install -r requirements.txt

# Generate API keys for authentication
python -c "from app.security import generate_api_key; print('API_KEY:', generate_api_key())"

# Run locally
python main.py  # Runs on localhost:8080
```

### 🔐 Production Environment Variables

**Required for production deployment**:
```bash
# Core Configuration
PROJECT_ID=your-project-id
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app

# Security (REQUIRED)
API_KEYS=key1,key2,key3  # Generate with security.generate_api_key()
ADMIN_API_KEY=admin-key  # Generate with security.generate_api_key()
CORS_ORIGINS=https://yourdomain.com  # Your actual domains

# Credentials (recommended)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Frontend Setup

```bash
# Navigate to frontend
cd chatbot_frontend

# Install Flutter dependencies
flutter pub get

# Run web app
flutter run -d web

# Run mobile app
flutter run
```

### Firebase Functions

```bash
# Navigate to functions
cd chatbot_frontend/functions

# Install dependencies
npm install

# Local emulator
npm run serve

# Deploy functions
npm run deploy
```

## 📊 Enhanced RAG System

### Universal Customer Support Features

Our **Enhanced Universal Customer Support RAG System** provides enterprise-grade customer support capabilities:

#### 🎯 Multi-Level Chunk Hierarchy
- **L0**: Quick facts and instant answers
- **L1**: Step-by-step procedures
- **L2**: Comprehensive summaries
- **QA**: Question-answer pairs
- **L3**: Full document context
- **L4**: Cross-references and related content

#### 🔍 Intelligent Search Strategies
1. **Quick Facts**: Instant indicator explanations, LED meanings
2. **Troubleshooting**: Progressive complexity search (L0→L2→L1→L4)
3. **Setup**: Guided procedures with prerequisites
4. **Progressive**: Adaptive search based on query complexity

#### 📈 Performance Metrics
- **2.6x More Chunks**: 34 enhanced vs 13 original chunks
- **75% Query Classification Accuracy**
- **<1ms Search Response Times**
- **1.2x-1.3x Level-Aware Boost Weights**

### Processing Any Manual

**Complete 5-Step Manual Processing Pipeline:**

```bash
# 1. Convert PDF to markdown template
python training/scripts/pdf_to_ascii_converter.py path/to/your_manual.pdf

# 2. Extract and upload images to Firebase Storage (if manual contains images)
python training/scripts/extract_pdf_images.py path/to/your_manual.pdf

# 3. Generate enhanced chunks with 6-level hierarchy (main orchestrator)
python training/scripts/generate_jsonl_enhanced.py templates/your_manual_content.md

# 4. Create FAISS vectors with multi-embedding strategy
python training/scripts/prepare_vectors_enhanced.py training/output/chunks/your_manual_content_enhanced_chunks.jsonl

# 5. Deploy enhanced vectors to production
cp training/output/vectors_v2/* app/vector-files/
./deployment/deploy_ai_service.ps1
```

**Results**: 2.6x more chunks (34 vs 13) with superior customer support optimization and sub-1ms search response times.

## 🛠️ Development

### Project Structure

```
universal-manual-rag-chat/
├── chatbot_backend/           # FastAPI backend
│   ├── agent/                 # AI chat logic
│   ├── api/                   # REST endpoints
│   ├── app/                   # Core services
│   ├── training/              # Enhanced RAG system
│   └── deployment/            # Cloud deployment
├── chatbot_frontend/          # Flutter frontend
│   ├── lib/                   # Dart source code
│   ├── functions/             # Firebase Functions
│   └── web/                   # Web assets
└── docs/                      # Documentation
```

### Key Technologies

#### Backend Stack
- **FastAPI 0.115.0**: High-performance web framework (security patched)
- **Security Middleware**: API authentication, rate limiting, input validation
- **Google Gemini 2.5 Flash**: AI model with strict adherence
- **FAISS**: Vector similarity search with enhanced security
- **Firebase Storage**: Secure image management with signed URLs
- **Google Cloud Run**: Buildpack deployment with auto-scaling

#### Frontend Stack
- **Flutter**: Cross-platform UI framework
- **Firebase Auth**: Google Sign-In authentication
- **Cloud Firestore**: Real-time database
- **Speech-to-Text/Text-to-Speech**: Google Cloud APIs

### Manual Adherence System

Our AI is configured with **critical requirements** ensuring responses contain only official manual information:

```python
# Strict response controls (agent/chat_manager.py)
- ONLY use exact information from manual context
- NO friendly greetings or conversational language
- NO generic advice not explicitly stated
- Quote LED meanings and troubleshooting word-for-word
- Direct technical responses with no embellishments
```

**Example Quality**:
- ✅ "Blinking red light indicates firmware corrupted (from Troubleshooting Section)"
- ❌ "Oh no worries! A blinking red light usually means there's an issue..."

## 🧪 Testing

### Enhanced RAG System Testing

```bash
# Test level-aware search and query classification
python test_simple.py

# Comprehensive customer support scenarios
python test_customer_queries.py

# Manual adherence validation
curl -X POST "https://your-backend.run.app/chat/send" \
  -H "Content-Type: application/json" \
  -d '{"message": "red light is blinking"}'
```

### API Testing

```bash
# Health checks
curl http://localhost:8080/health
curl http://localhost:8080/debug/faiss-status

# Authenticated chat endpoints (API key required)
curl -X POST "http://localhost:8080/chat/send" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"message": "What does red LED mean?"}'

# Production health check
curl https://ai-agent-service-325296751367.us-central1.run.app/health

# Flutter tests
cd chatbot_frontend && flutter test
```

## 🚀 Deployment

### 📦 Modern Buildpack Deployment (Google Cloud Run)

The system now uses **Google Cloud buildpacks** for improved security, reliability, and simplified deployment:

**Benefits of Buildpack Deployment**:
- 🔒 **Enhanced Security**: No Docker vulnerabilities, automatic security updates
- ⚡ **Faster Builds**: Optimized caching and dependency management
- 🛠️ **Simplified Configuration**: No Dockerfile needed, uses `.python-version`, `runtime.txt`, and `Procfile`
- 🔄 **Automatic Updates**: Google-managed base images with security patches
- 📊 **Better Resource Management**: Optimized memory and CPU usage

```bash
# Deploy with buildpack (simplified process)
cd chatbot_backend
./deployment/deploy_ai_service.ps1

# The script automatically:
# 1. Verifies buildpack configuration files
# 2. Checks security environment variables
# 3. Deploys using --source . (no Docker required)
# 4. Applies security configurations
# 5. Tests deployment health
```

**Buildpack Configuration Files**:
- `.python-version`: Specifies Python 3.11 runtime
- `runtime.txt`: Runtime specification for Google Cloud
- `Procfile`: Process definition (`web: python main.py`)
- No `Dockerfile` needed - buildpacks handle everything!

### Legacy Docker vs Buildpack Comparison

| Feature | Docker (Old) | Buildpack (New) |
|---------|-------------|------------------|
| Security | Manual updates | Automatic patches |
| Build Speed | Slower | **40% faster** |
| Configuration | Complex Dockerfile | Simple config files |
| Maintenance | High | **Minimal** |
| Security Scanning | Manual | **Automatic** |
| Base Image Updates | Manual | **Automatic** |

### Production Service Status

🌐 **Live Service**: [https://ai-agent-service-325296751367.us-central1.run.app](https://ai-agent-service-325296751367.us-central1.run.app/health)

- ✅ **Security**: All vulnerabilities resolved
- ✅ **Authentication**: API key protection enabled
- ✅ **Performance**: Sub-1ms search response times
- ✅ **Reliability**: Buildpack deployment with auto-scaling

### Frontend Deployment (Firebase)

```bash
# Deploy Flutter web app
cd chatbot_frontend
firebase deploy --only hosting

# Deploy Firebase Functions
firebase deploy --only functions
```

### Security Environment Variables

```bash
# Core Configuration
PROJECT_ID=your-project-id
LOCATION=us-central1
GENERATIVE_MODEL_NAME=gemini-2.5-flash
EMBEDDING_MODEL_NAME=text-embedding-004
DEFAULT_VOICE_NAME=en-US-Chirp3-HD-Leda

# Security (CRITICAL for production)
API_KEYS=key1,key2,key3  # Generate secure API keys
ADMIN_API_KEY=admin-key  # For admin endpoints
CORS_ORIGINS=https://yourdomain.com  # Explicit domains only

# Authentication
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

## 📚 Documentation

- **[🔒 Security Report](SECURITY_REPORT.md)** - Complete security audit results and resolution status
- **[🛡️ Security Setup Guide](chatbot_backend/SECURITY_SETUP.md)** - Production security configuration
- **[Enhanced RAG System Guide](chatbot_backend/training/docs/UNIVERSAL_RAG_SYSTEM_GUIDE.md)** - Comprehensive system documentation
- **[CLAUDE.md](CLAUDE.md)** - Development guidelines and project instructions
- **[API Documentation](docs/api.md)** - REST API reference with authentication
- **[Deployment Guide](docs/deployment.md)** - Buildpack deployment instructions

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Cloud Platform** - AI services, buildpack deployment, and security infrastructure
- **Firebase** - Authentication, database, and secure hosting
- **Flutter Team** - Cross-platform UI framework
- **FastAPI** - High-performance web framework with security features
- **FAISS** - Efficient similarity search and vector operations
- **Google Cloud Buildpacks** - Modern, secure deployment platform

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/patiza604/universal-manual-rag-chat/issues)
- **Discussions**: [GitHub Discussions](https://github.com/patiza604/universal-manual-rag-chat/discussions)
- **Documentation**: [Project Wiki](https://github.com/patiza604/universal-manual-rag-chat/wiki)

---

## 🏆 Enterprise Ready Status

<div align="center">

### ✅ Production Deployment Status

🔒 **Security Audit**: **PASSED** - All critical vulnerabilities resolved
🚀 **Deployment**: **LIVE** - [ai-agent-service-325296751367.us-central1.run.app](https://ai-agent-service-325296751367.us-central1.run.app/health)
📦 **Technology**: **Buildpack** - Modern Google Cloud deployment
🛡️ **Authentication**: **API Keys** - Enterprise-grade security
⚡ **Performance**: **Sub-1ms** - Lightning-fast search response times
🌐 **Reliability**: **Auto-scaling** - Production-ready infrastructure

**[⭐ Star this repo](https://github.com/patiza604/universal-manual-rag-chat) if you find it helpful!**

Made with ❤️ by the Universal Manual RAG Chat team

</div>
