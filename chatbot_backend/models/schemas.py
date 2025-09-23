from pydantic import BaseModel
from typing import Optional

class MessageRequest(BaseModel):
    message: str

class TextToSpeechRequest(BaseModel):
    text: str
    voice_name: str = "en-US-Chirp3-HD-Leda"
    language_code: str = "en-US"
    audio_encoding: str = "MP3"

class ChatWithTTSRequest(BaseModel):
    message: str
    tts_message: Optional[str] = None
    include_audio: bool = True
    voice_name: str = "en-US-Chirp3-HD-Leda"
    language_code: str = "en-US"

class SpeechToTextRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    encoding: str
    sample_rate: int
    language_code: str = "en-US"
    platform: str