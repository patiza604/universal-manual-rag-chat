# agent/retrieval.py - Fixed version
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from app.config import EMBEDDING_QUANT, DEFAULT_LANGUAGE
import logging

logger = logging.getLogger(__name__)

def retrieve_relevant_chunks(
    query_embedding: List[float], 
    faiss_service, 
    query_classification: Dict[str, Any] = None,
    num_neighbors: int = None,
    source_type_filter: Optional[str] = None,
    language_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Enhanced retrieval with dynamic logic and filtering"""
    
    if query_embedding is None:
        logger.warning("No query embedding provided.")
        return []
    
    if faiss_service is None:
        logger.error("FAISS service not provided")
        return []
    
    # Extract classification info if provided
    if query_classification:
        query_type = query_classification.get('type', 'simple')
        estimated_chunks = query_classification.get('estimated_chunks')
        classification_method = query_classification.get('method', 'unknown')
        
        logger.info(f"Using {classification_method} classification: {query_type} query, estimated {estimated_chunks} chunks")
    else:
        # Legacy mode - use provided num_neighbors or default
        query_type = 'simple'
        estimated_chunks = num_neighbors or EMBEDDING_QUANT
        classification_method = 'legacy'
        
        logger.info(f"Legacy mode: using {estimated_chunks} chunks")
    
    # Set default language filter if not provided
    if language_filter is None:
        language_filter = DEFAULT_LANGUAGE
    
    try:
        # Check if FAISS service supports dynamic search
        if hasattr(faiss_service, 'search_dynamic'):
            # Use enhanced dynamic search
            results = faiss_service.search_dynamic(
                query_embedding=query_embedding,
                query_type=query_type,
                estimated_chunks=estimated_chunks,
                source_type_filter=source_type_filter,
                language_filter=language_filter
            )
            
            logger.info(f"Dynamic search returned {len(results)} chunks")
        else:
            # Fallback to basic search
            k = estimated_chunks or EMBEDDING_QUANT
            results = faiss_service.search(query_embedding, k)
            
            # Apply post-search filtering
            if source_type_filter or language_filter:
                filtered_results = []
                for chunk in results:
                    if source_type_filter and chunk.get('source_type') != source_type_filter:
                        continue
                    if language_filter and chunk.get('language') != language_filter:
                        continue
                    filtered_results.append(chunk)
                results = filtered_results
            
            logger.info(f"Basic search with filtering returned {len(results)} chunks")

        # Enhanced chunk processing
        enhanced_chunks = []
        for chunk in results:
            enhanced_chunk = process_retrieved_chunk(chunk)
            enhanced_chunks.append(enhanced_chunk)

        # Sort by relevance score
        enhanced_chunks.sort(key=lambda x: x.get('similarity_score', 0.0), reverse=True)

        logger.info(f"Processed and sorted {len(enhanced_chunks)} enhanced chunks")
        return enhanced_chunks

    except Exception as e:
        logger.error(f"Enhanced retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return []

# agent/retrieval.py - Updated image URL building
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from app.config import EMBEDDING_QUANT, DEFAULT_LANGUAGE
import logging

logger = logging.getLogger(__name__)

def build_firebase_image_url(image_filename: str) -> Optional[str]:
    """Build Firebase Storage signed URL from filename"""
    if not image_filename:
        return None
    
    try:
        # If it's already a complete URL, return as-is
        if isinstance(image_filename, str) and image_filename.startswith('http'):
            logger.info(f"Image already has complete URL: {image_filename}")
            return image_filename
        
        # Handle base64 images
        if isinstance(image_filename, str) and image_filename.startswith('data:image/'):
            return image_filename
        
        # Convert to string if it's not already
        if not isinstance(image_filename, str):
            image_filename = str(image_filename)
        
        # Clean the filename
        clean_filename = image_filename.strip().lstrip('/')
        
        # Build the correct path structure for manual images
        # Check different possible path structures
        if not clean_filename.startswith('ai_images/'):
            if clean_filename.startswith('manual001/'):
                clean_filename = f'ai_images/{clean_filename}'
            else:
                clean_filename = f'ai_images/manual001/{clean_filename}'
        
        # URL encode the path (but keep forward slashes)
        encoded_path = quote(clean_filename, safe='/')
        
        # Build Firebase Storage URL with correct format
        # Using .firebasestorage.app domain as shown in your example
        firebase_url = f'https://firebasestorage.googleapis.com/v0/b/ai-chatbot-beb8d.firebasestorage.app/o/{encoded_path}?alt=media'
        
        logger.info(f"Built Firebase URL from '{image_filename}' -> '{firebase_url}'")
        return firebase_url
        
    except Exception as e:
        logger.error(f"Error building Firebase image URL for '{image_filename}': {e}")
        return None

def process_retrieved_chunk(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """Process and enhance a retrieved chunk with standardized fields"""
    try:
        # Ensure all required fields are present with defaults
        enhanced_chunk = {
            # Core identification
            'id': chunk.get('id', 'unknown'),
            'section_id': chunk.get('section_id', 'unknown'),
            'chunk_order': chunk.get('chunk_order', 0),
            
            # Content fields
            'content': chunk.get('content', chunk.get('original_text_chunk', '')),
            'original_text_chunk': chunk.get('original_text_chunk', chunk.get('content', '')),
            'summary': chunk.get('summary', ''),
            
            # Document metadata
            'title': chunk.get('title', 'Unknown Document'),
            'subtitle': chunk.get('subtitle', 'N/A Subtitle'),
            'page_number': str(chunk.get('page_number', 'N/A')),
            'version': chunk.get('version', 'N/A Version'),
            
            # Classification
            'source_type': chunk.get('source_type', 'unknown'),
            'language': chunk.get('language', DEFAULT_LANGUAGE),
            'is_complete_section': chunk.get('is_complete_section', False),
            
            # Search metadata
            'distance': chunk.get('distance', 0.0),
            'similarity_score': chunk.get('similarity_score', chunk.get('distance', 0.0)),
            'chunk_index': chunk.get('chunk_index', -1),
            
            # Relationship data
            'keywords': chunk.get('keywords', []),
            'related_sections': chunk.get('related_sections', []),
            
            # Image handling - FIXED to handle the error
            'image_description': chunk.get('image_description', 'N/A Image Description'),
        }
        
        # Process image safely
        image_data = chunk.get('image')
        if image_data:
            # Check if image_data is a string (filename) or something else
            if isinstance(image_data, str):
                # Build Firebase Storage URL from filename
                firebase_url = build_firebase_image_url(image_data)
                enhanced_chunk['image'] = firebase_url
            else:
                # If it's not a string, just pass it through (might be already processed)
                enhanced_chunk['image'] = image_data
        else:
            enhanced_chunk['image'] = None
        
        # Ensure keywords is a list
        if isinstance(enhanced_chunk['keywords'], str):
            enhanced_chunk['keywords'] = [kw.strip() for kw in enhanced_chunk['keywords'].split(',') if kw.strip()]
        elif not isinstance(enhanced_chunk['keywords'], list):
            enhanced_chunk['keywords'] = []
        
        # Ensure related_sections is a list
        if isinstance(enhanced_chunk['related_sections'], str):
            enhanced_chunk['related_sections'] = [rs.strip() for rs in enhanced_chunk['related_sections'].split(',') if rs.strip()]
        elif not isinstance(enhanced_chunk['related_sections'], list):
            enhanced_chunk['related_sections'] = []
        
        return enhanced_chunk
        
    except Exception as e:
        logger.error(f"Error processing chunk: {e}")
        import traceback
        traceback.print_exc()
        # Return minimal chunk on error
        return {
            'id': chunk.get('id', 'error'),
            'content': 'Error processing chunk content',
            'original_text_chunk': 'Error processing chunk content',
            'title': 'Processing Error',
            'source_type': 'error',
            'language': DEFAULT_LANGUAGE,
            'similarity_score': 0.0,
            'image': None,
            'image_description': 'Error processing image',
            'keywords': [],
            'related_sections': []
        }

def get_section_chunks(faiss_service, section_id: str) -> List[Dict[str, Any]]:
    """Get all chunks for a specific section"""
    if not faiss_service or not hasattr(faiss_service, 'get_section_chunks'):
        logger.warning("FAISS service doesn't support section chunk retrieval")
        return []
    
    try:
        chunks = faiss_service.get_section_chunks(section_id)
        enhanced_chunks = [process_retrieved_chunk(chunk) for chunk in chunks]
        
        # Sort by chunk_order
        enhanced_chunks.sort(key=lambda x: x.get('chunk_order', 0))
        
        logger.info(f"Retrieved {len(enhanced_chunks)} chunks for section {section_id}")
        return enhanced_chunks
        
    except Exception as e:
        logger.error(f"Failed to get section chunks for {section_id}: {e}")
        return []

# Legacy function for backward compatibility
def retrieve_relevant_chunks_legacy(query_embedding: List[float], faiss_service, num_neighbors: int = None) -> List[Dict[str, Any]]:
    """Legacy retrieval function for backward compatibility"""
    return retrieve_relevant_chunks(
        query_embedding=query_embedding,
        faiss_service=faiss_service,
        num_neighbors=num_neighbors
    )