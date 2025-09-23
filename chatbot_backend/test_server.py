# Simple test server for frontend-backend communication testing
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Test Backend Server", version="1.0.0")

# Configure CORS to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Test backend server is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "server": "test_server",
        "version": "1.0.0"
    }

@app.post("/chat/send")
async def test_chat(message: dict):
    return {
        "response": f"Echo: {message.get('message', 'No message provided')}",
        "status": "success"
    }

@app.post("/chat/send-with-tts")
async def test_chat_with_tts(request: dict):
    message = request.get('message', 'No message provided')
    return {
        "response": {
            "parts": [
                {
                    "type": "text",
                    "text": f"Test response: {message}"
                }
            ]
        },
        "audio_generated": request.get('include_audio', False),
        "audio_data": None if not request.get('include_audio', False) else "fake_audio_data",
        "status": "success"
    }

if __name__ == "__main__":
    print("Starting test server on http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)