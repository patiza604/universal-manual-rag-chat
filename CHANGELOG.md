# Changelog

All notable changes to Universal Manual RAG Chat will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial changelog implementation
- Security policy documentation

### Changed
- Enhanced frontend documentation with comprehensive Flutter setup
- Updated placeholder URLs for production readiness

## [2.0.0] - 2025-09-23

### Added
- Enhanced Universal Customer Support RAG System with 4 intelligent search strategies
- Multi-embedding architecture (content, question, combined embeddings)
- Level-aware search weights (L0: 1.2x boost, QA: 1.3x boost)
- Query classification with 75% accuracy automatic routing
- Progressive complexity search (L0 → L1 → L2 → L4)
- Customer support metadata with 6 specialized fields
- Production Firebase service account integration
- Image management workflow with Firebase Storage
- Strict manual adherence system - AI responses limited to official manual content only

### Changed
- **BREAKING**: AI responses now strictly adhere to manual content (no generic advice)
- Updated frontend to connect to production Cloud Run backend
- Enhanced FAISS vector service with 34 chunks (2.6x improvement from 13)
- Performance optimized to <1ms search response times
- Updated prompt system to eliminate conversational language

### Fixed
- Frontend-backend connection issues preventing chat functionality
- 7 linting errors in pdf_to_ascii_converter.py
- Manual processing workflow and file cleanup

### Security
- Implemented secure image access with Firebase Storage signed URLs
- Enhanced authentication with Google Sign-In integration
- Service account-based Firebase Storage access

## [1.0.0] - 2025-09-20

### Added
- Initial release of Universal Manual RAG Chat platform
- Flutter frontend with Firebase integration
- Python FastAPI backend with Google Gemini 2.5 Flash
- Embedded FAISS vector search with local vector files
- Multimodal chat capabilities (speech-to-text, text-to-speech)
- Google Cloud Run deployment
- Firebase Authentication with Google Sign-In
- Firebase Firestore and Cloud Storage integration
- Comprehensive documentation and setup guides

### Technical Architecture
- Backend: FastAPI + Python 3.11+ with Google Cloud services
- Frontend: Flutter with Firebase SDK integration
- AI: Google Gemini with strict manual adherence
- Vector Search: FAISS with enhanced chunking system
- Deployment: Google Cloud Run + Firebase Functions

---

## Version History Summary

- **v2.0.0**: Enhanced Universal Customer Support RAG System with strict manual adherence
- **v1.0.0**: Initial production-ready AI assistant platform

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/patiza604/universal-manual-rag-chat/issues) page.