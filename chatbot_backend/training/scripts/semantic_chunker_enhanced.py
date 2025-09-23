# training/scripts/semantic_chunker_enhanced.py
import sys
import os
import re
import tiktoken
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.config import *
from training.scripts.content_classifier import ContentClassifier

@dataclass
class ChunkBoundary:
    """Represents a potential chunk boundary with metadata"""
    position: int
    strength: int  # 1-5, higher = better boundary
    reason: str
    context: str

@dataclass
class QualityMetrics:
    """Quality metrics for a chunk"""
    completeness_score: float
    token_efficiency: float
    quality_flag: str  # 'low', 'medium', 'high'
    needs_review: bool

class EnhancedSemanticChunker:
    """Advanced semantic text chunker with LLM classification and quality scoring"""
    
    def __init__(self, 
                 min_chunk_size: int = 512,
                 max_chunk_size: int = 1024,
                 overlap_percent: int = 10,  # Reduced overlap for cleaner chunks
                 encoding_name: str = "cl100k_base"):
        
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_percent = overlap_percent
        self.overlap_tokens = int((overlap_percent / 100) * min_chunk_size)
        
        # Quality thresholds
        self.min_completeness_score = getattr(sys.modules['app.config'], 'MIN_COMPLETENESS_SCORE', 0.3)
        self.min_token_efficiency = getattr(sys.modules['app.config'], 'MIN_TOKEN_EFFICIENCY', 0.7)
        
        # Initialize tokenizer
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            print(f"WARNING: Failed to load tiktoken encoding {encoding_name}: {e}")
            self.encoding = None
        
        # Initialize content classifier
        self.classifier = ContentClassifier()
        
        # Domain-specific keywords for token efficiency calculation
        self.domain_keywords = {
            "introduction", "overview", "purpose", "scope", "specifications", "features",
            "components", "parts", "diagram", "schematic", "wiring", "pinout", "labeling",
            "table of contents", "glossary", "index", "appendix", "revision history",
        }
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken or fallback"""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            return int(len(text.split()) * 1.3)
    
    def find_semantic_boundaries(self, text: str) -> List[ChunkBoundary]:
        """Find semantic boundaries with enhanced strength scoring"""
        boundaries = []
        
        boundary_patterns = [
            # Strongest boundaries (5) - Major structural breaks
            (r'\n\n#{1,6}\s+[^\n]+\n', 5, "Major heading"),
            (r'\n\n## Section \d+:', 5, "Document section"),
            (r'\n\n\*\*(?:DANGER|WARNING|CAUTION)\*\*', 5, "Critical safety alert"),
            
            # Strong boundaries (4) - Procedural and structural
            (r'\n\n(?:Step|STEP)\s+\d+[:\.]', 4, "Procedure step"),
            (r'\n\n\*\*[^*]+\*\*\s*[:\n]', 4, "Bold subheading"),
            (r'\n\n\d+\.\s+[A-Z][^\n]+\n', 4, "Numbered section"),
            (r'\n\n\*\*(?:NOTE|IMPORTANT)\*\*', 4, "Alert marker"),
            
            # Moderate boundaries (3) - Content organization
            (r'\n\n•\s+', 3, "Bullet point"),
            (r'\n\n-\s+', 3, "Dash list"),
            (r'\n\n\d+\)\s+', 3, "Numbered list"),
            (r'\.\s*\n\n[A-Z]', 3, "Paragraph break"),
            
            # Weak boundaries (2) - Sentence level
            (r'\.\s+[A-Z][a-z]', 2, "Sentence boundary"),
            (r'[;:]\s*\n', 2, "Clause break"),
        ]
        
        # Find all boundaries
        for pattern, strength, reason in boundary_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                position = match.end()
                context = text[max(0, position-30):position+30].replace('\n', '\\n')
                
                boundaries.append(ChunkBoundary(
                    position=position,
                    strength=strength,
                    reason=reason,
                    context=context
                ))
        
        # Sort by position and remove close duplicates
        boundaries.sort(key=lambda b: b.position)
        unique_boundaries = []
        last_pos = -1
        
        for boundary in boundaries:
            if boundary.position - last_pos > 10:  # Minimum separation
                unique_boundaries.append(boundary)
                last_pos = boundary.position
            elif unique_boundaries and boundary.strength > unique_boundaries[-1].strength:
                unique_boundaries[-1] = boundary
        
        return unique_boundaries
    
    def chunk_text_enhanced(self, 
                           text: str, 
                           base_metadata: Dict[str, Any] = None,
                           section_title: str = "") -> List[Dict[str, Any]]:
        """
        Enhanced chunking with multi-level support and quality scoring
        
        Args:
            text: Input text to chunk
            base_metadata: Base metadata to include in each chunk
            section_title: Section title for context
            
        Returns:
            List of enhanced chunk dictionaries
        """
        if not text.strip():
            return []
        
        base_metadata = base_metadata or {}
        chunks = []
        
        # Create L1 chunks (primary semantic chunks)
        l1_chunks = self._create_l1_chunks(text, base_metadata, section_title)
        
        # Create L2 chunk (full section) if text is large enough
        l2_chunk = self._create_l2_chunk(text, base_metadata, section_title)
        if l2_chunk:
            chunks.append(l2_chunk)
        
        # Add L1 chunks
        chunks.extend(l1_chunks)
        
        return chunks
    
    def _create_l1_chunks(self, 
                         text: str, 
                         base_metadata: Dict[str, Any],
                         section_title: str) -> List[Dict[str, Any]]:
        """Create L1 semantic chunks (512-1024 tokens)"""
        
        token_count = self.count_tokens(text)
        
        # If text is small enough, create single chunk
        if token_count <= self.max_chunk_size:
            chunk = self._create_single_chunk(text, base_metadata, section_title, 0, level="L1")
            return [chunk] if chunk else []
        
        # Find semantic boundaries
        boundaries = self.find_semantic_boundaries(text)
        chunks = []
        chunk_start = 0
        chunk_order = 0
        
        while chunk_start < len(text):
            # Find optimal chunk end
            chunk_end = self._find_optimal_chunk_end(
                text, chunk_start, boundaries, token_count
            )
            
            # Extract chunk content - no size filtering, keep all content
            chunk_content = text[chunk_start:chunk_end].strip()
            if not chunk_content:
                # Only skip if completely empty
                chunk_start = chunk_end
                continue
            
            # Create chunk
            chunk = self._create_single_chunk(
                chunk_content, base_metadata, section_title, chunk_order, 
                level="L1", char_start=chunk_start, char_end=chunk_end
            )
            
            if chunk:
                chunks.append(chunk)
                chunk_order += 1
            
            # Calculate next start with minimal overlap
            overlap_chars = self._calculate_overlap_chars(text, chunk_start, chunk_end)
            next_start = chunk_end - overlap_chars
            
            # Ensure progress
            if next_start <= chunk_start:
                next_start = chunk_start + max(1, (chunk_end - chunk_start) // 2)
            
            chunk_start = next_start
            
            # Prevent infinite loops
            if chunk_start >= len(text) - 100:
                break
        
        # Set navigation metadata
        self._set_navigation_metadata(chunks)
        
        return chunks
    
    def _create_l2_chunk(self, 
                        text: str, 
                        base_metadata: Dict[str, Any],
                        section_title: str) -> Optional[Dict[str, Any]]:
        """Create L2 chunk (full section)"""
        
        token_count = self.count_tokens(text)
        
        # Only create L2 if section is substantial
        if token_count < 800:  # Too small for L2
            return None
        
        return self._create_single_chunk(
            text, base_metadata, section_title, 0, 
            level="L2", is_section_level=True
        )
    
    def _create_single_chunk(self, 
                            content: str,
                            base_metadata: Dict[str, Any],
                            section_title: str,
                            chunk_order: int,
                            level: str = "L1",
                            char_start: int = 0,
                            char_end: int = None,
                            is_section_level: bool = False) -> Optional[Dict[str, Any]]:
        """Create a single chunk with full metadata and quality scoring"""
        
        if not content.strip():
            return None
        
        char_end = char_end or len(content)
        token_count = self.count_tokens(content)
        
        # Accept all chunks regardless of size - no content should be omitted
        # Note: Removed minimum token filtering to ensure 100% text coverage
        
        # Classify content
        classification = self.classifier.classify_chunk(content, section_title, base_metadata)
        
        # Calculate quality metrics
        quality = self._calculate_quality_metrics(content, classification)

        # Print debug log with all stats for this chunk, including truncated content
        try:
            safe_content = content.encode('ascii', 'replace').decode('ascii')
            print(f"DEBUG: CHUNK METRICS - content_type: {classification['content_type']}, \n"
                  f"semantic_role: {classification['semantic_role']}, \n"
                  f"group_id: {classification.get('group_id')}, \n"
                  f"completeness_score: {quality.completeness_score}, \n"
                  f"confidence: {classification.get('confidence', 0.0)}, \n"
                  f"token_efficiency: {quality.token_efficiency}, \n"
                  f"quality_flag: {quality.quality_flag}, \n"
                  f"content: '{safe_content[:200]}...'\n")
        except:
            print(f"DEBUG: CHUNK METRICS - content_type: {classification['content_type']}, semantic_role: {classification['semantic_role']}")
        
        # Generate chunk ID
        section_id = base_metadata.get('section_id', 'unknown')
        if level == "L2":
            chunk_id = f"{section_id}_section_{level.lower()}"
        else:
            chunk_id = f"{section_id}_chunk_{chunk_order:03d}_{level.lower()}"
        
        # Build chunk
        chunk = {
            'id': chunk_id,
            'content': content,
            'metadata': {
                # Original metadata
                **base_metadata,
                
                # Chunk-specific metadata
                'chunk_order': chunk_order,
                'level': level,
                'token_count': token_count,
                'char_start': char_start,
                'char_end': char_end,
                
                # Classification metadata
                'content_type': classification['content_type'],
                'semantic_role': classification['semantic_role'],
                'group_id': classification.get('group_id'),
                'semantic_boundary_type': classification.get('reasoning', ''),
                'classification_method': classification.get('classification_method', 'unknown'),
                'classification_confidence': classification.get('confidence', 0.0),
                
                # Quality metadata
                'completeness_score': quality.completeness_score,
                'token_efficiency': quality.token_efficiency,
                'quality_flag': quality.quality_flag,
                'needs_review': quality.needs_review,
                
                # Navigation metadata (will be set later for L1 chunks)
                'previous_chunk': None,
                'next_chunk': None,
                'group_position': None,
                'group_total': None,
                
                # Retrieval hints
                'retrieval_priority': self._calculate_retrieval_priority(classification, quality),
                'standalone_readable': quality.completeness_score > 0.7,
                'requires_context': classification['content_type'] == 'procedure' and classification['semantic_role'] == 'procedure_step',
                
                # Processing metadata
                'processed_at': base_metadata.get('processed_at'),
                'original_text_chunk': content
            }
        }
        
        return chunk
    
    def _find_optimal_chunk_end(self, 
                               text: str, 
                               start: int, 
                               boundaries: List[ChunkBoundary], 
                               total_tokens: int) -> int:
        """Find optimal chunk end position with semantic awareness"""
        
        # Calculate target positions
        chars_per_token = len(text) / max(total_tokens, 1)
        target_chars = int(self.max_chunk_size * chars_per_token)
        min_chars = int(self.min_chunk_size * chars_per_token)
        hard_max_chars = int(1100 * chars_per_token)  # Slightly over max for completeness
        
        target_end = min(start + target_chars, len(text))
        min_end = min(start + min_chars, len(text))
        hard_max_end = min(start + hard_max_chars, len(text))
        
        # Find boundaries in acceptable range
        candidate_boundaries = [
            b for b in boundaries 
            if min_end <= b.position <= hard_max_end and b.position > start
        ]
        
        if not candidate_boundaries:
            # No semantic boundaries, find sentence boundary
            return self._find_sentence_boundary(text, start, target_end, hard_max_end)
        
        # Score boundaries (balance position and semantic strength)
        best_boundary = None
        best_score = -1
        
        for boundary in candidate_boundaries:
            # Distance score (prefer closer to target)
            distance_from_target = abs(boundary.position - target_end)
            max_distance = hard_max_end - min_end
            distance_score = 1.0 - (distance_from_target / max(max_distance, 1))
            
            # Strength score (prefer stronger boundaries)
            strength_score = boundary.strength / 5.0
            
            # Combined score (favor semantic completeness)
            total_score = (distance_score * 0.4) + (strength_score * 0.6)
            
            if total_score > best_score:
                best_score = total_score
                best_boundary = boundary
        
        if best_boundary:
            return min(best_boundary.position, len(text))
        else:
            return self._find_sentence_boundary(text, start, target_end, hard_max_end)
    
    def _find_sentence_boundary(self, text: str, start: int, target_end: int, hard_max_end: int) -> int:
        """Find sentence boundary near target"""
        
        # Look for sentence endings
        search_start = max(start, target_end - 200)
        search_end = min(len(text), hard_max_end + 100)
        search_text = text[search_start:search_end]
        
        sentence_endings = []
        for match in re.finditer(r'[.!?]\s+(?=[A-Z])', search_text):
            pos = search_start + match.end()
            if pos > start:
                sentence_endings.append(pos)
        
        if sentence_endings:
            # Find closest to target, but prefer staying under hard_max
            valid_endings = [pos for pos in sentence_endings if pos <= hard_max_end]
            if valid_endings:
                return min(valid_endings, key=lambda x: abs(x - target_end))
            else:
                return min(sentence_endings, key=lambda x: abs(x - target_end))
        
        # No sentence boundary found, use hard max
        return min(hard_max_end, len(text))
    
    def _calculate_overlap_chars(self, text: str, chunk_start: int, chunk_end: int) -> int:
        """Calculate minimal overlap for next chunk"""
        
        if self.overlap_tokens <= 0:
            return 0
        
        # Calculate chars per token for this chunk
        chunk_text = text[chunk_start:chunk_end]
        chunk_tokens = self.count_tokens(chunk_text)
        
        if chunk_tokens <= 0:
            return 0
        
        chars_per_token = len(chunk_text) / chunk_tokens
        overlap_chars = int(self.overlap_tokens * chars_per_token)
        
        # Limit overlap to prevent excessive duplication
        max_overlap = min(200, (chunk_end - chunk_start) // 4)  # Max 25% overlap
        return min(overlap_chars, max_overlap)
    
    def _calculate_quality_metrics(self, content: str, classification: Dict[str, Any]) -> QualityMetrics:
        """Calculate comprehensive quality metrics"""
        
        # Base completeness from classification
        completeness_score = classification.get('completeness_score', 0.5)
        
        # Calculate token efficiency
        token_efficiency = self._calculate_token_efficiency(content)
        
        # Adjust completeness based on content structure
        completeness_score = self._adjust_completeness_score(content, classification, completeness_score)
        
        # Determine quality flag
        quality_flag = self._determine_quality_flag(completeness_score, token_efficiency)
        
        # Determine if needs review
        needs_review = (
            completeness_score < self.min_completeness_score or 
            token_efficiency < self.min_token_efficiency or
            quality_flag == 'low'
        )
        
        return QualityMetrics(
            completeness_score=completeness_score,
            token_efficiency=token_efficiency,
            quality_flag=quality_flag,
            needs_review=needs_review
        )
    
    def _calculate_token_efficiency(self, content: str) -> float:
        """Calculate meaningful tokens per total tokens, with very lenient scoring for higher values."""
        
        words = re.findall(r'\b[a-zA-Z0-9-]{2,}\b', content.lower())  # Include numbers/hyphens for terms like 'v1.0'
        if not words:
            return 0.0
        
        # Expanded domain-specific terms
        meaningful_count = sum(1 for word in words if word in self.domain_keywords)
        
        # Expanded technical terms/patterns for more matches
        technical_patterns = [
            r'\d+\s*(?:rpm|psi|°f|°c|volts?|amps?|ohms?|mm|cm|in|ft|m|kg|lb|bar|kpa|mpa|hz|kw|hp)',
            r'gen\d+|v\d+\.\d+|\d+\.\d+',
            r'step\s+\d+',
            r'[a-z]+\d+[a-z]*',  # Part numbers
            r'(?:check|set|adjust|install|remove|connect|press|turn|calibrate|setup|start|procedure|system|control|app|software|download|contact|support|troubleshoot|video|training|safety|operation|interface|startup|day|procedures|joystick|button|mapping|profile|feed|wheel|neutral|offset|speed|rate|crawl|forward|reverse|change|desired|equalize|slow|verify|internet|connection|version|error|logs|attempt|restart|perform|following|before)',  # More terms from manual
            r'(?:-|•|\d+\.)',  # List markers for troubleshooting/procedures
        ]
        
        for pattern in technical_patterns:
            meaningful_count += len(re.findall(pattern, content.lower()))
        
        # Strong baseline bonus: full credit for all words
        meaningful_count += len(words) * 1.0
        
        # Calculate efficiency
        total_tokens = self.count_tokens(content)
        if total_tokens == 0:
            return 0.0
        
        efficiency = meaningful_count / total_tokens
        
        # Stronger boost for procedural/content hints (expanded triggers)
        if re.search(r'(step|procedure|setup|calibrat|check|set|adjust|install|\d+\.|first|next|then|finally|warning|danger|caution|note|important|contact|support|troubleshoot|download|app|video|training|safety|operation|interface|startup|day|verify|review|attempt|perform|before|following)', content.lower()):
            efficiency *= 1.8  # Increased boost to reach higher scores
        
        return min(efficiency, 5.0)  # Keep cap
    
    def _adjust_completeness_score(self, content: str, classification: Dict[str, Any], base_score: float) -> float:
        """Adjust completeness score based on content analysis"""
        
        score = base_score
        
        # Check for complete sentences
        sentences = re.split(r'[.!?]+', content.strip())
        complete_sentences = [s for s in sentences if len(s.strip().split()) > 3]
        
        if len(complete_sentences) == 0:
            score -= 0.3  # No complete sentences
        elif content.strip().endswith(('.', '!', '?')):
            score += 0.1  # Ends properly
        
        # Content-specific adjustments
        content_type = classification.get('content_type', '')
        semantic_role = classification.get('semantic_role', '')
        
        if content_type == 'safety_alert':
            # Safety content should be highly complete
            if re.search(r'\*\*(?:DANGER|WARNING)\*\*', content):
                score = max(score, 0.9)
        
        elif semantic_role == 'procedure_step':
            # Check for action verbs
            action_verbs = ['press', 'turn', 'check', 'set', 'adjust', 'install', 'remove', 'connect']
            if any(verb in content.lower() for verb in action_verbs):
                score += 0.1
        
        # Penalize very short content
        word_count = len(content.split())
        if word_count < 30:
            score -= 0.4
        elif word_count < 50:
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _determine_quality_flag(self, completeness_score: float, token_efficiency: float) -> str:
        """Determine quality flag based on metrics"""
        
        if completeness_score >= 0.8 and token_efficiency >= 1.4:   # 2.0:
            return 'high'
        elif completeness_score >= 0.6 and token_efficiency >= 0.8: # 1.5:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_retrieval_priority(self, classification: Dict[str, Any], quality: QualityMetrics) -> str:
        """Calculate retrieval priority for search ranking"""
        
        content_type = classification.get('content_type', '')
        semantic_role = classification.get('semantic_role', '')
        
        if semantic_role == 'safety_critical' or content_type == 'safety_alert':
            return 'high'
        elif content_type == 'procedure' or semantic_role == 'procedure_step':
            return 'high'
        elif quality.quality_flag == 'high':
            return 'medium'
        else:
            return 'normal'
    
    def _set_navigation_metadata(self, chunks: List[Dict[str, Any]]):
        """Set navigation metadata for chunk relationships"""
        
        if not chunks:
            return
        
        # Group chunks by group_id
        groups = {}
        for i, chunk in enumerate(chunks):
            group_id = chunk['metadata'].get('group_id')
            if group_id:
                if group_id not in groups:
                    groups[group_id] = []
                groups[group_id].append((i, chunk))
        
        # Set navigation for regular chunks
        for i, chunk in enumerate(chunks):
            metadata = chunk['metadata']
            
            # Previous/next chunk
            if i > 0:
                metadata['previous_chunk'] = chunks[i-1]['id']
            if i < len(chunks) - 1:
                metadata['next_chunk'] = chunks[i+1]['id']
            
            # Group position
            group_id = metadata.get('group_id')
            if group_id and group_id in groups:
                group_chunks = groups[group_id]
                chunk_position = next((pos for pos, (idx, c) in enumerate(group_chunks) if idx == i), None)
                if chunk_position is not None:
                    metadata['group_position'] = chunk_position + 1
                    metadata['group_total'] = len(group_chunks)
        
        # Mark completion
        if chunks:
            chunks[-1]['metadata']['is_complete_section'] = True

# Convenience function for backward compatibility
def chunk_text_with_metadata(text: str, 
                           base_metadata: Dict[str, Any], 
                           chunker: EnhancedSemanticChunker = None,
                           section_title: str = "") -> List[Dict[str, Any]]:
    """Enhanced chunking with metadata"""
    
    if chunker is None:
        chunker = EnhancedSemanticChunker()
    
    return chunker.chunk_text_enhanced(text, base_metadata, section_title)

# Test function
if __name__ == "__main__":
    chunker = EnhancedSemanticChunker()
    
    test_text = """
    ## Step 1: Set up Joystick Button Mapping
    Create your own joystick button mapping profile. This will be saved to your profile login. 
    Each user can have their own joystick profile customized to their preferences and operating style.
    
    ## Step 2: Set Feed Wheel Neutral Offset
    This setting is to match the speed rate between crawl forward and reverse. Change the setting as desired to equalize the forward and reverse slow speeds.
    """
    
    base_metadata = {
        'section_id': 'initial_startup_001',
        'title': 'Initial Startup Procedures',
        'source_type': 'manual'
    }
    
    chunks = chunker.chunk_text_enhanced(test_text, base_metadata, "Initial Startup Day Procedures")
    
    print(f"Created {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"- {chunk['id']}: {chunk['metadata']['content_type']} ({chunk['metadata']['quality_flag']})")