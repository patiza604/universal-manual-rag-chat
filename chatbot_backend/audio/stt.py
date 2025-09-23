# audio/stt.py
import base64
import subprocess
import tempfile
import os
from google.cloud import speech_v1p1beta1 as speech
import logging

logger = logging.getLogger(__name__)

def convert_webm_to_wav(webm_data: bytes) -> bytes:
    """Convert WebM audio to WAV format using ffmpeg"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as webm_file:
            webm_file.write(webm_data)
            webm_path = webm_file.name
        
        wav_path = webm_path.replace('.webm', '.wav')
        
        # Use ffmpeg to convert WebM to WAV
        cmd = [
            'ffmpeg',
            '-i', webm_path,
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-f', 'wav',
            wav_path,
            '-y'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg conversion failed: {result.stderr}")
            raise Exception(f"Audio conversion failed: {result.stderr}")
        
        # Read the converted WAV file
        with open(wav_path, 'rb') as wav_file:
            wav_data = wav_file.read()
        
        # Cleanup
        os.unlink(webm_path)
        os.unlink(wav_path)
        
        return wav_data
        
    except Exception as e:
        logger.error(f"WebM to WAV conversion failed: {e}")
        raise

def convert_speech_to_text(
    client: speech.SpeechClient,
    audio_data_base64: str,
    encoding: str,
    sample_rate: int,
    language_code: str,
    platform: str = "unknown"
) -> dict:
    """Convert speech to text with platform-specific handling"""
    
    if not client:
        raise ValueError("Speech-to-Text client not initialized")
    
    # Decode base64 audio
    audio_bytes = base64.b64decode(audio_data_base64)
    logger.info(f"Processing audio - Platform: {platform}, Size: {len(audio_bytes)} bytes, Encoding: {encoding}")
    
    # Handle WebM format from web browsers
    if platform == "web" and encoding == "WEBM_OPUS":
        logger.info("Converting WebM audio to WAV for transcription")
        try:
            audio_bytes = convert_webm_to_wav(audio_bytes)
            encoding = "LINEAR16"
            sample_rate = 16000
            logger.info(f"Converted to WAV - Size: {len(audio_bytes)} bytes")
        except Exception as e:
            logger.error(f"WebM conversion failed: {e}")
            raise ValueError(f"Failed to convert WebM audio: {str(e)}")
    
    # Map encoding strings to Speech API enums
    encoding_map = {
        "LINEAR16": speech.RecognitionConfig.AudioEncoding.LINEAR16,
        "FLAC": speech.RecognitionConfig.AudioEncoding.FLAC,
        "MULAW": speech.RecognitionConfig.AudioEncoding.MULAW,
        "AMR": speech.RecognitionConfig.AudioEncoding.AMR,
        "AMR_WB": speech.RecognitionConfig.AudioEncoding.AMR_WB,
        "OGG_OPUS": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        "SPEEX_WITH_HEADER_BYTE": speech.RecognitionConfig.AudioEncoding.SPEEX_WITH_HEADER_BYTE,
        "WEBM_OPUS": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
    }
    
    # Get the proper encoding enum
    audio_encoding = encoding_map.get(encoding)
    if not audio_encoding:
        # Default to LINEAR16 if encoding not recognized
        logger.warning(f"Unrecognized encoding: {encoding}, defaulting to LINEAR16")
        audio_encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
    
    # Configure recognition
    config = speech.RecognitionConfig(
        encoding=audio_encoding,
        sample_rate_hertz=sample_rate,
        language_code=language_code,
        enable_automatic_punctuation=True,
        model="latest_long",
        use_enhanced=True,
    )
    
    # Create audio object
    audio = speech.RecognitionAudio(content=audio_bytes)
    
    try:
        # Perform recognition
        logger.info("Sending audio to Speech-to-Text API...")
        response = client.recognize(config=config, audio=audio)
        
        # Process results
        transcript = ""
        confidence = 0.0
        
        for result in response.results:
            # Get the most likely transcript
            if result.alternatives:
                transcript += result.alternatives[0].transcript + " "
                if result.alternatives[0].confidence:
                    confidence = max(confidence, result.alternatives[0].confidence)
        
        transcript = transcript.strip()
        
        if not transcript:
            logger.warning("No transcript generated from audio")
            return {
                "transcript": "",
                "confidence": 0.0,
                "error": "No speech detected in audio"
            }
        
        logger.info(f"Transcription successful: '{transcript[:50]}...' (confidence: {confidence:.2f})")
        
        return {
            "transcript": transcript,
            "confidence": confidence
        }
        
    except Exception as e:
        logger.error(f"Speech-to-Text API error: {e}")
        raise