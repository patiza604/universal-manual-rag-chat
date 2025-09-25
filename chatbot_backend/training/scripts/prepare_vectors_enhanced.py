# training/scripts/prepare_vectors_enhanced.py
import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from tqdm import tqdm
import faiss
from collections import defaultdict, Counter
import google.generativeai as genai
from google.cloud import aiplatform

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.config import *

class EnhancedVectorProcessor:
    """Enhanced vector processor with multi-embedding strategy and customer support optimization"""

    def __init__(self,
                 input_jsonl_file: str,
                 output_dir: str = "training/output/vectors",
                 enable_quality_filtering: bool = True,
                 min_quality_score: float = 0.2,
                 enable_multi_embeddings: bool = True):

        self.input_jsonl_file = Path(input_jsonl_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Quality filtering
        self.enable_quality_filtering = enable_quality_filtering
        self.min_quality_score = min_quality_score

        # Multi-embedding strategy
        self.enable_multi_embeddings = enable_multi_embeddings

        # Initialize embedding client
        self._init_embedding_client()
        
        # Output files
        self.embeddings_file = self.output_dir / "embeddings_enhanced.npy"
        self.metadata_file = self.output_dir / "metadata_enhanced.pkl"
        self.index_map_file = self.output_dir / "index_to_id_enhanced.pkl"
        self.faiss_index_file = self.output_dir / "faiss_index_enhanced.index"
        self.stats_file = self.output_dir / "vector_stats_enhanced.json"

        # Multi-embedding output files
        self.question_embeddings_file = self.output_dir / "question_embeddings_enhanced.npy"
        self.combined_embeddings_file = self.output_dir / "combined_embeddings_enhanced.npy"
        self.embedding_types_file = self.output_dir / "embedding_types_enhanced.pkl"
        
        # Processing statistics
        self.stats = {
            'total_chunks_processed': 0,
            'chunks_included': 0,
            'chunks_filtered_out': 0,
            'embedding_dimension': 0,
            'content_type_distribution': defaultdict(int),
            'semantic_role_distribution': defaultdict(int),
            'level_distribution': defaultdict(int),
            'quality_flag_distribution': defaultdict(int),
            'classification_method_distribution': defaultdict(int),
            'chunks_needing_review': 0,
            'average_completeness_score': 0.0,
            'average_token_efficiency': 0.0,
            'group_id_count': 0,
            'unique_sections': 0,
            'processing_errors': [],
            # Multi-embedding statistics
            'total_user_questions': 0,
            'question_embeddings_generated': 0,
            'combined_embeddings_generated': 0,
            'support_category_distribution': defaultdict(int),
            'difficulty_level_distribution': defaultdict(int),
            'domain_category_distribution': defaultdict(int)
        }

    def _init_embedding_client(self):
        """Initialize embedding client using secured credential authentication"""
        try:
            # Use environment-based credentials (recommended)
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            credentials = None

            if credentials_path and os.path.exists(credentials_path):
                print(f"SUCCESS: Using service account key from GOOGLE_APPLICATION_CREDENTIALS")
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                key_used = credentials_path

            # Initialize Vertex AI with service account credentials
            if credentials:
                # Set environment variable for vertexai
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_used
                import vertexai
                vertexai.init(
                    project=PROJECT_ID,
                    location=LOCATION,
                    credentials=credentials
                )
                print(f"SUCCESS: Vertex AI initialized with service account")
            else:
                # Fallback to Application Default Credentials
                print("INFO: No service account key found, using Application Default Credentials")
                import vertexai
                vertexai.init(
                    project=PROJECT_ID,
                    location=LOCATION
                )

            # Import and initialize embedding model
            from vertexai.language_models import TextEmbeddingModel
            self.embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_NAME)

            print(f"SUCCESS: Initialized embedding client with model {EMBEDDING_MODEL_NAME}")

        except Exception as e:
            print(f"WARNING: Failed to initialize embedding client: {e}")
            print("INFO: Multi-embedding features will be disabled")
            self.enable_multi_embeddings = False
            self.embedding_model = None
    
    def process_jsonl(self) -> Dict[str, Any]:
        """Process enhanced JSONL file into FAISS-ready vectors"""
        
        print(f"Loading enhanced chunks from {self.input_jsonl_file}")
        
        if not self.input_jsonl_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_jsonl_file}")
        
        # Load and validate chunks
        chunks = self._load_and_validate_chunks()
        
        if not chunks:
            raise ValueError("No valid chunks found in input file")
        
        print(f"SUCCESS: Loaded {len(chunks)} valid chunks")
        
        # Filter chunks by quality if enabled
        if self.enable_quality_filtering:
            chunks = self._filter_chunks_by_quality(chunks)
            print(f"INFO: After quality filtering: {len(chunks)} chunks")
        
        # Extract embeddings and metadata
        embeddings, metadata_list, id_map = self._extract_embeddings_and_metadata(chunks)
        
        # Create FAISS index
        faiss_index = self._create_faiss_index(embeddings)
        
        # Save all outputs
        self._save_outputs(embeddings, metadata_list, id_map, faiss_index)
        
        # Generate comprehensive statistics
        self._generate_statistics(chunks, metadata_list)
        
        # Save statistics
        self._save_statistics()
        
        print(f"\nSUCCESS: Enhanced vector processing complete!")
        print(f"INFO: Processed {self.stats['total_chunks_processed']} chunks")
        print(f"TOTAL: Included {self.stats['chunks_included']} in final index")
        print(f"FILTERED: Filtered out {self.stats['chunks_filtered_out']} low-quality chunks")
        
        return self.stats
    
    def _load_and_validate_chunks(self) -> List[Dict[str, Any]]:
        """Load and validate chunks from JSONL file"""
        
        chunks = []
        line_number = 0
        
        with open(self.input_jsonl_file, 'r', encoding='utf-8') as file:
            for line in file:
                line_number += 1
                line = line.strip()
                
                if not line:
                    continue
                
                try:
                    chunk = json.loads(line)
                    
                    # Validate required fields
                    if not self._validate_chunk_structure(chunk, line_number):
                        continue
                    
                    chunks.append(chunk)
                    self.stats['total_chunks_processed'] += 1
                    
                except json.JSONDecodeError as e:
                    error_msg = f"JSON decode error at line {line_number}: {e}"
                    print(f"WARNING: {error_msg}")
                    self.stats['processing_errors'].append(error_msg)
                    continue
                except Exception as e:
                    error_msg = f"Unexpected error at line {line_number}: {e}"
                    print(f"WARNING: {error_msg}")
                    self.stats['processing_errors'].append(error_msg)
                    continue
        
        return chunks
    
    def _validate_chunk_structure(self, chunk: Dict[str, Any], line_number: int) -> bool:
        """Validate chunk has required structure"""
        
        required_fields = ['id', 'content', 'embedding', 'metadata']
        
        for field in required_fields:
            if field not in chunk:
                error_msg = f"Missing required field '{field}' at line {line_number}"
                print(f"WARNING: {error_msg}")
                self.stats['processing_errors'].append(error_msg)
                return False
        
        # Validate embedding
        embedding = chunk['embedding']
        if not isinstance(embedding, list) or len(embedding) == 0:
            error_msg = f"Invalid embedding format at line {line_number}"
            print(f"WARNING: {error_msg}")
            self.stats['processing_errors'].append(error_msg)
            return False
        
        # Validate metadata
        metadata = chunk['metadata']
        if not isinstance(metadata, dict):
            error_msg = f"Invalid metadata format at line {line_number}"
            print(f"WARNING: {error_msg}")
            self.stats['processing_errors'].append(error_msg)
            return False
        
        # Check content
        content = chunk.get('content', '').strip()
        if not content:
            error_msg = f"Empty content at line {line_number}"
            print(f"WARNING: {error_msg}")
            self.stats['processing_errors'].append(error_msg)
            return False
        
        return True
    
    def _filter_chunks_by_quality(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter chunks based on quality metrics"""
        
        filtered_chunks = []
        
        for chunk in chunks:
            metadata = chunk.get('metadata', {})
            
            # Get quality metrics
            completeness_score = metadata.get('completeness_score', 0.5)
            quality_flag = metadata.get('quality_flag', 'medium')
            needs_review = metadata.get('needs_review', False)
            
            # Quality filtering logic
            include_chunk = True
            
            # Filter by completeness score
            if completeness_score < self.min_quality_score:
                include_chunk = False
            
            # Always include safety-critical content regardless of quality
            semantic_role = metadata.get('semantic_role', '')
            content_type = metadata.get('content_type', '')
            
            if semantic_role == 'safety_critical' or content_type == 'safety_alert':
                include_chunk = True
            
            # Always include L2 and L3 chunks (section and document level)
            level = metadata.get('level', 'L1')
            if level in ['L2', 'L3']:
                include_chunk = True
            
            if include_chunk:
                filtered_chunks.append(chunk)
                self.stats['chunks_included'] += 1
            else:
                self.stats['chunks_filtered_out'] += 1
        
        return filtered_chunks
    
    def _extract_embeddings_and_metadata(self, chunks: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[Dict], List[str]]:
        """Extract embeddings and clean metadata with multi-embedding strategy"""

        content_embeddings = []
        question_embeddings = []
        combined_embeddings = []
        metadata_list = []
        id_map = []
        embedding_types = []

        print("Processing: Extracting embeddings and metadata with multi-embedding strategy...")

        for chunk in tqdm(chunks, desc="Processing chunks"):
            try:
                # Extract main content embedding (existing)
                content_embedding = np.array(chunk['embedding'], dtype='float32')
                content_embeddings.append(content_embedding)

                # Set embedding dimension if not set
                if self.stats['embedding_dimension'] == 0:
                    self.stats['embedding_dimension'] = len(content_embedding)

                # Extract and clean metadata
                original_metadata = chunk['metadata']
                clean_metadata = self._clean_metadata_for_storage(original_metadata, chunk)

                # Multi-embedding strategy for enhanced search
                if self.enable_multi_embeddings and self.embedding_model:
                    question_emb, combined_emb = self._generate_additional_embeddings(chunk, original_metadata)
                    question_embeddings.append(question_emb)
                    combined_embeddings.append(combined_emb)

                    # Update metadata with multi-embedding info
                    clean_metadata['has_question_embeddings'] = True
                    clean_metadata['has_combined_embeddings'] = True
                else:
                    # Use content embedding as fallback
                    question_embeddings.append(content_embedding)
                    combined_embeddings.append(content_embedding)
                    clean_metadata['has_question_embeddings'] = False
                    clean_metadata['has_combined_embeddings'] = False

                # Apply level-aware processing weights
                clean_metadata = self._apply_level_weights(clean_metadata, original_metadata)

                metadata_list.append(clean_metadata)

                # Store ID mapping and embedding type info
                id_map.append(chunk['id'])
                embedding_types.append({
                    'id': chunk['id'],
                    'level': original_metadata.get('level', 'L1'),
                    'support_category': original_metadata.get('support_category', 'information'),
                    'has_questions': bool(original_metadata.get('user_questions', []))
                })

                # Update statistics
                self._update_statistics_from_chunk(original_metadata)

            except Exception as e:
                error_msg = f"Error processing chunk {chunk.get('id', 'unknown')}: {e}"
                print(f"WARNING: {error_msg}")
                self.stats['processing_errors'].append(error_msg)
                continue

        # Convert embeddings to numpy arrays
        content_embeddings_array = np.array(content_embeddings, dtype='float32')
        question_embeddings_array = np.array(question_embeddings, dtype='float32')
        combined_embeddings_array = np.array(combined_embeddings, dtype='float32')

        # Save additional embedding arrays
        if self.enable_multi_embeddings:
            self._save_additional_embeddings(question_embeddings_array, combined_embeddings_array, embedding_types)

        print(f"SUCCESS: Extracted {len(content_embeddings_array)} content embeddings of dimension {self.stats['embedding_dimension']}")
        if self.enable_multi_embeddings:
            print(f"SUCCESS: Generated {len(question_embeddings_array)} question embeddings")
            print(f"SUCCESS: Generated {len(combined_embeddings_array)} combined embeddings")

        # Return content embeddings as primary (for backward compatibility)
        return content_embeddings_array, metadata_list, id_map
    
    def _clean_metadata_for_storage(self, metadata: Dict[str, Any], chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and standardize metadata for efficient storage"""
        
        clean_metadata = {
            # Core identification
            'id': chunk['id'],
            'section_id': metadata.get('section_id', ''),
            'title': metadata.get('title', ''),
            'subtitle': metadata.get('subtitle', ''),
            
            # Content classification
            'content_type': metadata.get('content_type', 'manual_section'),
            'semantic_role': metadata.get('semantic_role', 'general'),
            'level': metadata.get('level', 'L1'),
            'group_id': metadata.get('group_id'),
            
            # Quality metrics
            'completeness_score': float(metadata.get('completeness_score', 0.5)),
            'token_efficiency': float(metadata.get('token_efficiency', 1.0)),
            'quality_flag': metadata.get('quality_flag', 'medium'),
            'needs_review': bool(metadata.get('needs_review', False)),
            
            # Chunk metadata
            'chunk_order': int(metadata.get('chunk_order', 0)),
            'token_count': int(metadata.get('token_count', 0)),
            'page_number': str(metadata.get('page_number', 'N/A')),
            
            # Navigation
            'previous_chunk': metadata.get('previous_chunk'),
            'next_chunk': metadata.get('next_chunk'),
            'group_position': metadata.get('group_position'),
            'group_total': metadata.get('group_total'),
            
            # Retrieval hints
            'retrieval_priority': metadata.get('retrieval_priority', 'normal'),
            'standalone_readable': bool(metadata.get('standalone_readable', True)),
            'requires_context': bool(metadata.get('requires_context', False)),
            
            # Content metadata
            'summary': metadata.get('summary', ''),
            'keywords': metadata.get('keywords', []),
            'related_sections': metadata.get('related_sections', []),
            'complexity_level': metadata.get('complexity_level', 'basic'),
            
            # Technical metadata
            'version': metadata.get('version', ''),
            'language': metadata.get('language', DEFAULT_LANGUAGE),
            'source_type': metadata.get('source_type', 'manual'),
            
            # Classification metadata
            'classification_method': metadata.get('classification_method', 'unknown'),
            'classification_confidence': float(metadata.get('classification_confidence', 0.0)),
            'semantic_boundary_type': metadata.get('semantic_boundary_type', ''),
            
            # Media
            'image_gcs_uri': metadata.get('image_gcs_uri', ''),
            'image_description': metadata.get('image_description', ''),
            
            # Processing metadata
            'processed_at': metadata.get('processed_at', ''),
            'is_complete_section': bool(metadata.get('is_complete_section', False))
        }
        
        # Store original content for reference (truncated)
        content = chunk.get('content', '')
        clean_metadata['content'] = content  # Store full content for RAG retrieval
        clean_metadata['content_preview'] = content[:200] + "..." if len(content) > 200 else content
        clean_metadata['content_length'] = len(content)
        
        return clean_metadata
    
    def _update_statistics_from_chunk(self, metadata: Dict[str, Any]):
        """Update processing statistics from chunk metadata"""
        
        # Content type distribution
        content_type = metadata.get('content_type', 'unknown')
        self.stats['content_type_distribution'][content_type] += 1
        
        # Semantic role distribution
        semantic_role = metadata.get('semantic_role', 'unknown')
        self.stats['semantic_role_distribution'][semantic_role] += 1
        
        # Level distribution
        level = metadata.get('level', 'L1')
        self.stats['level_distribution'][level] += 1
        
        # Quality flag distribution
        quality_flag = metadata.get('quality_flag', 'medium')
        self.stats['quality_flag_distribution'][quality_flag] += 1
        
        # Classification method distribution
        classification_method = metadata.get('classification_method', 'unknown')
        self.stats['classification_method_distribution'][classification_method] += 1
        
        # Review flags
        if metadata.get('needs_review', False):
            self.stats['chunks_needing_review'] += 1
        
        # Group IDs
        if metadata.get('group_id'):
            self.stats['group_id_count'] += 1

        # Customer support metadata
        support_category = metadata.get('support_category', 'information')
        self.stats['support_category_distribution'][support_category] += 1

        difficulty_level = metadata.get('difficulty_level', 'beginner')
        self.stats['difficulty_level_distribution'][difficulty_level] += 1

        domain_category = metadata.get('domain_category', 'electronics')
        self.stats['domain_category_distribution'][domain_category] += 1
    
    def _create_faiss_index(self, embeddings: np.ndarray) -> faiss.Index:
        """Create optimized FAISS index"""
        
        print("Processing: Creating FAISS index...")
        
        dimension = embeddings.shape[1]
        n_vectors = embeddings.shape[0]
        
        # Choose index type based on data size
        if n_vectors < 1000:
            # Use flat index for small datasets
            index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            print(f"STATS: Created Flat index for {n_vectors} vectors")
        
        elif n_vectors < 10000:
            # Use IVF with reasonable number of centroids
            nlist = min(int(np.sqrt(n_vectors)), 100)  # Number of clusters
            quantizer = faiss.IndexFlatIP(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
            
            # Train the index
            print(f"Training IVF index with {nlist} centroids...")
            index.train(embeddings)
            print(f"STATS: Created IVF index for {n_vectors} vectors")
        
        else:
            # Use IVF with PQ for large datasets
            nlist = int(np.sqrt(n_vectors))
            m = 8  # Number of subquantizers
            quantizer = faiss.IndexFlatIP(dimension)
            index = faiss.IndexIVFPQ(quantizer, dimension, nlist, m, 8)
            
            # Train the index
            print(f"Training IVFPQ index with {nlist} centroids...")
            index.train(embeddings)
            print(f"STATS: Created IVFPQ index for {n_vectors} vectors")
        
        # Add vectors to index
        print("ADDING: Adding vectors to index...")
        index.add(embeddings)
        
        return index
    
    def _save_outputs(self, 
                     embeddings: np.ndarray, 
                     metadata_list: List[Dict], 
                     id_map: List[str], 
                     faiss_index: faiss.Index):
        """Save all outputs to files"""
        
        print("SAVING: Saving enhanced vector outputs...")
        
        # Save embeddings
        np.save(self.embeddings_file, embeddings)
        print(f"SUCCESS: Saved embeddings to {self.embeddings_file}")
        
        # Save metadata
        with open(self.metadata_file, 'wb') as f:
            pickle.dump(metadata_list, f)
        print(f"SUCCESS: Saved metadata to {self.metadata_file}")
        
        # Save ID mapping
        with open(self.index_map_file, 'wb') as f:
            pickle.dump(id_map, f)
        print(f"SUCCESS: Saved ID mapping to {self.index_map_file}")
        
        # Save FAISS index
        faiss.write_index(faiss_index, str(self.faiss_index_file))
        print(f"SUCCESS: Saved FAISS index to {self.faiss_index_file}")
    
    def _generate_statistics(self, chunks: List[Dict], metadata_list: List[Dict]):
        """Generate comprehensive statistics"""
        
        # Calculate averages
        if metadata_list:
            completeness_scores = [m.get('completeness_score', 0.0) for m in metadata_list]
            token_efficiencies = [m.get('token_efficiency', 0.0) for m in metadata_list]
            
            self.stats['average_completeness_score'] = np.mean(completeness_scores)
            self.stats['average_token_efficiency'] = np.mean(token_efficiencies)
        
        # Count unique sections
        unique_sections = set()
        unique_groups = set()
        
        for metadata in metadata_list:
            section_id = metadata.get('section_id')
            if section_id:
                unique_sections.add(section_id)
            
            group_id = metadata.get('group_id')
            if group_id:
                unique_groups.add(group_id)
        
        self.stats['unique_sections'] = len(unique_sections)
        self.stats['unique_groups'] = len(unique_groups)
        
        # Convert defaultdict to regular dict for JSON serialization
        self.stats['content_type_distribution'] = dict(self.stats['content_type_distribution'])
        self.stats['semantic_role_distribution'] = dict(self.stats['semantic_role_distribution'])
        self.stats['level_distribution'] = dict(self.stats['level_distribution'])
        self.stats['quality_flag_distribution'] = dict(self.stats['quality_flag_distribution'])
        self.stats['classification_method_distribution'] = dict(self.stats['classification_method_distribution'])
    
    def _save_statistics(self):
        """Save processing statistics"""
        
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        
        print(f"STATS: Saved statistics to {self.stats_file}")
    
    def print_summary(self):
        """Print processing summary"""
        
        print("\n" + "="*70)
        print("STATS: ENHANCED VECTOR PROCESSING SUMMARY")
        print("="*70)
        
        print(f"INPUT: {self.input_jsonl_file}")
        print(f"OUTPUT: Output: {self.output_dir}")
        print(f"TOTAL: Total chunks processed: {self.stats['total_chunks_processed']}")
        print(f"SUCCESS: Chunks included in index: {self.stats['chunks_included']}")
        print(f"FILTERED: Chunks filtered out: {self.stats['chunks_filtered_out']}")
        print(f"Embedding dimension: {self.stats['embedding_dimension']}")
        
        print(f"\nSTATS: Content Distribution:")
        for content_type, count in self.stats['content_type_distribution'].items():
            percentage = (count / self.stats['chunks_included']) * 100
            print(f"  • {content_type}: {count} ({percentage:.1f}%)")
        
        print(f"\nSemantic Role Distribution:")
        for role, count in self.stats['semantic_role_distribution'].items():
            percentage = (count / self.stats['chunks_included']) * 100
            print(f"  • {role}: {count} ({percentage:.1f}%)")
        
        print(f"\nLevel Distribution:")
        for level, count in self.stats['level_distribution'].items():
            percentage = (count / self.stats['chunks_included']) * 100
            print(f"  • {level}: {count} ({percentage:.1f}%)")
        
        print(f"\nQuality Metrics:")
        print(f"  • Average completeness: {self.stats['average_completeness_score']:.2f}")
        print(f"  • Average token efficiency: {self.stats['average_token_efficiency']:.2f}")
        print(f"  • Chunks needing review: {self.stats['chunks_needing_review']}")
        
        quality_total = sum(self.stats['quality_flag_distribution'].values())
        if quality_total > 0:
            print(f"  • Quality distribution:")
            for flag, count in self.stats['quality_flag_distribution'].items():
                percentage = (count / quality_total) * 100
                print(f"    - {flag}: {count} ({percentage:.1f}%)")
        
        print(f"\nClassification Methods:")
        for method, count in self.stats['classification_method_distribution'].items():
            percentage = (count / self.stats['chunks_included']) * 100
            print(f"  • {method}: {count} ({percentage:.1f}%)")
        
        print(f"\nCustomer Support Enhancements:")
        if self.enable_multi_embeddings:
            print(f"  • Total user questions: {self.stats['total_user_questions']}")
            print(f"  • Question embeddings: {self.stats['question_embeddings_generated']}")
            print(f"  • Combined embeddings: {self.stats['combined_embeddings_generated']}")
        else:
            print(f"  • Multi-embedding: Disabled")

        print(f"\nSupport Category Distribution:")
        for category, count in self.stats['support_category_distribution'].items():
            percentage = (count / self.stats['chunks_included']) * 100
            print(f"  • {category}: {count} ({percentage:.1f}%)")

        print(f"\nDifficulty Level Distribution:")
        for level, count in self.stats['difficulty_level_distribution'].items():
            percentage = (count / self.stats['chunks_included']) * 100
            print(f"  • {level}: {count} ({percentage:.1f}%)")

        print(f"\nDomain Category Distribution:")
        for domain, count in self.stats['domain_category_distribution'].items():
            percentage = (count / self.stats['chunks_included']) * 100
            print(f"  • {domain}: {count} ({percentage:.1f}%)")

        print(f"\nTOTAL: Organization:")
        print(f"  • Unique sections: {self.stats['unique_sections']}")
        print(f"  • Unique groups: {self.stats['unique_groups']}")

        if self.stats['processing_errors']:
            print(f"\nWARNING: Processing Errors: {len(self.stats['processing_errors'])}")
            for error in self.stats['processing_errors'][:3]:
                print(f"  - {error}")
            if len(self.stats['processing_errors']) > 3:
                print(f"  ... and {len(self.stats['processing_errors']) - 3} more")
        
        print("="*70)

    def _generate_additional_embeddings(self, chunk: Dict[str, Any], metadata: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Generate question and combined embeddings for enhanced search"""
        try:
            content = chunk.get('content', '')
            user_questions = metadata.get('user_questions', [])

            # Generate question embeddings
            question_embedding = None
            if user_questions:
                # Combine all user questions for this chunk
                questions_text = " ".join(user_questions)
                question_response = self.embedding_model.get_embeddings([questions_text])
                if question_response and len(question_response) > 0:
                    question_embedding = np.array(question_response[0].values, dtype='float32')
                    self.stats['question_embeddings_generated'] += 1
                    self.stats['total_user_questions'] += len(user_questions)

            # Generate combined embedding (content + questions)
            combined_embedding = None
            if user_questions:
                combined_text = content + " " + " ".join(user_questions)
                combined_response = self.embedding_model.get_embeddings([combined_text])
                if combined_response and len(combined_response) > 0:
                    combined_embedding = np.array(combined_response[0].values, dtype='float32')
                    self.stats['combined_embeddings_generated'] += 1

            # Use content embedding as fallback
            content_embedding = np.array(chunk['embedding'], dtype='float32')
            if question_embedding is None:
                question_embedding = content_embedding
            if combined_embedding is None:
                combined_embedding = content_embedding

            return question_embedding, combined_embedding

        except Exception as e:
            print(f"WARNING: Failed to generate additional embeddings for {chunk.get('id', 'unknown')}: {e}")
            # Return content embedding as fallback
            content_embedding = np.array(chunk['embedding'], dtype='float32')
            return content_embedding, content_embedding

    def _apply_level_weights(self, clean_metadata: Dict[str, Any], original_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Apply level-aware processing weights for customer support optimization"""

        level = original_metadata.get('level', 'L1')

        # Level-specific search weights and priorities
        level_weights = {
            'L0': {'retrieval_priority': 'high', 'search_weight': 1.2},     # Quick facts
            'L1': {'retrieval_priority': 'normal', 'search_weight': 1.0},   # Standard sections
            'L2': {'retrieval_priority': 'medium', 'search_weight': 1.1},   # Summaries
            'QA': {'retrieval_priority': 'high', 'search_weight': 1.3},     # Q&A pairs
            'L3': {'retrieval_priority': 'medium', 'search_weight': 0.9},   # Document level
            'L4': {'retrieval_priority': 'normal', 'search_weight': 1.0}    # Cross-references
        }

        if level in level_weights:
            clean_metadata['retrieval_priority'] = level_weights[level]['retrieval_priority']
            clean_metadata['search_weight'] = level_weights[level]['search_weight']
        else:
            clean_metadata['retrieval_priority'] = 'normal'
            clean_metadata['search_weight'] = 1.0

        # Add customer support specific metadata
        clean_metadata['user_questions'] = original_metadata.get('user_questions', [])
        clean_metadata['difficulty_level'] = original_metadata.get('difficulty_level', 'beginner')
        clean_metadata['estimated_time'] = original_metadata.get('estimated_time', '1 minute')
        clean_metadata['support_category'] = original_metadata.get('support_category', 'information')
        clean_metadata['domain_category'] = original_metadata.get('domain_category', 'electronics')
        clean_metadata['user_synonyms'] = original_metadata.get('user_synonyms', {})
        clean_metadata['escalation_path'] = original_metadata.get('escalation_path', [])

        return clean_metadata

    def _save_additional_embeddings(self, question_embeddings: np.ndarray, combined_embeddings: np.ndarray, embedding_types: List[Dict]):
        """Save additional embedding arrays for multi-embedding search"""
        try:
            # Save question embeddings
            np.save(self.question_embeddings_file, question_embeddings)
            print(f"SUCCESS: Saved question embeddings to {self.question_embeddings_file}")

            # Save combined embeddings
            np.save(self.combined_embeddings_file, combined_embeddings)
            print(f"SUCCESS: Saved combined embeddings to {self.combined_embeddings_file}")

            # Save embedding types mapping
            with open(self.embedding_types_file, 'wb') as f:
                pickle.dump(embedding_types, f)
            print(f"SUCCESS: Saved embedding types to {self.embedding_types_file}")

        except Exception as e:
            print(f"WARNING: Failed to save additional embeddings: {e}")

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced vector preparation from JSONL chunks")
    parser.add_argument("input_jsonl", help="Input JSONL file with enhanced chunks")
    parser.add_argument("--output-dir", default="training/output/vectors", help="Output directory")
    parser.add_argument("--disable-quality-filter", action="store_true", help="Disable quality filtering")
    parser.add_argument("--min-quality", type=float, default=0.2, help="Minimum quality score for inclusion")
    parser.add_argument("--disable-multi-embeddings", action="store_true", help="Disable multi-embedding generation")

    args = parser.parse_args()

    # Initialize processor
    processor = EnhancedVectorProcessor(
        input_jsonl_file=args.input_jsonl,
        output_dir=args.output_dir,
        enable_quality_filtering=not args.disable_quality_filter,
        min_quality_score=args.min_quality,
        enable_multi_embeddings=not args.disable_multi_embeddings
    )
    
    try:
        # Process vectors
        stats = processor.process_jsonl()
        
        # Print summary
        processor.print_summary()
        
        return 0
        
    except Exception as e:
        print(f"ERROR: Processing failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())