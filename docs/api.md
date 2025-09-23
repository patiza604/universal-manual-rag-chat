# API Documentation

## Base URL

**Production**: `https://ai-agent-service-325296751367.us-central1.run.app`
**Development**: `http://localhost:8080`

## Authentication

Currently, the API uses simple request-based authentication. Future versions will include API key authentication.

## Endpoints

### Chat Endpoints

#### Send Chat Message

Send a message to the AI assistant and receive a response.

```http
POST /chat/send
Content-Type: application/json

{
  "message": "What does red LED mean?"
}
```

**Response:**
```json
{
  "response": "Blinking red light indicates firmware corrupted (from Troubleshooting Indicators & Connectivity)",
  "search_strategy": "quick_facts",
  "chunks_used": 3,
  "response_time_ms": 0.8
}
```

### Speech-to-Text (STT)

#### Upload Audio for Transcription

Convert audio to text using Google Cloud Speech-to-Text.

```http
POST /stt/transcribe
Content-Type: multipart/form-data

file: [audio file]
```

**Supported formats**: WAV, MP3, FLAC, OGG
**Max file size**: 10MB

**Response:**
```json
{
  "transcript": "What does red LED mean?",
  "confidence": 0.95
}
```

### Text-to-Speech (TTS)

#### Generate Audio from Text

Convert text to speech using Google Cloud Text-to-Speech.

```http
POST /tts/synthesize
Content-Type: application/json

{
  "text": "Blinking red light indicates firmware corrupted",
  "voice_name": "en-US-Chirp3-HD-Leda"
}
```

**Response:**
```json
{
  "audio_url": "https://storage.googleapis.com/bucket/audio_12345.mp3",
  "duration_seconds": 3.2
}
```

### Debug Endpoints

#### Health Check

Check if the service is running.

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-23T10:30:00Z",
  "version": "1.0.0"
}
```

#### FAISS Status

Check the status of the vector search system.

```http
GET /debug/faiss-status
```

**Response:**
```json
{
  "status": "loaded",
  "total_vectors": 34,
  "index_type": "IndexFlatL2",
  "embedding_dimension": 768,
  "enhanced_features": {
    "level_aware_search": true,
    "multi_embedding_support": true,
    "query_classification": true,
    "search_strategies": 4
  }
}
```

#### Firebase Status

Check Firebase Storage connectivity.

```http
GET /debug/firebase-status
```

**Response:**
```json
{
  "status": "connected",
  "bucket": "ai-chatbot-472322.firebasestorage.app",
  "service_account": "active",
  "image_proxy_enabled": true
}
```

### Image Proxy (Development)

#### Serve Manual Images

Proxy Firebase Storage images with CORS headers for development.

```http
GET /image-proxy/{filename}
```

**Example:**
```http
GET /image-proxy/modem_router_cabling.png
```

**Response**: Image file with proper CORS headers

## Enhanced RAG System

### Query Classification

The system automatically classifies queries into four strategies:

1. **quick_facts** - Instant answers (LED meanings, indicators)
2. **troubleshooting** - Problem-solving workflows
3. **setup** - Step-by-step procedures
4. **progressive** - Adaptive complexity search

### Search Strategies

#### Quick Facts Strategy
- **Target**: L0 chunks (quick facts)
- **Boost weight**: 1.2x
- **Use case**: "What does red LED mean?"

#### Troubleshooting Strategy
- **Search order**: L0 → L2 → L1 → L4
- **Boost weight**: QA pairs get 1.3x
- **Use case**: "WiFi not working"

#### Setup Strategy
- **Target**: L1 chunks (procedures)
- **Include**: Prerequisites and steps
- **Use case**: "How to setup router"

#### Progressive Strategy
- **Adaptive**: Adjusts based on query complexity
- **Multi-level**: Combines multiple chunk types
- **Use case**: Complex technical questions

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input format",
    "details": "Message field is required"
  },
  "timestamp": "2025-09-23T10:30:00Z"
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Invalid request format | 400 |
| `FAISS_ERROR` | Vector search failure | 500 |
| `AI_SERVICE_ERROR` | Gemini API failure | 500 |
| `AUDIO_PROCESSING_ERROR` | STT/TTS failure | 500 |
| `FIREBASE_ERROR` | Storage access failure | 500 |

## Rate Limiting

Current limits (subject to change):
- **Chat**: 100 requests/minute per IP
- **STT**: 20 requests/minute per IP
- **TTS**: 50 requests/minute per IP

## Response Times

Target performance metrics:
- **Vector search**: <1ms
- **Chat response**: <2s
- **STT processing**: <3s
- **TTS generation**: <2s

## Examples

### Complete Chat Flow

```bash
# Send a troubleshooting query
curl -X POST "https://ai-agent-service-325296751367.us-central1.run.app/chat/send" \
  -H "Content-Type: application/json" \
  -d '{"message": "WiFi connection keeps dropping"}'

# Response
{
  "response": "Check cable connections between modem and router. Ensure all cables are securely connected (from Network Setup Section)",
  "search_strategy": "troubleshooting",
  "chunks_used": 5,
  "manual_sections": ["Network Setup", "Troubleshooting Connectivity"],
  "response_time_ms": 1.2
}
```

### Manual Adherence Example

```bash
# Query that should return only manual content
curl -X POST "https://ai-agent-service-325296751367.us-central1.run.app/chat/send" \
  -H "Content-Type: application/json" \
  -d '{"message": "router not working"}'

# Correct response (manual content only)
{
  "response": "Power LED solid red indicates no internet connection. Check modem cable connection (from LED Status Indicators)",
  "search_strategy": "troubleshooting"
}

# Incorrect response would include:
# "I'm sorry to hear you're having issues! Let me help you troubleshoot..."
```

## SDK Integration

### JavaScript/TypeScript

```typescript
class UniversalRAGClient {
  constructor(private baseUrl: string) {}

  async sendMessage(message: string) {
    const response = await fetch(`${this.baseUrl}/chat/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    return response.json();
  }

  async transcribeAudio(audioFile: File) {
    const formData = new FormData();
    formData.append('file', audioFile);

    const response = await fetch(`${this.baseUrl}/stt/transcribe`, {
      method: 'POST',
      body: formData
    });
    return response.json();
  }
}
```

### Python

```python
import requests

class UniversalRAGClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def send_message(self, message: str):
        response = requests.post(
            f"{self.base_url}/chat/send",
            json={"message": message}
        )
        return response.json()

    def transcribe_audio(self, audio_file_path: str):
        with open(audio_file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.base_url}/stt/transcribe",
                files=files
            )
        return response.json()
```

## Changelog

### v1.0.0 (Current)
- Enhanced Universal Customer Support RAG System
- 4 intelligent search strategies
- Multi-embedding architecture
- Level-aware search weights
- Strict manual adherence
- 34 enhanced chunks vs 13 original

### Future Versions
- API key authentication
- WebSocket support for real-time chat
- Batch processing endpoints
- Analytics and metrics API