# training/scripts/generate_jsonl_enhanced.py
import os
import json
import sys
import argparse
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Google Cloud imports
import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput
from vertexai.generative_models import GenerativeModel, Part
from google.oauth2 import service_account

# Local imports
from app.config import *
from training.scripts.semantic_chunker_enhanced import EnhancedSemanticChunker, chunk_text_with_metadata

class EnhancedTemplateProcessor:
    """Enhanced processor for Markdown templates with LLM classification and quality scoring"""
    
    def __init__(self, 
                 project_id: str = PROJECT_ID,
                 location: str = LOCATION,
                 credentials_path: str = None,
                 output_dir: str = "training/output/chunks"):
        
        self.project_id = project_id
        self.location = location
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.enable_llm_classification = getattr(sys.modules['app.config'], 'ENABLE_LLM_CLASSIFICATION', True)
        self.enable_multi_level_chunking = getattr(sys.modules['app.config'], 'ENABLE_MULTI_LEVEL_CHUNKING', True)
        
        # Initialize services
        self._initialize_vertex_ai(credentials_path)
        self._initialize_models()
        
        # Initialize enhanced chunker with shared credentials
        self.chunker = EnhancedSemanticChunker(
            min_chunk_size=CHUNK_SIZE_MIN,
            max_chunk_size=CHUNK_SIZE_MAX,
            overlap_percent=CHUNK_OVERLAP_PERCENT
        )

        # Pass the already-initialized model to the chunker's classifier to avoid double initialization
        if hasattr(self.chunker, 'classifier') and hasattr(self, 'generative_model'):
            self.chunker.classifier.model = self.generative_model  # Reuse the same model instance
            print("SUCCESS: Shared Gemini model with content classifier to avoid duplicate auth")
        
        # Statistics tracking
        self.stats = {
            'templates_processed': 0,
            'sections_processed': 0,
            'chunks_created': 0,
            'l1_chunks': 0,
            'l2_chunks': 0,
            'l3_chunks': 0,
            'embeddings_generated': 0,
            'summaries_generated': 0,
            'llm_classifications': 0,
            'pattern_fallbacks': 0,
            'quality_flags': {'high': 0, 'medium': 0, 'low': 0},
            'needs_review': 0,
            'errors': []
        }
    
    def _initialize_vertex_ai(self, credentials_path: str = None):
        """Initialize Vertex AI with robust local/cloud credential handling."""
        try:
            print("DEBUG: Initializing Vertex AI...", flush=True)

            # Detect if running locally (no Cloud Run environment)
            is_local = os.getenv("CLOUD_RUN_JOB", "") == "" and os.getenv("CLOUD_RUN_SERVICE", "") == ""
            cred_path = credentials_path or os.getenv("VERTEX_CREDENTIALS_PATH", "gcp-keys/service-account-key.json")

            if is_local:
                print("DEBUG: Detected LOCAL environment", flush=True)
                print(f"DEBUG: Looking for Vertex AI credentials at: {cred_path}")

                if not os.path.exists(cred_path):
                    print(f"ERROR: Service account key not found at {cred_path}.", flush=True)
                    print("DEBUG: Falling back to ADC (gcloud auth application-default login).", flush=True)
                    vertexai.init(project=self.project_id, location=self.location)
                else:
                    vertex_credentials = service_account.Credentials.from_service_account_file(cred_path)
                    vertexai.init(project=self.project_id, location=self.location, credentials=vertex_credentials)
                    print("SUCCESS: Vertex AI initialized with local credentials", flush=True)
            else:
                print("DEBUG: Detected CLOUD environment (Cloud Run / GCP)", flush=True)
                vertexai.init(project=self.project_id, location=self.location)
                print("SUCCESS: Vertex AI initialized with default cloud credentials", flush=True)

        except Exception as e:
            raise Exception(f"ERROR: Failed to initialize Vertex AI: {e}")


    
    def _initialize_models(self):
        """Initialize embedding and generative models"""
        try:
            self.embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_NAME)
            self.generative_model = GenerativeModel(GENERATIVE_MODEL_NAME)
            print(f"SUCCESS: Models initialized: {EMBEDDING_MODEL_NAME}, {GENERATIVE_MODEL_NAME}")
        except Exception as e:
            raise Exception(f"Failed to initialize models: {e}")
    
    def parse_template(self, template_path: str) -> Dict[str, Any]:
        """Parse a Markdown template file with enhanced metadata extraction"""
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract document metadata
        doc_metadata = self._extract_document_metadata(content)
        
        # Parse sections
        sections = self._parse_sections(content)
        
        return {
            'template_path': template_path,
            'document_metadata': doc_metadata,
            'sections': sections,
            'total_sections': len(sections)
        }
    
    def _extract_document_metadata(self, content: str) -> Dict[str, Any]:
        """Extract enhanced document-level metadata"""
        metadata = {}
        
        # Look for metadata section
        metadata_match = re.search(r'## Document Metadata\s*\n(.*?)\n---', content, re.DOTALL)
        if metadata_match:
            metadata_text = metadata_match.group(1)
            
            for line in metadata_text.split('\n'):
                if line.strip().startswith('- **'):
                    match = re.match(r'- \*\*([^*]+)\*\*:\s*(.+)', line.strip())
                    if match:
                        key = match.group(1).lower().replace(' ', '_').replace('/', '_')
                        value = match.group(2)
                        metadata[key] = value
        
        # Set enhanced defaults
        metadata.setdefault('language', DEFAULT_LANGUAGE)
        metadata.setdefault('version', 'v1.0.0')
        metadata.setdefault('source_type', 'manual')
        metadata.setdefault('document_type', 'technical_manual')
        metadata.setdefault('domain', 'any')
        
        return metadata
    
    def _parse_sections(self, content: str) -> List[Dict[str, Any]]:
        """Parse sections with enhanced metadata"""
        sections = []
        
        # Find all sections
        section_pattern = r'## Section \d+: ([^\n]+)\n(.*?)(?=## Section \d+:|$)'
        section_matches = re.findall(section_pattern, content, re.DOTALL)
        
        for i, (title, section_content) in enumerate(section_matches):
            section = self._parse_single_section(title, section_content, i)
            if section:
                sections.append(section)
        
        return sections
    
    def _parse_single_section(self, title: str, content: str, index: int) -> Optional[Dict[str, Any]]:
        """Parse a single section with enhanced structure"""
        try:
            section = {
                'title': title.strip(),
                'section_index': index,
                'content': '',
                'subtitle': '',
                'page_number': '',
                'section_id': '',
                'images': [],
                'keywords': [],
                'related_sections': [],
                'is_complete_section': True,
                'estimated_reading_time': 0,
                'complexity_level': 'basic'
            }
            
            # Parse section content
            lines = content.split('\n')
            current_section = None
            content_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('**Subtitle**:'):
                    section['subtitle'] = line.replace('**Subtitle**:', '').strip()
                elif line.startswith('**Page Number**:'):
                    section['page_number'] = line.replace('**Page Number**:', '').strip()
                elif line.startswith('**Section ID**:'):
                    section['section_id'] = line.replace('**Section ID**:', '').strip()
                elif line == '### Content':
                    current_section = 'content'
                elif line == '### Images':
                    current_section = 'images'
                elif line == '### Metadata':
                    current_section = 'metadata'
                elif line.startswith('**Image Filename**:'):
                    if current_section == 'images':
                        filename = line.replace('**Image Filename**:', '').strip()
                        section['images'].append({'filename': filename})
                elif line.startswith('**Firebase Path**:'):
                    if section['images'] and current_section == 'images':
                        section['images'][-1]['firebase_path'] = line.replace('**Firebase Path**:', '').strip()
                elif line.startswith('**Image Description**:'):
                    if section['images'] and current_section == 'images':
                        section['images'][-1]['description'] = line.replace('**Image Description**:', '').strip()
                elif line.startswith('**Keywords**:'):
                    keywords_text = line.replace('**Keywords**:', '').strip()
                    section['keywords'] = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
                elif line.startswith('**Related Sections**:'):
                    related_text = line.replace('**Related Sections**:', '').strip()
                    if related_text.startswith('[') and related_text.endswith(']'):
                        related_text = related_text[1:-1]
                    section['related_sections'] = [rs.strip() for rs in related_text.split(',') if rs.strip()]
                elif line.startswith('**Is Complete Section**:'):
                    is_complete = line.replace('**Is Complete Section**:', '').strip().lower()
                    section['is_complete_section'] = is_complete == 'true'
                elif current_section == 'content' and not line.startswith('**'):
                    content_lines.append(line)
            
            # Process content
            section['content'] = '\n'.join(content_lines).strip()
            
            # Generate section_id if missing
            if not section['section_id']:
                safe_title = re.sub(r'[^a-zA-Z0-9_]', '_', section['title'].lower())
                section['section_id'] = f"{safe_title}_{index:03d}"
            
            # Calculate enhanced metadata
            section['estimated_reading_time'] = self._estimate_reading_time(section['content'])
            section['complexity_level'] = self._assess_complexity(section['content'])
            
            # Validate section
            if not section['content']:
                print(f"WARNING: Section '{title}' has no content, skipping")
                return None
            
            return section
            
        except Exception as e:
            print(f"ERROR: Failed to parse section '{title}': {e}")
            self.stats['errors'].append(f"Section parsing error: {e}")
            return None
    
    def _estimate_reading_time(self, content: str) -> int:
        """Estimate reading time in minutes (200 words per minute)"""
        word_count = len(content.split())
        return max(1, round(word_count / 200))
    
    def _assess_complexity(self, content: str) -> str:
        """Assess content complexity level"""
        # Count technical indicators
        technical_indicators = 0
        
        # Technical terms
        if re.search(r'\d+\s*(?:psi|rpm|°f|°c|volts?)', content, re.IGNORECASE):
            technical_indicators += 2
        
        # Procedure steps
        if re.search(r'step\s+\d+', content, re.IGNORECASE):
            technical_indicators += 1
        
        # Safety warnings
        if re.search(r'danger|warning|caution', content, re.IGNORECASE):
            technical_indicators += 1
        
        # Complex sentences
        long_sentences = len([s for s in content.split('.') if len(s.split()) > 20])
        technical_indicators += min(long_sentences // 3, 2)
        
        if technical_indicators >= 4:
            return 'advanced'
        elif technical_indicators >= 2:
            return 'intermediate'
        else:
            return 'basic'
    
    def generate_embedding(self, text: str, chunk_id: str = "") -> Optional[List[float]]:
        """Generate embedding with error handling"""
        try:
            # Truncate if too long
            if len(text) > 8000:  # Conservative limit
                text = text[:8000] + "..."
            
            inputs = [TextEmbeddingInput(text)]
            response = self.embedding_model.get_embeddings(inputs)
            embedding = response[0].values
            self.stats['embeddings_generated'] += 1
            return embedding
            
        except Exception as e:
            error_msg = f"Failed to generate embedding for {chunk_id}: {e}"
            print(f"ERROR: {error_msg}")
            self.stats['errors'].append(error_msg)
            return None
    
    def generate_summary(self, content: str, max_length: int = 150) -> str:
        """Generate enhanced summary using Gemini"""
        try:
            prompt = f"""
Create a concise, informative summary of this technical content in {max_length} characters or less.
Focus on key actions, components, safety information, and procedures mentioned.

Content:
{content[:3000]}

Requirements:
- Highlight any safety warnings or critical information
- Include key procedural steps if present
- Mention specific equipment or components
- Use clear, technical language
- Stay under {max_length} characters

Summary:"""
            
            response = self.generative_model.generate_content(
                [Part.from_text(prompt)],
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 80
                }
            )
            
            if response.candidates and response.candidates[0].content.parts:
                summary = response.candidates[0].content.parts[0].text.strip()
                self.stats['summaries_generated'] += 1
                return summary[:max_length]
            else:
                return content[:max_length] + "..." if len(content) > max_length else content
                
        except Exception as e:
            print(f"WARNING: Failed to generate summary: {e}")
            return content[:max_length] + "..." if len(content) > max_length else content
    
    def generate_document_summary(self, sections: List[Dict[str, Any]], doc_metadata: Dict[str, Any]) -> str:
        """Generate L3 document-level summary"""
        try:
            # Prepare document overview
            section_summaries = []
            for section in sections[:10]:  # Limit to first 10 sections
                title = section['title']
                content_preview = section['content'][:200]
                section_summaries.append(f"- {title}: {content_preview}")
            
            overview_text = "\n".join(section_summaries)
            
            prompt = f"""
Create a comprehensive summary of this technical manual in 500-800 tokens.

Document Title: {doc_metadata.get('title', 'Technical Manual')}
Version: {doc_metadata.get('version', 'Unknown')}
Type: {doc_metadata.get('source_type', 'Manual')}

Section Overview:
{overview_text}

Create a summary that:
- Provides a clear overview of the manual's purpose and scope
- Highlights key safety information and warnings
- Summarizes major procedural sections
- Mentions important technical specifications
- Uses professional technical language
- Is useful for quick reference and context

Summary:"""
            
            response = self.generative_model.generate_content(
                [Part.from_text(prompt)],
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 400
                }
            )
            
            if response.candidates and response.candidates[0].content.parts:
                return response.candidates[0].content.parts[0].text.strip()
            else:
                return f"Technical manual covering {len(sections)} sections including operational procedures, safety protocols, and maintenance guidelines."
                
        except Exception as e:
            print(f"WARNING: Failed to generate document summary: {e}")
            return f"Technical manual covering {len(sections)} sections including operational procedures, safety protocols, and maintenance guidelines."
    
    def process_template(self, template_path: str, output_filename: str = None) -> str:
        """Process template with enhanced chunking and classification"""
        print(f"\nProcessing template: {template_path}")
        
        # Parse template
        parsed_template = self.parse_template(template_path)
        doc_metadata = parsed_template['document_metadata']
        sections = parsed_template['sections']
        
        # Generate output filename
        if output_filename is None:
            template_name = Path(template_path).stem
            output_filename = f"{template_name}_enhanced_chunks.jsonl"
        
        output_path = self.output_dir / output_filename
        
        # Generate L3 document summary if enabled
        l3_chunks = []
        if self.enable_multi_level_chunking:
            doc_summary = self.generate_document_summary(sections, doc_metadata)
            l3_chunk = self._create_l3_chunk(doc_summary, doc_metadata, template_path)
            if l3_chunk:
                l3_chunks.append(l3_chunk)
                self.stats['l3_chunks'] += 1
        
        # Import universal chunking system
        from training.scripts.chunking_orchestrator import UniversalChunkingOrchestrator

        # Initialize universal chunking orchestrator
        print("=> Initializing Universal Customer Support Chunking System...")
        orchestrator = UniversalChunkingOrchestrator(model=self.generative_model)

        # Process sections using universal system
        all_chunks = []
        all_chunks.extend(l3_chunks)  # Add L3 first

        for section_index, section in enumerate(sections):
            print(f"  -> Processing section with Universal System: {section['title']}")

            # Prepare base metadata
            base_metadata = {
                **doc_metadata,
                'title': section['title'],
                'subtitle': section['subtitle'],
                'section_id': section['section_id'],
                'page_number': section['page_number'],
                'keywords': section['keywords'],
                'related_sections': section['related_sections'],
                'is_complete_section': section['is_complete_section'],
                'estimated_reading_time': section['estimated_reading_time'],
                'complexity_level': section['complexity_level']
            }

            # Handle images
            if section['images']:
                image = section['images'][0]
                base_metadata['image_firebase_url'] = image.get('firebase_path', '')
                base_metadata['image_description'] = image.get('description', '')

            # Process section with Universal Chunking System
            if section['content'].strip():
                try:
                    # Generate multi-level chunks using universal system
                    universal_chunks = orchestrator.process_section(
                        section['content'],
                        base_metadata,
                        section['title']
                    )

                    # Process each universal chunk through existing pipeline
                    for universal_chunk in universal_chunks:
                        # Add embedding if not present
                        if 'embedding' not in universal_chunk:
                            embedding = self.generate_embedding(
                                universal_chunk['content'],
                                universal_chunk['id']
                            )
                            universal_chunk['embedding'] = embedding

                        # Generate summary if not present
                        if 'summary' not in universal_chunk.get('metadata', {}):
                            summary = self.generate_summary(universal_chunk['content'])
                            universal_chunk['metadata']['summary'] = summary

                        # Ensure required fields
                        from datetime import datetime
                        universal_chunk['metadata']['processed_at'] = datetime.utcnow().isoformat()
                        universal_chunk['metadata']['original_text_chunk'] = universal_chunk['content']

                        all_chunks.append(universal_chunk)

                        # Update statistics based on chunk level
                        level = universal_chunk['metadata'].get('level', 'L1')
                        if level == 'L0':
                            self.stats['l1_chunks'] += 1  # Count as L1 for compatibility
                        elif level == 'L1':
                            self.stats['l1_chunks'] += 1
                        elif level == 'L2':
                            self.stats['l2_chunks'] += 1
                        elif level == 'QA':
                            self.stats['l1_chunks'] += 1  # Count as L1 for compatibility
                        elif level == 'L4':
                            self.stats['l1_chunks'] += 1  # Count as L1 for compatibility

                        # Track quality
                        quality_flag = universal_chunk['metadata'].get('quality_flag', 'high')
                        self.stats['quality_flags'][quality_flag] += 1

                        # Track classification method
                        method = universal_chunk['metadata'].get('classification_method', 'universal_system')
                        if method == 'llm' or method == 'universal_system':
                            self.stats['llm_classifications'] += 1
                        else:
                            self.stats['pattern_fallbacks'] += 1

                    print(f"    => Generated {len(universal_chunks)} chunks from universal system")

                except Exception as e:
                    print(f"    WARNING: Universal system failed, falling back to basic chunking: {e}")

                    # Fallback to basic section chunk
                    section_chunk = self._create_section_chunk(
                        section['content'],
                        base_metadata,
                        section['title'],
                        section_index
                    )

                    if section_chunk:
                        processed_chunk = self._process_chunk(section_chunk)
                        if processed_chunk:
                            all_chunks.append(processed_chunk)
                            self.stats['l1_chunks'] += 1

            self.stats['sections_processed'] += 1

        # Print universal system statistics
        print("\n=> Universal Chunking System Results:")
        orchestrator.print_processing_statistics()
        
        # Write JSONL file
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in all_chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
        
        self.stats['templates_processed'] += 1
        self.stats['chunks_created'] = len(all_chunks)
        
        print(f"SUCCESS: Generated {len(all_chunks)} enhanced chunks in {output_path}")
        return str(output_path)
    
    def _create_section_chunk(self,
                             section_content: str,
                             base_metadata: Dict[str, Any],
                             section_title: str,
                             section_index: int) -> Optional[Dict[str, Any]]:
        """Create a single chunk containing the complete section content with no omission"""

        if not section_content.strip():
            return None

        # Use the existing chunker's classification but create single chunk
        classification = self.chunker.classifier.classify_chunk(section_content, section_title, base_metadata)

        # Calculate token count
        token_count = self.chunker.count_tokens(section_content)

        # Generate chunk ID
        section_id = base_metadata.get('section_id', f'section_{section_index}')
        chunk_id = f"{section_id}_complete_l1"

        # Build chunk with all content included
        chunk = {
            'id': chunk_id,
            'content': section_content,
            'metadata': {
                # Original metadata
                **base_metadata,

                # Chunk-specific metadata
                'chunk_order': 0,  # Single chunk per section
                'level': 'L1',
                'token_count': token_count,
                'char_start': 0,
                'char_end': len(section_content),

                # Classification metadata
                'content_type': classification['content_type'],
                'semantic_role': classification['semantic_role'],
                'group_id': classification.get('group_id'),
                'semantic_boundary_type': classification.get('reasoning', ''),
                'classification_method': classification.get('classification_method', 'section_based'),
                'classification_confidence': classification.get('confidence', 1.0),  # High confidence for complete sections

                # Quality metadata - always accept section content
                'completeness_score': 1.0,  # Complete section = 100% complete
                'token_efficiency': 2.0,    # Assume good efficiency for manual content
                'quality_flag': 'high',     # Manual sections are high quality
                'needs_review': False,      # No review needed for complete sections

                # Navigation metadata
                'previous_chunk': None,
                'next_chunk': None,
                'group_position': section_index + 1,
                'group_total': None,  # Will be set later

                # Retrieval hints
                'retrieval_priority': 'high',        # Sections are high priority
                'standalone_readable': True,         # Complete sections are standalone
                'requires_context': False,           # Self-contained

                # Processing metadata
                'processed_at': base_metadata.get('processed_at'),
                'original_text_chunk': section_content
            }
        }

        return chunk

    def _create_l3_chunk(self, doc_summary: str, doc_metadata: Dict[str, Any], template_path: str) -> Optional[Dict[str, Any]]:
        """Create L3 document-level chunk"""
        
        embedding = self.generate_embedding(doc_summary, "document_summary")
        if not embedding:
            return None
        
        chunk_id = f"document_summary_l3"
        
        return {
            'id': chunk_id,
            'content': doc_summary,
            'embedding': embedding,
            'metadata': {
                **doc_metadata,
                'level': 'L3',
                'content_type': 'reference',
                'semantic_role': 'overview',
                'chunk_order': 0,
                'token_count': len(doc_summary.split()) * 1.3,  # Rough estimate
                'quality_flag': 'high',
                'needs_review': False,
                'completeness_score': 1.0,
                'token_efficiency': 3.0,
                'retrieval_priority': 'medium',
                'standalone_readable': True,
                'requires_context': False,
                'classification_method': 'generated',
                'summary': doc_summary[:100] + "..." if len(doc_summary) > 100 else doc_summary,
                'original_text_chunk': doc_summary,
                'processed_at': datetime.utcnow().isoformat()
            }
        }
    
    def _process_chunk(self, chunk: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process individual chunk with embeddings and final formatting - no content filtering"""

        content = chunk.get('content', '').strip()
        if not content:
            return None

        # Generate embedding - if embedding fails, still keep the chunk with None embedding
        embedding = self.generate_embedding(content, chunk.get('id', ''))
        # Note: We no longer return None if embedding fails - we keep the chunk
        
        # Generate summary
        summary = self.generate_summary(content)
        
        # Build standardized chunk
        metadata = chunk.get('metadata', {})
        
        standardized_chunk = {
            'id': chunk.get('id'),
            'content': content,
            'embedding': embedding,  # May be None if embedding generation failed
            'metadata': {
                # Core metadata
                'source_type': metadata.get('source_type', 'manual'),
                'title': metadata.get('title', ''),
                'subtitle': metadata.get('subtitle', ''),
                'section_id': metadata.get('section_id', ''),
                'chunk_order': metadata.get('chunk_order', 0),
                'page_number': str(metadata.get('page_number', 'N/A')),
                'version': metadata.get('version', ''),
                'language': metadata.get('language', DEFAULT_LANGUAGE),
                
                # Enhanced classification
                'level': metadata.get('level', 'L1'),
                'content_type': metadata.get('content_type', 'manual_section'),
                'semantic_role': metadata.get('semantic_role', 'general'),
                'group_id': metadata.get('group_id'),
                'semantic_boundary_type': metadata.get('semantic_boundary_type', ''),
                'classification_method': metadata.get('classification_method', 'unknown'),
                'classification_confidence': metadata.get('classification_confidence', 0.0),
                
                # Quality metrics
                'completeness_score': metadata.get('completeness_score', 0.5),
                'token_efficiency': metadata.get('token_efficiency', 1.0),
                'quality_flag': metadata.get('quality_flag', 'medium'),
                'needs_review': metadata.get('needs_review', False),
                
                # Navigation
                'previous_chunk': metadata.get('previous_chunk'),
                'next_chunk': metadata.get('next_chunk'),
                'group_position': metadata.get('group_position'),
                'group_total': metadata.get('group_total'),
                
                # Retrieval hints
                'retrieval_priority': metadata.get('retrieval_priority', 'normal'),
                'standalone_readable': metadata.get('standalone_readable', True),
                'requires_context': metadata.get('requires_context', False),
                
                # Content metadata
                'token_count': metadata.get('token_count', 0),
                'char_start': metadata.get('char_start', 0),
                'char_end': metadata.get('char_end', 0),
                'estimated_reading_time': metadata.get('estimated_reading_time', 1),
                'complexity_level': metadata.get('complexity_level', 'basic'),
                
                # Media
                'image_gcs_uri': metadata.get('image_firebase_url', ''),
                'image_description': metadata.get('image_description', ''),
                
                # Generated content
                'summary': summary,
                'keywords': metadata.get('keywords', []),
                'related_sections': metadata.get('related_sections', []),
                'is_complete_section': metadata.get('is_complete_section', False),
                
                # Processing metadata
                'original_text_chunk': content,
                'processed_at': datetime.utcnow().isoformat()
            }
        }
        
        return standardized_chunk
    
    def print_enhanced_statistics(self):
        """Print comprehensive processing statistics"""
        print("\n" + "="*60)
        print("ENHANCED PROCESSING STATISTICS")
        print("="*60)
        print(f"Templates processed: {self.stats['templates_processed']}")
        print(f"Sections processed: {self.stats['sections_processed']}")
        print(f"Total chunks created: {self.stats['chunks_created']}")
        print(f"  • L1 chunks (semantic): {self.stats['l1_chunks']}")
        print(f"  • L2 chunks (section): {self.stats['l2_chunks']}")
        print(f"  • L3 chunks (document): {self.stats['l3_chunks']}")
        print(f"Embeddings generated: {self.stats['embeddings_generated']}")
        print(f"Summaries generated: {self.stats['summaries_generated']}")
        
        print(f"\nCLASSIFICATION METHODS:")
        print(f"  • LLM classifications: {self.stats['llm_classifications']}")
        print(f"  • Pattern fallbacks: {self.stats['pattern_fallbacks']}")
        
        print(f"\nQUALITY DISTRIBUTION:")
        total_quality = sum(self.stats['quality_flags'].values())
        if total_quality > 0:
            for flag, count in self.stats['quality_flags'].items():
                percentage = (count / total_quality) * 100
                print(f"  • {flag.capitalize()}: {count} ({percentage:.1f}%)")
        
        print(f"\nQUALITY ISSUES:")
        print(f"  • Chunks needing review: {self.stats['needs_review']}")
        print(f"  • Processing errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            print(f"\n❌ Error Summary:")
            for error in self.stats['errors'][:3]:
                print(f"  - {error}")
            if len(self.stats['errors']) > 3:
                print(f"  ... and {len(self.stats['errors']) - 3} more")
        
        print("="*60)

def main():
    """Enhanced main function"""
    parser = argparse.ArgumentParser(description="Enhanced Markdown template processor with LLM classification")
    parser.add_argument("input_path", help="Path to template file or directory")
    parser.add_argument("--project-id", default=PROJECT_ID, help="Google Cloud Project ID")
    parser.add_argument("--credentials", help="Path to service account credentials")
    parser.add_argument("--output-dir", default="training/output/chunks", help="Output directory")
    parser.add_argument("--disable-llm", action="store_true", help="Disable LLM classification")
    parser.add_argument("--disable-multi-level", action="store_true", help="Disable multi-level chunking")
    
    args = parser.parse_args()
    
    # Override config if specified
    if args.disable_llm:
        os.environ['ENABLE_LLM_CLASSIFICATION'] = 'false'
    if args.disable_multi_level:
        os.environ['ENABLE_MULTI_LEVEL_CHUNKING'] = 'false'
    
    # Initialize processor
    processor = EnhancedTemplateProcessor(
        project_id=args.project_id,
        credentials_path=args.credentials,
        output_dir=args.output_dir
    )
    
    # Process input
    input_path = Path(args.input_path)
    
    if input_path.is_file():
        output_file = processor.process_template(str(input_path))
        print(f"\nSUCCESS: Processed single template: {output_file}")
    elif input_path.is_dir():
        template_files = list(input_path.glob("*.md"))
        if not template_files:
            print(f"❌ No .md files found in {input_path}")
            return 1
        
        print(f"📁 Found {len(template_files)} template files")
        output_files = []
        
        for template_file in template_files:
            try:
                output_file = processor.process_template(str(template_file))
                output_files.append(output_file)
            except Exception as e:
                error_msg = f"Failed to process {template_file}: {e}"
                print(f"❌ {error_msg}")
                processor.stats['errors'].append(error_msg)
        
        print(f"\n✅ Processed {len(output_files)} templates successfully")
    else:
        print(f"❌ Invalid input path: {input_path}")
        return 1
    
    # Print statistics
    processor.print_enhanced_statistics()
    
    return 0

if __name__ == "__main__":
    exit(main())