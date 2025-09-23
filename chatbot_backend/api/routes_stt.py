# api/routes_stt.py
from fastapi import APIRouter, HTTPException, Request
from models.schemas import SpeechToTextRequest
from audio.stt import convert_speech_to_text
import base64
import traceback
import subprocess

router = APIRouter()

@router.post("/speech-to-text")
async def speech_to_text(request: SpeechToTextRequest, req: Request):
    """Convert speech audio to text using Google Speech-to-Text."""
    speech_client = req.app.state.speech_client
    
    if not speech_client:
        # Check if the service was initialized
        print("ERROR: Speech-to-Text client is None")
        print(f"DEBUG: App state keys: {list(req.app.state.__dict__.keys())}")
        raise HTTPException(status_code=500, detail="Speech-to-Text service not available.")
    
    try:
        # Validate request
        if not request.audio_data:
            raise HTTPException(status_code=400, detail="No audio data provided")
        
        # Log request details
        print(f"DEBUG: STT request - Platform: {request.platform}, Encoding: {request.encoding}, Sample rate: {request.sample_rate}")
        
        # Decode and check audio size
        try:
            audio_bytes = base64.b64decode(request.audio_data)
            print(f"DEBUG: Audio validation - Size: {len(audio_bytes)} bytes")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 audio data: {str(e)}")
        
        if len(audio_bytes) < 100:
            raise HTTPException(status_code=400, detail="Audio data is too short for transcription")
        
        # Process transcription
        result = convert_speech_to_text(
            speech_client,
            request.audio_data,
            request.encoding,
            request.sample_rate,
            request.language_code,
            request.platform
        )
        
        print(f"DEBUG: Transcription successful: {result}")
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        print(f"ERROR: Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Audio conversion failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error converting audio format for transcription.")
    except Exception as e:
        print(f"ERROR: Speech-to-text conversion failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error converting speech to text: {str(e)}")