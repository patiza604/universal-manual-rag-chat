from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from models.schemas import TextToSpeechRequest
from audio.clean_text import clean_for_tts
from google.cloud import texttospeech
import io

router = APIRouter()

@router.post("")
async def generate_speech(request: TextToSpeechRequest, req: Request):
    """Standalone TTS endpoint for converting text to speech."""
    tts_client = req.app.state.tts_client
    
    if not tts_client:
        raise HTTPException(status_code=500, detail="Text-to-Speech service not available.")

    try:
        # Clean the text for TTS
        cleaned_text = clean_for_tts(request.text)
        print(f"DEBUG: TTS endpoint - Original text: '{request.text[:100]}...'")
        print(f"DEBUG: TTS endpoint - Cleaned text: '{cleaned_text[:100]}...'")
        
        synthesis_input = texttospeech.SynthesisInput(text=cleaned_text)

        voice_params = texttospeech.VoiceSelectionParams(
            language_code=request.language_code,
            name=request.voice_name
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = tts_client.synthesize_speech(
            input=synthesis_input, 
            voice=voice_params, 
            audio_config=audio_config
        )

        return StreamingResponse(
            io.BytesIO(response.audio_content),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"}
        )
        
    except Exception as e:
        print(f"ERROR: TTS synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating speech: {e}")

@router.get("/voices")
async def get_available_voices(req: Request):
    """Get list of available TTS voices."""
    tts_client = req.app.state.tts_client
    
    if not tts_client:
        raise HTTPException(status_code=500, detail="Text-to-Speech service not available.")

    try:
        voices = tts_client.list_voices()
        
        english_voices = []
        for voice in voices.voices:
            if voice.language_codes and 'en-US' in voice.language_codes:
                english_voices.append({
                    "name": voice.name,
                    "language_codes": list(voice.language_codes),
                    "gender": voice.ssml_gender.name,
                    "natural_sample_rate_hertz": voice.natural_sample_rate_hertz
                })
        
        return {
            "voices": english_voices,
            "recommended_voices": [
                "en-US-Chirp3-HD-Leda",
                "en-US-Chirp3-HD-Umbriel",
                "en-US-Chirp3-HD-Charon",
                "Kore"
            ],
            "current_default": "en-US-Chirp3-HD-Leda"
        }
        
    except Exception as e:
        print(f"ERROR: Failed to get voices: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting voices: {e}")