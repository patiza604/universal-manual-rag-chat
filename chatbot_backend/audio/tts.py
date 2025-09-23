# audio/tts.py
import time
from google.cloud import texttospeech
from google.api_core import retry
from google.api_core.exceptions import GoogleAPIError
import logging

logger = logging.getLogger(__name__)

@retry.Retry(
    initial=1.0,
    maximum=60.0,
    multiplier=2.0,
    deadline=300.0,
    predicate=retry.if_exception_type(GoogleAPIError)
)
def synthesize_speech_with_retry(
    client: texttospeech.TextToSpeechClient,
    synthesis_input: texttospeech.SynthesisInput,
    voice: texttospeech.VoiceSelectionParams,
    audio_config: texttospeech.AudioConfig,
    max_retries: int = 3
) -> texttospeech.SynthesizeSpeechResponse:
    """
    Synthesize speech with retry logic for handling transient errors.
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"TTS synthesis attempt {attempt + 1}/{max_retries}")
            
            # Make the synthesis request
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            logger.info("TTS synthesis successful")
            return response
            
        except Exception as e:
            last_error = e
            logger.error(f"TTS synthesis attempt {attempt + 1} failed: {str(e)}")
            
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + 0.5
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"All TTS synthesis attempts failed")
                raise last_error
    
    raise last_error or Exception("TTS synthesis failed after all retries")