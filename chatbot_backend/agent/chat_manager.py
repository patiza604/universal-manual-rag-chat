# agent/chat_manager.py
import json
import logging
from typing import List, Dict, Any, Callable, Optional
from urllib.parse import quote
from vertexai.generative_models import GenerativeModel, ChatSession
from app.config import GLOBAL_SAFETY_SETTINGS

logger = logging.getLogger(__name__)

class AIChatManager:
    """Enhanced AI Chat Manager with Firebase signed URL support"""
    
    def __init__(self, model: GenerativeModel):
        self._model = model
        self._chat: Optional[ChatSession] = None
        self._initialize_chat()
        logger.info("AI Chat Manager initialized successfully")
    
    def _initialize_chat(self):
        """Initialize a new chat session"""
        try:
            self._chat = self._model.start_chat(history=[])
            logger.info("New chat session started")
        except Exception as e:
            logger.error(f"Failed to initialize chat session: {e}")
            self._chat = None
    
    def send_message(self, 
                    message: str, 
                    query_embedding_func: Callable[[str], List[float]],
                    retrieval_func: Callable[[List[float], Optional[Dict[str, Any]]], List[Dict[str, Any]]],
                    firebase_service=None) -> str:
        """Send message and get structured JSON response with proper image handling"""
        
        if not self._chat:
            logger.error("Chat session not initialized")
            return json.dumps({
                "parts": [{
                    "type": "text",
                    "content": "Sorry, the chat system is not available right now."
                }]
            })
        
        try:
            logger.info(f"Processing message: '{message[:100]}...'")
            
            # Get query embedding
            query_embedding = query_embedding_func(message)
            if not query_embedding:
                logger.warning("Failed to generate query embedding")
                return json.dumps({
                    "parts": [{
                        "type": "text", 
                        "content": "I'm having trouble processing your question. Please try rephrasing it."
                    }]
                })
            
            # Retrieve relevant chunks (with optional query classification)
            relevant_chunks = retrieval_func(query_embedding, None)
            logger.info(f"Retrieved {len(relevant_chunks)} relevant chunks")

            # Debug: Log chunk details
            for i, chunk in enumerate(relevant_chunks[:3]):  # Show first 3 chunks
                content_preview = chunk.get('content', '')[:100] + "..." if len(chunk.get('content', '')) > 100 else chunk.get('content', '')
                logger.info(f"Chunk {i+1}: {chunk.get('title', 'No title')} - Content: {content_preview}")

            # Build enhanced prompt with RAG context
            enhanced_prompt = self._build_enhanced_prompt(message, relevant_chunks)
            
            # Get AI response
            response = self._chat.send_message(enhanced_prompt, safety_settings=GLOBAL_SAFETY_SETTINGS)
            response_text = response.text.strip()
            
            logger.info(f"AI response generated: {len(response_text)} characters")
            
            # Format structured response with RAG content and images
            structured_response = self._format_structured_response(response_text, relevant_chunks, firebase_service)
            
            return json.dumps(structured_response)
            
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            import traceback
            traceback.print_exc()
            
            return json.dumps({
                "parts": [{
                    "type": "text",
                    "content": "I encountered an error processing your request. Please try again."
                }]
            })
    
    def _build_enhanced_prompt(self, user_message: str, relevant_chunks: List[Dict[str, Any]]) -> str:
        """Build enhanced prompt with RAG context"""
        
        if not relevant_chunks:
            return f"""
User Question: {user_message}

Please provide a helpful response based on your knowledge about the manual procedures.
"""
        
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(relevant_chunks, 1):
            content = chunk.get('content', '').strip()
            title = chunk.get('title', 'Unknown Section')
            page = chunk.get('page_number', 'N/A')
            
            if content:
                context_parts.append(f"""
Context {i} (from {title}, Page {page}):
{content}
""")
        
        context_text = "\n".join(context_parts)

        # Debug: Log the context being sent
        logger.info(f"Context text length: {len(context_text)} chars")
        if context_text:
            logger.info(f"Context preview: {context_text[:200]}...")

        return f"""
You are a technical support assistant for the Orbi Mesh WiFi System manual. You MUST ONLY provide information that is directly stated in the official manual context below.

MANUAL CONTEXT:
{context_text}

User Question: {user_message}

CRITICAL REQUIREMENTS:
- Use ONLY the exact information from the manual context above
- Do NOT add friendly greetings, personal commentary, or conversational language
- Do NOT provide advice not explicitly stated in the manual
- Quote LED meanings and troubleshooting steps word-for-word from the manual
- If the manual doesn't contain the answer, respond: "That information is not found in the manual sections available to me."
- Reference the specific manual section name
- Be direct and factual - no embellishments

Provide a direct technical response using only the manual content above."""
    
    def _format_structured_response(self, ai_response: str, relevant_chunks: List[Dict[str, Any]], firebase_service=None) -> Dict[str, Any]:
        """Format AI response and RAG content into structured JSON with Firebase signed URLs"""
        
        response_parts = []
        
        # Add AI response as text
        if ai_response:
            response_parts.append({
                "type": "text",
                "content": ai_response
            })
        
        # Add ONE most relevant image from chunks
        processed_image_urls = set()  # Track processed image URLs
        image_added = False  # Only add one image per response
        
        for chunk in relevant_chunks:
            if image_added:  # Skip if we already added an image
                break
                
            try:
                # Check multiple possible image field names
                image_data = None
                image_description = chunk.get('image_description', 'CovernuCover image for the manual')
                
                # Try different image field names that might exist in your metadata
                possible_image_fields = [
                    'image',
                    'image_uri', 
                    'image_url',
                    'image_path',
                    'image_filename',
                    'image_gcs_uri',
                    'image_firebase_url'
                ]
                
                for field_name in possible_image_fields:
                    if chunk.get(field_name):
                        image_data = chunk.get(field_name)
                        logger.info(f"Found image data in field '{field_name}': {image_data}")
                        break
                
                if image_data:
                    # Handle different types of image data
                    image_url = None
                    
                    if isinstance(image_data, str):
                        # String - could be filename or URL
                        if image_data.startswith('http'):
                            image_url = image_data
                        else:
                            # It's a filename, build Firebase signed URL
                            image_url = self._build_firebase_image_url(image_data, firebase_service)
                    elif isinstance(image_data, dict):
                        # Handle dict structure properly
                        # First try to get existing URLs
                        image_url = (image_data.get('firebase_url') or 
                                   image_data.get('url') or 
                                   image_data.get('uri') or
                                   image_data.get('downloadUrl'))
                        
                        # If no URL found, try to build from filename with signed URL
                        if not image_url:
                            filename = (image_data.get('filename') or 
                                      image_data.get('image_filename') or
                                      image_data.get('name'))
                            if filename:
                                logger.info(f"Building signed URL from filename: {filename}")
                                image_url = self._build_firebase_image_url(filename, firebase_service)
                        
                        # Add image if we have a valid URL and haven't processed it yet
                        if image_url and image_url not in processed_image_urls:
                            response_parts.append({
                                "type": "image",
                                "uri": image_url,
                                "alt": image_description
                            })
                            processed_image_urls.add(image_url)
                            image_added = True  # Mark that we've added an image
                            logger.info(f"✅ Added signed image URL to response: {image_url}")  # Show full URL
                        else:
                            logger.warning(f"Could not build valid signed image URL from: {image_data}")

                        # Update description if available in dict
                        if image_data.get('description'):
                            image_description = image_data.get('description')
                        else:
                            # Other types - try to convert to string
                            image_url = self._build_firebase_image_url(str(image_data), firebase_service)
                    
                    # Add image if we have a valid URL and haven't processed it yet
                    if image_url and image_url not in processed_image_urls:
                        response_parts.append({
                            "type": "image",
                            "uri": image_url,
                            "alt": image_description
                        })
                        processed_image_urls.add(image_url)
                        image_added = True  # Mark that we've added an image
                        logger.info(f"Added signed image URL to response: {image_url[:100]}...")
                    else:
                        logger.warning(f"Could not build valid signed image URL from: {image_data}")
                        
            except Exception as e:
                logger.error(f"Error processing image from chunk: {e}")
                continue
        
        logger.info(f"Response contains {len(response_parts)} parts ({len([p for p in response_parts if p['type'] == 'image'])} images)")
        return {"parts": response_parts}

    def _build_firebase_image_url(self, image_filename: str, firebase_service=None) -> Optional[str]:
        """Build Firebase Storage signed URL from filename with path discovery"""
        if not image_filename:
            return None
        
        try:
            # If it's already a complete URL, return as-is
            if image_filename.startswith('http'):
                return image_filename
            
            # Handle base64 images
            if image_filename.startswith('data:image/'):
                return image_filename
            
            # Clean the filename - REMOVE any existing path prefixes
            clean_filename = str(image_filename).strip().lstrip('/')
            
            # Remove any existing path prefixes that might be in the filename
            if clean_filename.startswith('ai_images/manual001/'):
                clean_filename = clean_filename.replace('ai_images/manual001/', '')
            elif clean_filename.startswith('ai_images/'):
                clean_filename = clean_filename.replace('ai_images/', '')
            elif clean_filename.startswith('manual/'):
                clean_filename = clean_filename.replace('manual001/', '')
            
            logger.info(f"🔍 Processing image filename: '{image_filename}' -> cleaned: '{clean_filename}'")
            
            if firebase_service and hasattr(firebase_service, 'generate_signed_url'):
                # Pass just the clean filename to Firebase service
                # The service will handle path building internally
                signed_url = firebase_service.generate_signed_url(clean_filename)
                if signed_url:
                    logger.info(f"✅ Generated signed URL for '{clean_filename}' -> '{signed_url[:100]}...'")
                    return signed_url
                else:
                    logger.warning(f"❌ Failed to generate signed URL for '{clean_filename}'")
                    return None
            
            # Fallback to public URL (won't work for private storage)
            logger.warning("Firebase service not available, using fallback public URL")
            encoded_path = quote(f'ai_images/manual001/{clean_filename}', safe='/')
            firebase_url = f'https://firebasestorage.googleapis.com/v0/b/ai-chatbot-beb8da.firebasestorage.app/o/{encoded_path}?alt=media'
            return firebase_url
            
        except Exception as e:
            logger.error(f"Error building Firebase image URL for '{image_filename}': {e}")
            return None
    
    def format_rag_content_for_response(self, relevant_chunks: List[Dict[str, Any]], firebase_service=None) -> Dict[str, Any]:
        """Format RAG content into structured response with Firebase signed URLs"""
        try:
            response_parts = []
            processed_image_urls = set()  # Track URLs instead of objects
            
            for chunk in relevant_chunks:
                # Add text content
                content = chunk.get('content', '').strip()
                if content:
                    response_parts.append({
                        "type": "text",
                        "content": content
                    })
                
                # Handle images safely with signed URLs
                try:
                    image_data = chunk.get('image')
                    if image_data:
                        image_url = None
                        
                        if isinstance(image_data, str):
                            image_url = self._build_firebase_image_url(image_data, firebase_service)
                        elif isinstance(image_data, dict):
                            # Try existing URLs first
                            image_url = (image_data.get('firebase_url') or 
                                       image_data.get('url') or 
                                       image_data.get('uri'))
                            
                            # If no URL, build from filename
                            if not image_url:
                                filename = image_data.get('filename')
                                if filename:
                                    image_url = self._build_firebase_image_url(filename, firebase_service)
                        
                        if image_url and image_url not in processed_image_urls:
                            response_parts.append({
                                "type": "image",
                                "uri": image_url,
                                "alt": chunk.get('image_description', 'Equipment diagram')
                            })
                            processed_image_urls.add(image_url)
                            
                except Exception as e:
                    logger.error(f"Error processing image in format_rag_content: {e}")
                    continue
            
            return {"parts": response_parts}
            
        except Exception as e:
            logger.error(f"Error formatting RAG content: {e}")
            return {
                "parts": [{
                    "type": "text",
                    "content": "I encountered an error processing the retrieved information."
                }]
            }
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get chat history in a structured format"""
        if not self._chat or not hasattr(self._chat, 'history'):
            return []
        
        try:
            history = []
            for message in self._chat.history:
                if hasattr(message, 'role') and hasattr(message, 'parts'):
                    # Convert message parts to our format
                    parts = []
                    for part in message.parts:
                        if hasattr(part, 'text'):
                            parts.append({
                                "type": "text",
                                "content": part.text
                            })
                    
                    if parts:
                        history.append({
                            "role": message.role,
                            "parts": parts,
                            "timestamp": getattr(message, 'timestamp', None)
                        })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    def reset_chat(self) -> Dict[str, str]:
        """Reset the chat session"""
        try:
            self._initialize_chat()
            logger.info("Chat session reset successfully")
            return {"message": "Chat session has been reset."}
        except Exception as e:
            logger.error(f"Error resetting chat: {e}")
            return {"message": "Failed to reset chat session.", "error": str(e)}
    
    def get_chat_status(self) -> Dict[str, Any]:
        """Get current chat session status"""
        return {
            "chat_initialized": self._chat is not None,
            "model_available": self._model is not None,
            "session_active": self._chat is not None and hasattr(self._chat, 'history'),
            "message_count": len(self._chat.history) if self._chat and hasattr(self._chat, 'history') else 0
        }
    
    def validate_and_clean_response(self, response_text: str) -> str:
        """Validate and clean AI response text"""
        if not response_text:
            return "I don't have enough information to provide a helpful response."
        
        # Remove any potential JSON formatting issues
        cleaned = response_text.strip()
        
        # Remove markdown code blocks if present
        if cleaned.startswith('```') and cleaned.endswith('```'):
            lines = cleaned.split('\n')
            if len(lines) > 2:
                cleaned = '\n'.join(lines[1:-1])
        
        return cleaned
    
    def extract_technical_terms(self, text: str) -> List[str]:
        """Extract technical terms from text for enhanced responses"""
        # Common terms
        technical_terms = [
            'product', 'feature', 'component', 'accessory', 'settings',
            'setup', 'installation', 'operation', 'guidelines', 'troubleshooting',
            'maintenance', 'safety', 'support', 'diagram', 'model',
            'power', 'indicator'
]
        
        found_terms = []
        text_lower = text.lower()
        
        for term in technical_terms:
            if term in text_lower:
                found_terms.append(term)
        
        return found_terms
    
    def enhance_response_with_context(self, response: str, chunks: List[Dict[str, Any]]) -> str:
        """Enhance response with additional context from chunks"""
        try:
            # Add page references if available
            page_refs = []
            for chunk in chunks:
                page = chunk.get('page_number')
                title = chunk.get('title', 'Manual001')
                if page and page != 'N/A':
                    page_refs.append(f"{title} (Page {page})")
            
            if page_refs:
                unique_refs = list(set(page_refs))
                if len(unique_refs) <= 3:  # Don't overwhelm with too many references
                    ref_text = ", ".join(unique_refs)
                    response += f"\n\n*Reference: {ref_text}*"
            
            return response
            
        except Exception as e:
            logger.error(f"Error enhancing response with context: {e}")
            return response