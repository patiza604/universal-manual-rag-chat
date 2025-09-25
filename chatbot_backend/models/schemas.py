from pydantic import BaseModel, Field, validator
from typing import Optional
import re

class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message")

    @validator('message')
    def validate_message(cls, v):
        # Remove dangerous characters and patterns
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')

        # Check for potential injection patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',                # JavaScript protocol
            r'on\w+\s*=',                 # Event handlers
            r'data:text/html',            # Data URLs
            r'vbscript:',                 # VBScript
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE | re.DOTALL):
                raise ValueError('Message contains potentially dangerous content')

        return v.strip()

class TextToSpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    voice_name: str = Field(default="en-US-Chirp3-HD-Leda", pattern=r"^[a-zA-Z0-9\-_]+$")
    language_code: str = Field(default="en-US", pattern=r"^[a-z]{2}-[A-Z]{2}$")
    audio_encoding: str = Field(default="MP3", pattern=r"^(MP3|LINEAR16|OGG_OPUS)$")

    @validator('text')
    def validate_text(cls, v):
        return v.strip() if v else ""

class ChatWithTTSRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    tts_message: Optional[str] = Field(None, max_length=5000, description="Override text for TTS")
    include_audio: bool = True
    voice_name: str = Field(default="en-US-Chirp3-HD-Leda", pattern=r"^[a-zA-Z0-9\-_]+$")
    language_code: str = Field(default="en-US", pattern=r"^[a-z]{2}-[A-Z]{2}$")

    @validator('message')
    def validate_message(cls, v):
        # Apply same validation as MessageRequest
        return MessageRequest.validate_message(v)

class SpeechToTextRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    encoding: str
    sample_rate: int
    language_code: str = "en-US"
    platform: str