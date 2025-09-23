# api/routes_chat.py - Fixed version
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from models.schemas import MessageRequest, ChatWithTTSRequest
from audio.clean_text import clean_for_tts
from audio.tts import synthesize_speech_with_retry
from agent.embedding import get_query_embedding
from agent.retrieval import retrieve_relevant_chunks
from google.cloud import texttospeech
import base64
import traceback
import json
import requests
import io

router = APIRouter()

# api/routes_chat.py - Fix both endpoints to pass firebase_service
@router.post("/send")
async def send_chat_message(request: MessageRequest, req: Request):
    """Endpoint to send a message and get a structured JSON response using RAG."""
    chat_manager = req.app.state.chat_manager
    embedding_model = req.app.state.embedding_model
    faiss_service = req.app.state.faiss_service
    firebase_service = req.app.state.firebase_service  # Add this line
    
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="AI Agent Service is not fully initialized.")
    
    if faiss_service is None:
        raise HTTPException(status_code=503, detail="FAISS service is not available.")
    
    print(f"DEBUG: /chat/send endpoint called with message: '{request.message}'")
    
    try:
        # Create wrapper functions for chat manager
        def query_embedding_func(text):
            return get_query_embedding(embedding_model, text)
        
        def retrieval_func(query_embedding, query_classification=None):
            return retrieve_relevant_chunks(
                query_embedding=query_embedding, 
                faiss_service=faiss_service,
                query_classification=query_classification
            )
        
        # Get AI response (now returns structured JSON) with firebase_service
        structured_response = chat_manager.send_message(
            request.message, 
            query_embedding_func,
            retrieval_func,
            firebase_service  # Add this parameter
        )
        print(f"DEBUG: Structured response generated: '{structured_response[:200]}...'")
        
        # Parse the JSON to validate it
        try:
            parsed_response = json.loads(structured_response)
            return {"response": parsed_response}
        except json.JSONDecodeError:
            print("WARNING: Failed to parse structured response as JSON, falling back to plain text")
            return {"response": {"parts": [{"type": "text", "content": structured_response}]}}
        
    except Exception as e:
        print(f"ERROR: Exception in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-with-tts")
async def send_chat_message_with_tts(request: ChatWithTTSRequest, req: Request):
    """Endpoint to send a message and get both structured JSON and audio response."""
    chat_manager = req.app.state.chat_manager
    embedding_model = req.app.state.embedding_model
    faiss_service = req.app.state.faiss_service
    tts_client = req.app.state.tts_client
    firebase_service = req.app.state.firebase_service  # This should already be here from my previous code
    
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="AI Agent Service is not fully initialized.")
    
    if faiss_service is None:
        raise HTTPException(status_code=503, detail="FAISS service is not available.")
    
    if tts_client is None:
        raise HTTPException(status_code=503, detail="Text-to-Speech service not available.")
    
    print(f"DEBUG: /chat/send-with-tts endpoint called with message: '{request.message}'")
    print(f"DEBUG: Firebase service available: {firebase_service is not None}")
    
    try:
        # Create wrapper functions
        def query_embedding_func(text):
            return get_query_embedding(embedding_model, text)
        
        def retrieval_func(query_embedding, query_classification=None):
            return retrieve_relevant_chunks(
                query_embedding=query_embedding,
                faiss_service=faiss_service,
                query_classification=query_classification
            )
        
        # Get AI response with firebase_service for signed URLs
        structured_response = chat_manager.send_message(
            request.message,
            query_embedding_func,
            retrieval_func,
            firebase_service  # Make sure this is passed
        )
        print(f"DEBUG: Structured response generated: '{structured_response[:200]}...'")
        
        # Rest of the TTS function remains the same...
        # Parse the JSON response
        try:
            parsed_response = json.loads(structured_response)
        except json.JSONDecodeError:
            parsed_response = {"parts": [{"type": "text", "content": structured_response}]}
        
        response_data = {
            "response": parsed_response,
            "audio_generated": False,
            "audio_data": None
        }
        
        # Generate TTS if requested
        if request.include_audio:
            try:
                print(f"DEBUG: Generating TTS audio with voice: {request.voice_name}")
                
                # Extract text content from structured response for TTS
                if request.tts_message:
                    tts_text = request.tts_message
                else:
                    # Extract text from parts for TTS
                    text_parts = []
                    for part in parsed_response.get('parts', []):
                        if part.get('type') == 'text':
                            text_parts.append(part.get('content', ''))
                    tts_text = ' '.join(text_parts)
                    tts_text = clean_for_tts(tts_text)
                
                print(f"DEBUG: TTS text length: {len(tts_text)}")
                print(f"DEBUG: TTS text preview: '{tts_text[:100]}...'")
                
                # Create synthesis input
                synthesis_input = texttospeech.SynthesisInput(text=tts_text)
                
                # Configure voice
                voice_params = texttospeech.VoiceSelectionParams(
                    language_code=request.language_code,
                    name=request.voice_name
                )
                
                # Configure audio output
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                )
                
                try:
                    # Try with retry logic
                    tts_response = synthesize_speech_with_retry(
                        tts_client, synthesis_input, voice_params, audio_config
                    )
                except Exception as retry_error:
                    print(f"DEBUG: Retry logic failed, attempting direct synthesis: {retry_error}")
                    # Fallback to direct synthesis
                    tts_response = tts_client.synthesize_speech(
                        input=synthesis_input,
                        voice=voice_params,
                        audio_config=audio_config
                    )
                
                audio_base64 = base64.b64encode(tts_response.audio_content).decode('utf-8')
                
                response_data["audio_generated"] = True
                response_data["audio_data"] = audio_base64
                response_data["tts_text_used"] = tts_text
                
                print(f"DEBUG: TTS audio generated successfully with {request.voice_name} (size: {len(tts_response.audio_content)} bytes)")
                
            except Exception as tts_error:
                print(f"ERROR: TTS generation failed: {tts_error}")
                traceback.print_exc()
                response_data["audio_generated"] = False
                response_data["audio_error"] = str(tts_error)
        
        return response_data
        
    except Exception as e:
        print(f"ERROR: Exception in chat-with-tts endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/history")
async def get_chat_history(req: Request):
    """Endpoint to retrieve the current chat history."""
    chat_manager = req.app.state.chat_manager
    if chat_manager is None:
        return {"history": []}
    print("DEBUG: /chat/history endpoint called.")
    history = chat_manager.get_history()
    return {"history": history}

@router.post("/reset")
async def reset_chat_session(req: Request):
    """Endpoint to reset the current chat session."""
    chat_manager = req.app.state.chat_manager
    if chat_manager is None:
        return {"message": "Model not initialized, cannot reset chat."}
    print("DEBUG: /chat/reset endpoint called.")
    return chat_manager.reset_chat()

@router.options("/send-with-tts")
async def preflight_send_with_tts():
    return {}

@router.get("/image-proxy")
async def image_proxy(url: str):
    """Proxy endpoint to serve Firebase Storage images and bypass CORS"""
    try:
        if not url.startswith('https://firebasestorage.googleapis.com/'):
            raise HTTPException(status_code=400, detail="Invalid image URL")
        
        response = requests.get(url)
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return StreamingResponse(
            io.BytesIO(response.content),
            media_type=response.headers.get("content-type", "image/png"),
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        print(f"ERROR: Image proxy failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch image")