# app/faiss_vector_service.py - Enhanced with new metadata handling
import os
import pickle
import numpy as np
import faiss
from typing import List, Dict, Any, Optional
import logging
from collections import defaultdict
from app.config import (
    LOCAL_VECTOR_FILES_PATH, EMBEDDING_QUANT, SECTION_EXPANSION_ENABLED,
    MIN_CHUNKS_SIMPLE, MAX_CHUNKS_SIMPLE, MIN_CHUNKS_DETAILED, MAX_CHUNKS_DETAILED
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedFAISSVectorService:
    """Enhanced FAISS-based vector search service with dynamic retrieval and metadata handling"""
    
    def __init__(self, 
                 vector_files_path: str = LOCAL_VECTOR_FILES_PATH,
                 embeddings_file: str = "embeddings_enhanced.npy",
                 metadata_file: str = "metadata_enhanced.pkl", 
                 id_map_file: str = "index_to_id_enhanced.pkl",
                 index_type: str = "IVF"):
        
        self.vector_files_path = vector_files_path
        self.embeddings_file = embeddings_file
        self.metadata_file = metadata_file
        self.id_map_file = id_map_file
        self.index_type = index_type
        
        # In-memory storage
        self.faiss_index = None
        self.metadata = None
        self.id_map = None
        self.embeddings = None
        
        # Section mapping for quick lookups
        self.section_to_chunks = defaultdict(list)  # section_id -> [chunk_indices]
        self.chunk_to_section = {}  # chunk_index -> section_id
        
        logger.info(f"Enhanced FAISS Vector Service initialized with path: {vector_files_path}")
    
    def load_index(self) -> bool:
        """Load FAISS index and metadata from local files with enhanced structure"""
        try:
            # Load embeddings
            embeddings_path = os.path.join(self.vector_files_path, self.embeddings_file)
            if not os.path.exists(embeddings_path):
                logger.error(f"Embeddings file not found: {embeddings_path}")
                return False
            
            self.embeddings = np.load(embeddings_path).astype('float32')
            logger.info(f"Loaded embeddings: {self.embeddings.shape}")
            
            # Load metadata
            metadata_path = os.path.join(self.vector_files_path, self.metadata_file)
            if not os.path.exists(metadata_path):
                logger.error(f"Metadata file not found: {metadata_path}")
                return False
            
            with open(metadata_path, "rb") as f:
                self.metadata = pickle.load(f)
            logger.info(f"Loaded metadata: {type(self.metadata)} with {len(self.metadata)} entries")
            
            # Load ID map
            id_map_path = os.path.join(self.vector_files_path, self.id_map_file)
            if not os.path.exists(id_map_path):
                logger.error(f"ID map file not found: {id_map_path}")
                return False
            
            with open(id_map_path, "rb") as f:
                self.id_map = pickle.load(f)
            logger.info(f"Loaded ID map: {type(self.id_map)} with {len(self.id_map)} entries")
            
            # Validate and build section mappings
            if not self._validate_and_build_mappings():
                return False
            
            # Build FAISS index
            self._build_faiss_index()
            
            logger.info(f"Successfully loaded {len(self.embeddings)} vectors with enhanced metadata")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False
    
    def _validate_and_build_mappings(self) -> bool:
        """Validate data and build section mappings for quick retrieval"""
        try:
            if not (len(self.embeddings) == len(self.metadata) == len(self.id_map)):
                logger.error("Dimension mismatch between embeddings, metadata, and ID map")
                return False
            
            # Build section mappings
            for idx, metadata_item in enumerate(self.metadata):
                if isinstance(metadata_item, dict):
                    section_id = metadata_item.get('section_id', f'unknown_section_{idx}')
                    self.section_to_chunks[section_id].append(idx)
                    self.chunk_to_section[idx] = section_id
                else:
                    # Handle legacy format
                    section_id = f'legacy_section_{idx}'
                    self.section_to_chunks[section_id].append(idx)
                    self.chunk_to_section[idx] = section_id
            
            # Sort chunks within sections by chunk_order if available
            for section_id, chunk_indices in self.section_to_chunks.items():
                chunk_indices.sort(key=lambda idx: self._get_chunk_order(idx))
            
            logger.info(f"Built section mappings: {len(self.section_to_chunks)} sections")
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate and build mappings: {e}")
            return False
    
    def _get_chunk_order(self, chunk_idx: int) -> int:
        """Get chunk order for sorting, default to index if not available"""
        try:
            if isinstance(self.metadata[chunk_idx], dict):
                return self.metadata[chunk_idx].get('chunk_order', chunk_idx)
            return chunk_idx
        except:
            return chunk_idx
    
    def _build_faiss_index(self):
        """Build FAISS index from embeddings"""
        try:
            dimension = self.embeddings.shape[1]
            num_vectors = len(self.embeddings)
            
            if self.index_type == "Flat" or num_vectors < 100:
                self.faiss_index = faiss.IndexFlatIP(dimension)
            else:
                nlist = min(100, max(1, num_vectors // 10))
                quantizer = faiss.IndexFlatIP(dimension)
                self.faiss_index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
                
                if num_vectors >= nlist:
                    self.faiss_index.train(self.embeddings)
                else:
                    logger.warning("Not enough vectors for IVF training, using Flat index")
                    self.faiss_index = faiss.IndexFlatIP(dimension)
            
            self.faiss_index.add(self.embeddings)
            logger.info(f"FAISS index built: {type(self.faiss_index).__name__} with {self.faiss_index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Failed to build FAISS index: {e}")
            raise
    
    def search_dynamic(self, 
                      query_embedding: List[float], 
                      query_type: str = "simple",
                      estimated_chunks: int = None,
                      source_type_filter: Optional[str] = None,
                      language_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Enhanced search with dynamic retrieval and filtering"""
        
        if self.faiss_index is None:
            logger.error("FAISS index not loaded")
            return []
        
        try:
            # Determine initial k based on query type
            if query_type == "detailed":
                initial_k = min(estimated_chunks or MIN_CHUNKS_DETAILED, MAX_CHUNKS_DETAILED)
            else:
                initial_k = min(estimated_chunks or MIN_CHUNKS_SIMPLE, MAX_CHUNKS_SIMPLE)
            
            initial_k = min(initial_k, self.faiss_index.ntotal)
            
            logger.info(f"Dynamic search: type={query_type}, initial_k={initial_k}")
            
            # Initial FAISS search
            query_vec = np.array([query_embedding], dtype='float32')
            distances, indices = self.faiss_index.search(query_vec, initial_k * 2)  # Get extra for filtering
            
            # Filter results
            filtered_results = []
            for distance, idx in zip(distances[0], indices[0]):
                if idx == -1 or idx >= len(self.metadata):
                    continue
                
                metadata_item = self._get_metadata_item(idx)
                
                # Apply filters
                if source_type_filter and metadata_item.get('source_type') != source_type_filter:
                    continue
                
                if language_filter and metadata_item.get('language') != language_filter:
                    continue
                
                filtered_results.append((distance, idx, metadata_item))
                
                if len(filtered_results) >= initial_k:
                    break
            
            # Group by section and apply expansion logic
            if SECTION_EXPANSION_ENABLED and query_type == "detailed":
                expanded_results = self._expand_by_sections(filtered_results)
            else:
                expanded_results = filtered_results
            
            # Build final results
            final_results = []
            for distance, idx, metadata_item in expanded_results:
                section_id = self._get_section_id(idx)
                result = self._build_enhanced_result_dict(metadata_item, section_id, float(distance), idx)
                final_results.append(result)
            
            logger.info(f"Search completed: {len(final_results)} results returned")
            return final_results
            
        except Exception as e:
            logger.error(f"Dynamic search failed: {e}")
            return []
    
    def _expand_by_sections(self, initial_results: List[tuple]) -> List[tuple]:
        """Expand results by including all chunks from sections with multiple hits"""
        section_hits = defaultdict(list)
        
        # Group initial results by section
        for distance, idx, metadata_item in initial_results:
            section_id = metadata_item.get('section_id', f'unknown_{idx}')
            section_hits[section_id].append((distance, idx, metadata_item))
        
        expanded_results = []
        
        for section_id, hits in section_hits.items():
            if len(hits) > 1:  # Multiple hits in this section - expand
                logger.info(f"Expanding section {section_id} with {len(hits)} hits")
                
                # Get all chunks in this section
                all_section_chunks = self.section_to_chunks.get(section_id, [])
                for chunk_idx in all_section_chunks:
                    if chunk_idx < len(self.metadata):
                        metadata_item = self._get_metadata_item(chunk_idx)
                        # Use best distance from this section
                        best_distance = min(h[0] for h in hits)
                        expanded_results.append((best_distance, chunk_idx, metadata_item))
            else:
                # Single hit - keep as is
                expanded_results.extend(hits)
        
        # Sort by distance and remove duplicates
        seen_indices = set()
        unique_results = []
        for distance, idx, metadata_item in sorted(expanded_results, key=lambda x: x[0]):
            if idx not in seen_indices:
                unique_results.append((distance, idx, metadata_item))
                seen_indices.add(idx)
        
        return unique_results
    
    def search(self, query_embedding: List[float], k: int = None) -> List[Dict[str, Any]]:
        """Legacy search method for backward compatibility"""
        if k is None:
            k = EMBEDDING_QUANT
        
        # Use simple search for legacy compatibility
        return self.search_dynamic(query_embedding, "simple", k)
    
    def _get_metadata_item(self, idx: int) -> Dict[str, Any]:
        """Get metadata item by index with enhanced structure support"""
        try:
            if isinstance(self.metadata, list):
                if 0 <= idx < len(self.metadata):
                    item = self.metadata[idx]
                    if isinstance(item, dict):
                        return item
                    else:
                        # Legacy format conversion
                        return {
                            "original_text_chunk": str(item),
                            "content": str(item),
                            "section_id": f"legacy_section_{idx}",
                            "chunk_order": 0,
                            "source_type": "unknown",
                            "language": "en-US"
                        }
                else:
                    logger.warning(f"Index {idx} out of range for metadata list")
                    return {}
            else:
                logger.error(f"Unexpected metadata type: {type(self.metadata)}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting metadata item {idx}: {e}")
            return {}
    
    def _get_section_id(self, idx: int) -> str:
        """Get section ID by index"""
        return self.chunk_to_section.get(idx, f"unknown_section_{idx}")
    
    def _build_enhanced_result_dict(self, metadata_item: Dict[str, Any], section_id: str, distance: float, idx: int) -> Dict[str, Any]:
        """Build enhanced result dictionary with new metadata fields"""
        try:
            # Handle nested metadata structure from new JSONL format
            nested_metadata = metadata_item.get('metadata', {})

            # Extract content - prefer original_text_chunk for full content
            content = (nested_metadata.get('original_text_chunk') or
                      metadata_item.get('content') or
                      nested_metadata.get('content', ''))

            result = {
                # Core fields
                'id': metadata_item.get('id', section_id),
                'distance': distance,
                'similarity_score': distance,
                'chunk_index': idx,

                # Content fields - use full original text when available
                'content': content,
                'original_text_chunk': nested_metadata.get('original_text_chunk', content),
                'summary': nested_metadata.get('summary', ''),

                # Document structure - prefer nested metadata
                'title': nested_metadata.get('title', metadata_item.get('title', 'Unknown Document')),
                'subtitle': nested_metadata.get('subtitle', metadata_item.get('subtitle', 'N/A Subtitle')),
                'section_id': nested_metadata.get('section_id', metadata_item.get('section_id', section_id)),
                'chunk_order': nested_metadata.get('chunk_order', metadata_item.get('chunk_order', 0)),
                'page_number': str(nested_metadata.get('page_number', metadata_item.get('page_number', 'N/A'))),
                'version': nested_metadata.get('version', metadata_item.get('version', 'N/A Version')),

                # Classification
                'source_type': nested_metadata.get('source_type', metadata_item.get('source_type', 'unknown')),
                'language': nested_metadata.get('language', metadata_item.get('language', 'en-US')),
                'is_complete_section': nested_metadata.get('is_complete_section', metadata_item.get('is_complete_section', False)),
                
                # Search metadata
                'keywords': metadata_item.get('keywords', []),
                'related_sections': metadata_item.get('related_sections', []),
                
                # Image handling (Firebase URLs)
                'image': None
            }
            
            # Handle image metadata for Firebase Storage
            image_uri = metadata_item.get('image_gcs_uri') or metadata_item.get('image_firebase_url')
            if image_uri:
                result['image'] = {
                    'firebase_url': image_uri if 'firebase' in image_uri else None,
                    'gcs_uri': image_uri if 'gs://' in image_uri else None,
                    'filename': image_uri.split('/')[-1] if '/' in image_uri else image_uri,
                    'description': metadata_item.get('image_description', metadata_item.get('image_text_description', 'Equipment diagram'))
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error building enhanced result dict: {e}")
            # Return minimal result on error
            return {
                'id': section_id,
                'distance': distance,
                'similarity_score': distance,
                'content': 'Error retrieving content',
                'original_text_chunk': 'Error retrieving content',
                'title': 'Unknown Section',
                'source_type': 'error',
                'language': 'en-US'
            }
    
    def get_section_chunks(self, section_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific section"""
        chunk_indices = self.section_to_chunks.get(section_id, [])
        results = []
        
        for idx in chunk_indices:
            metadata_item = self._get_metadata_item(idx)
            result = self._build_enhanced_result_dict(metadata_item, section_id, 0.0, idx)
            results.append(result)
        
        # Sort by chunk_order
        results.sort(key=lambda x: x.get('chunk_order', 0))
        return results

    def search_level_aware(self,
                          query_embedding: List[float],
                          query_type: str = "auto",
                          max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Level-aware search strategy optimized for customer support

        Args:
            query_embedding: Query vector
            query_type: "quick_facts", "troubleshooting", "setup", "auto"
            max_results: Maximum number of results to return
        """
        if self.faiss_index is None:
            logger.error("FAISS index not loaded")
            return []

        try:
            # Classify query type if auto
            if query_type == "auto":
                query_type = self._classify_query_type(query_embedding)

            # Execute search strategy based on query type
            if query_type == "quick_facts":
                return self._search_quick_facts(query_embedding, max_results)
            elif query_type == "troubleshooting":
                return self._search_troubleshooting(query_embedding, max_results)
            elif query_type == "setup":
                return self._search_setup(query_embedding, max_results)
            else:
                # Default: progressive complexity search
                return self._search_progressive(query_embedding, max_results)

        except Exception as e:
            logger.error(f"Level-aware search failed: {e}")
            return []

    def _classify_query_type(self, query_embedding: List[float]) -> str:
        """Intelligent query classification for customer support"""
        # This is a placeholder - in production, this could use the query text
        # For now, we'll implement a simple pattern-based approach
        return "progressive"

    def classify_query_from_text(self, query_text: str) -> str:
        """
        Classify query type based on text patterns

        Args:
            query_text: The user's query text

        Returns:
            Query type: "quick_facts", "troubleshooting", "setup", or "progressive"
        """
        query_lower = query_text.lower()

        # Quick facts patterns
        quick_patterns = [
            "what does", "what is", "meaning of", "define", "explain",
            "led", "light", "indicator", "status", "color"
        ]

        # Troubleshooting patterns
        trouble_patterns = [
            "not working", "broken", "error", "problem", "issue", "fix",
            "won't", "can't", "doesn't", "failed", "trouble", "disconnect",
            "slow", "intermittent", "red light", "blinking"
        ]

        # Setup patterns
        setup_patterns = [
            "how to", "setup", "install", "configure", "connect", "pair",
            "sync", "first time", "initial", "getting started", "begin"
        ]

        # Count pattern matches
        quick_score = sum(1 for pattern in quick_patterns if pattern in query_lower)
        trouble_score = sum(1 for pattern in trouble_patterns if pattern in query_lower)
        setup_score = sum(1 for pattern in setup_patterns if pattern in query_lower)

        # Determine query type based on highest score
        if trouble_score > max(quick_score, setup_score):
            return "troubleshooting"
        elif setup_score > max(quick_score, trouble_score):
            return "setup"
        elif quick_score > max(trouble_score, setup_score):
            return "quick_facts"
        else:
            return "progressive"

    def _search_quick_facts(self, query_embedding: List[float], max_results: int) -> List[Dict[str, Any]]:
        """Search optimized for quick facts (L0 chunks)"""
        logger.info("Executing quick facts search strategy")

        # Step 1: Search L0 chunks (quick facts) with high priority
        l0_results = self._search_by_level(query_embedding, "L0", max_results=max_results//2 + 1)

        # Step 2: If not enough results, add Q&A pairs
        if len(l0_results) < max_results:
            qa_results = self._search_by_level(query_embedding, "QA", max_results=max_results - len(l0_results))
            l0_results.extend(qa_results)

        # Apply search weight boosts
        boosted_results = self._apply_search_weights(l0_results)

        return boosted_results[:max_results]

    def _search_troubleshooting(self, query_embedding: List[float], max_results: int) -> List[Dict[str, Any]]:
        """Search optimized for troubleshooting workflows"""
        logger.info("Executing troubleshooting search strategy")

        # Progressive search: L0 → L2 → L1 → L4
        results = []

        # Quick indicators first (L0)
        l0_results = self._search_by_level(query_embedding, "L0", max_results=2)
        results.extend(l0_results)

        # Troubleshooting summaries (L2)
        if len(results) < max_results:
            l2_results = self._search_by_level(query_embedding, "L2", max_results=max_results - len(results))
            results.extend(l2_results)

        # Detailed procedures (L1) if needed
        if len(results) < max_results:
            l1_results = self._search_by_level(query_embedding, "L1", max_results=max_results - len(results))
            results.extend(l1_results)

        return self._apply_search_weights(results)[:max_results]

    def _search_setup(self, query_embedding: List[float], max_results: int) -> List[Dict[str, Any]]:
        """Search optimized for setup procedures"""
        logger.info("Executing setup search strategy")

        # Focus on procedural content: L1 → L2 → L4
        results = []

        # Main setup procedures (L1)
        l1_results = self._search_by_level(query_embedding, "L1", max_results=max_results//2 + 1)
        results.extend(l1_results)

        # Setup summaries (L2)
        if len(results) < max_results:
            l2_results = self._search_by_level(query_embedding, "L2", max_results=max_results - len(results))
            results.extend(l2_results)

        return self._apply_search_weights(results)[:max_results]

    def _search_progressive(self, query_embedding: List[float], max_results: int) -> List[Dict[str, Any]]:
        """Progressive complexity search for general queries"""
        logger.info("Executing progressive complexity search strategy")

        # Balanced approach across all levels
        results = []

        # Quick answers first (L0, QA)
        quick_results = self._search_by_level(query_embedding, ["L0", "QA"], max_results=2)
        results.extend(quick_results)

        # Main content (L1, L2)
        if len(results) < max_results:
            main_results = self._search_by_level(query_embedding, ["L1", "L2"], max_results=max_results - len(results))
            results.extend(main_results)

        return self._apply_search_weights(results)[:max_results]

    def _search_by_level(self, query_embedding: List[float], levels, max_results: int) -> List[Dict[str, Any]]:
        """Search within specific levels"""
        if isinstance(levels, str):
            levels = [levels]

        # Search with higher k to allow level filtering
        query_vec = np.array([query_embedding], dtype='float32')
        search_k = min(max_results * 10, self.faiss_index.ntotal)  # Search more to filter by level
        distances, indices = self.faiss_index.search(query_vec, search_k)

        # Filter by level and collect results
        level_results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1 or idx >= len(self.metadata):
                continue

            metadata_item = self._get_metadata_item(idx)
            chunk_level = metadata_item.get('level', 'L1')

            if chunk_level in levels:
                section_id = self._get_section_id(idx)
                result = self._build_enhanced_result_dict(metadata_item, section_id, float(distance), idx)
                level_results.append(result)

                if len(level_results) >= max_results:
                    break

        return level_results

    def _apply_search_weights(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply level-based search weights to boost relevance"""
        for result in results:
            search_weight = result.get('search_weight', 1.0)
            original_distance = result.get('distance', 1.0)

            # Apply weight boost (lower distance = higher relevance)
            boosted_distance = original_distance / search_weight
            result['distance'] = boosted_distance
            result['similarity_score'] = boosted_distance
            result['search_boost_applied'] = True

        # Re-sort by boosted distance
        results.sort(key=lambda x: x.get('distance', 1.0))
        return results

    # app/faiss_vector_service.py - Update health check
    def health_check(self) -> Dict[str, Any]:
        """Enhanced health check with section information"""
        try:
            return {
                "status": "healthy" if self.faiss_index is not None else "unhealthy",
                "index_loaded": self.faiss_index is not None,
                "total_vectors": self.faiss_index.ntotal if self.faiss_index else 0,
                "total_sections": len(self.section_to_chunks),
                "metadata_type": type(self.metadata).__name__ if self.metadata else "None",
                "id_map_type": type(self.id_map).__name__ if self.id_map else "None",
                "service": "enhanced-faiss-vector-search",
                "vector_files_path": self.vector_files_path,
                "expected_files": [
                    self.embeddings_file,
                    self.metadata_file,
                    self.id_map_file
                ],
                "features": {
                    "dynamic_retrieval": True,
                    "section_expansion": SECTION_EXPANSION_ENABLED,
                    "multi_language": True,
                    "source_filtering": True
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "enhanced-faiss-vector-search",
                "vector_files_path": self.vector_files_path,
                "expected_files": [
                    self.embeddings_file,
                    self.metadata_file,
                    self.id_map_file
                ]
            }