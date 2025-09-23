# Universal Manual RAG Chat

> **AI-powered universal manual customer support system with advanced RAG, multi-embedding search, and strict manual adherence**

[![Flutter](https://img.shields.io/badge/Flutter-02569B?style=for-the-badge&logo=flutter&logoColor=white)](https://flutter.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com)
[![Firebase](https://img.shields.io/badge/Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com)

## 🌟 Overview

Universal Manual RAG Chat is a cutting-edge AI customer support system that transforms any technical manual into an intelligent, interactive assistant. Built with **strict manual adherence**, it provides accurate, reliable responses exclusively from official documentation.

### 🎯 Key Features

- **🔍 Universal Manual Processing** - Works with any domain: electronics, automotive, software, appliances
- **🧠 Enhanced RAG Architecture** - 6-level chunk hierarchy with intelligent search strategies
- **🎙️ Multimodal Interface** - Voice input/output, text chat, and image support
- **⚡ Lightning Fast** - Sub-1ms search response times with FAISS vector search
- **🎯 Strict Manual Adherence** - Responses limited to official manual content only
- **📱 Cross-Platform** - Flutter web/mobile app with Firebase integration

### 🏗️ Architecture Highlights

- **4 Intelligent Search Strategies**: Quick facts, troubleshooting, setup, progressive
- **Multi-Embedding System**: Content, question, and combined embeddings
- **Level-Aware Search Weights**: L0 (1.2x boost), QA pairs (1.3x boost)
- **Query Classification**: 75% accuracy automatic routing
- **Production Ready**: Google Cloud Run deployment

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

# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py  # Runs on localhost:8080
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
- **FastAPI**: High-performance web framework
- **Google Gemini 2.5 Flash**: AI model with strict adherence
- **FAISS**: Vector similarity search
- **Firebase Storage**: Image management
- **Google Cloud Run**: Serverless deployment

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

# Chat endpoints
curl -X POST "http://localhost:8080/chat/send" \
  -H "Content-Type: application/json" \
  -d '{"message": "What does red LED mean?"}'

# Flutter tests
cd chatbot_frontend && flutter test
```

## 🚀 Deployment

### Backend Deployment (Google Cloud Run)

```bash
# Deploy AI service
cd chatbot_backend
./deployment/deploy_ai_service.ps1

# Update vectors in production
./deployment/update_vectors.ps1
```

### Frontend Deployment (Firebase)

```bash
# Deploy Flutter web app
cd chatbot_frontend
firebase deploy --only hosting

# Deploy Firebase Functions
firebase deploy --only functions
```

### Environment Variables

```bash
# Backend (.env)
PROJECT_ID=your-project-id
LOCATION=us-central1
GENERATIVE_MODEL_NAME=gemini-2.5-flash
EMBEDDING_MODEL_NAME=text-embedding-004
DEFAULT_VOICE_NAME=en-US-Chirp3-HD-Leda
```

## 📚 Documentation

- **[Enhanced RAG System Guide](chatbot_backend/training/docs/UNIVERSAL_RAG_SYSTEM_GUIDE.md)** - Comprehensive system documentation
- **[CLAUDE.md](CLAUDE.md)** - Development guidelines and project instructions
- **[API Documentation](docs/api.md)** - REST API reference
- **[Deployment Guide](docs/deployment.md)** - Production deployment instructions

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

- **Google Cloud Platform** - AI services and deployment infrastructure
- **Firebase** - Authentication, database, and hosting
- **Flutter Team** - Cross-platform UI framework
- **FastAPI** - High-performance web framework
- **FAISS** - Efficient similarity search

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/patiza604/universal-manual-rag-chat/issues)
- **Discussions**: [GitHub Discussions](https://github.com/patiza604/universal-manual-rag-chat/discussions)
- **Documentation**: [Project Wiki](https://github.com/patiza604/universal-manual-rag-chat/wiki)

---

<div align="center">

**[⭐ Star this repo](https://github.com/patiza604/universal-manual-rag-chat) if you find it helpful!**

Made with ❤️ by the Universal Manual RAG Chat team

</div>
