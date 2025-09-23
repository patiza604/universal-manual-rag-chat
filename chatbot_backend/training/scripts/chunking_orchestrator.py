# training/scripts/chunking_orchestrator.py
import os
import sys
import yaml
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import vertexai
from vertexai.generative_models import GenerativeModel
from app.config import *
from training.scripts.content_extractor import UniversalContentExtractor, DomainInfo, ExtractedContent
from training.scripts.metadata_enhancer import UniversalMetadataEnhancer

@dataclass
class ChunkingConfig:
    """Configuration for chunking process"""
    default_strategy: Dict[str, Any]
    domain_configs: Dict[str, Dict[str, Any]]
    question_generation: Dict[str, Any]
    metadata_enhancement: Dict[str, Any]
    chunking_levels: Dict[str, Any]
    quality_control: Dict[str, Any]
    output_format: Dict[str, Any]

class UniversalChunkingOrchestrator:
    """Universal orchestrator that coordinates content extraction, enhancement, and chunking"""

    def __init__(self,
                 config_path: str = None,
                 model: GenerativeModel = None):

        self.model = model

        # Load configuration
        if config_path is None:
            config_path = project_root / "training" / "config" / "manual_config.yaml"

        self.config = self._load_config(config_path)

        # Initialize components
        self.content_extractor = UniversalContentExtractor(model=self.model)
        self.metadata_enhancer = UniversalMetadataEnhancer(model=self.model)

        # Processing statistics
        self.stats = {
            'sections_processed': 0,
            'l0_chunks': 0,  # Quick facts
            'l1_chunks': 0,  # Standard sections (preserved)
            'l2_chunks': 0,  # Procedure summaries
            'qa_chunks': 0,  # Question-answer pairs
            'l3_chunks': 0,  # Document summary (preserved)
            'l4_chunks': 0,  # Cross-references
            'total_extracted_content': 0,
            'domain_detected': '',
            'questions_generated': 0,
            'errors': []
        }

    def _load_config(self, config_path: str) -> ChunkingConfig:
        """Load configuration from YAML file"""

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            return ChunkingConfig(
                default_strategy=config_data.get('default_strategy', {}),
                domain_configs=config_data.get('domain_configs', {}),
                question_generation=config_data.get('question_generation', {}),
                metadata_enhancement=config_data.get('metadata_enhancement', {}),
                chunking_levels=config_data.get('chunking_levels', {}),
                quality_control=config_data.get('quality_control', {}),
                output_format=config_data.get('output_format', {})
            )

        except Exception as e:
            print(f"WARNING: Failed to load config from {config_path}: {e}")
            # Return default config
            return self._get_default_config()

    def _get_default_config(self) -> ChunkingConfig:
        """Get default configuration if loading fails"""

        return ChunkingConfig(
            default_strategy={
                'quick_facts_max_chars': 150,
                'procedure_summary_max_chars': 400,
                'detailed_section_max_chars': 2000,
                'qa_chunk_max_chars': 300,
                'extraction_priorities': {
                    'status_indicators': 'high',
                    'procedures': 'high',
                    'troubleshooting': 'high',
                    'specifications': 'medium'
                }
            },
            domain_configs={},
            question_generation={'max_questions_per_chunk': 5},
            metadata_enhancement={},
            chunking_levels={},
            quality_control={'min_confidence_threshold': 0.6},
            output_format={'preserve_original_chunks': True}
        )

    def process_section(self,
                       section_content: str,
                       section_metadata: Dict[str, Any],
                       section_title: str = "") -> List[Dict[str, Any]]:
        """Process a single section and generate multi-level chunks"""

        print(f"  -> Analyzing section: {section_title}")

        all_chunks = []

        try:
            # Step 1: Extract domain info and content patterns
            domain_info, extracted_content = self.content_extractor.extract_all_content(
                section_content, section_title
            )

            # Update stats
            self.stats['domain_detected'] = f"{domain_info.category} - {domain_info.product_type}"
            self.stats['total_extracted_content'] += len(extracted_content)

            print(f"    >> Domain: {domain_info.category}, Extracted: {len(extracted_content)} items")

            # Step 2: Create L1 chunk (preserve original section-based chunk)
            if self.config.output_format.get('preserve_original_chunks', True):
                l1_chunk = self._create_l1_section_chunk(
                    section_content, section_metadata, section_title, domain_info
                )
                all_chunks.append(l1_chunk)
                self.stats['l1_chunks'] += 1

            # Step 3: Generate enhanced chunks from extracted content
            if extracted_content:
                enhanced_chunks = self.metadata_enhancer.enhance_extracted_content(
                    extracted_content, domain_info, section_title
                )

                # Process each enhanced chunk
                for enhanced_chunk in enhanced_chunks:
                    # Apply domain-specific enhancements
                    self._apply_domain_enhancements(enhanced_chunk, domain_info)

                    # Categorize by level
                    level = enhanced_chunk['metadata']['level']
                    if level == 'L0':
                        self.stats['l0_chunks'] += 1
                    elif level == 'L2':
                        self.stats['l2_chunks'] += 1
                    elif level == 'QA':
                        self.stats['qa_chunks'] += 1

                    # Track questions generated
                    questions = enhanced_chunk['metadata'].get('user_questions', [])
                    self.stats['questions_generated'] += len(questions)

                    all_chunks.append(enhanced_chunk)

            # Step 4: Generate cross-reference chunks (L4)
            l4_chunks = self._generate_cross_reference_chunks(
                extracted_content, domain_info, section_title
            )
            all_chunks.extend(l4_chunks)
            self.stats['l4_chunks'] += len(l4_chunks)

            self.stats['sections_processed'] += 1

            print(f"    => Generated {len(all_chunks)} chunks total")

        except Exception as e:
            error_msg = f"Failed to process section '{section_title}': {e}"
            print(f"    ERROR: {error_msg}")
            self.stats['errors'].append(error_msg)

            # Fallback: create basic L1 chunk
            l1_chunk = self._create_l1_section_chunk(
                section_content, section_metadata, section_title, None
            )
            all_chunks.append(l1_chunk)
            self.stats['l1_chunks'] += 1

        return all_chunks

    def _create_l1_section_chunk(self,
                                section_content: str,
                                section_metadata: Dict[str, Any],
                                section_title: str,
                                domain_info: Optional[DomainInfo]) -> Dict[str, Any]:
        """Create L1 section chunk (preserve original chunking approach)"""

        chunk_id = f"{section_metadata.get('section_id', 'section')}_complete_l1"

        # Generate basic user questions for the section
        basic_questions = self._generate_basic_section_questions(section_title, section_content)

        return {
            'id': chunk_id,
            'content': section_content,
            'metadata': {
                # Original metadata
                **section_metadata,

                # Chunk info
                'level': 'L1',
                'content_type': 'section_content',
                'chunk_order': 0,
                'token_count': len(section_content.split()) * 1.3,  # Rough estimate

                # Customer support metadata
                'user_questions': basic_questions,
                'difficulty_level': self._assess_section_difficulty(section_content),
                'estimated_time': self._estimate_section_time(section_content),
                'support_category': self._categorize_section_for_support(section_title, section_content),
                'urgency_level': 'medium',

                # Domain info
                'domain_category': domain_info.category if domain_info else 'unknown',
                'product_type': domain_info.product_type if domain_info else 'unknown',

                # Quality flags
                'quality_flag': 'high',
                'needs_review': False,
                'standalone_readable': True,
                'requires_context': False,

                # Enhanced for customer support
                'user_synonyms': domain_info.user_terms if domain_info else {},
                'prerequisites': [],
                'success_indicators': [],
                'common_errors': [],
                'escalation_path': [
                    "Review section documentation",
                    "Try related troubleshooting steps",
                    "Contact technical support"
                ]
            }
        }

    def _apply_domain_enhancements(self, chunk: Dict[str, Any], domain_info: DomainInfo):
        """Apply domain-specific enhancements to a chunk"""

        domain_category = domain_info.category

        # Get domain-specific config
        domain_config = self.config.domain_configs.get(domain_category, {})

        # Add domain-specific user terms
        common_terms = domain_config.get('common_user_terms', {})
        existing_synonyms = chunk['metadata'].get('user_synonyms', {})
        chunk['metadata']['user_synonyms'] = {**existing_synonyms, **common_terms}

        # Enhance based on domain
        if domain_category == 'electronics':
            self._enhance_electronics_chunk(chunk, domain_info)
        elif domain_category == 'automotive':
            self._enhance_automotive_chunk(chunk, domain_info)
        elif domain_category == 'appliance':
            self._enhance_appliance_chunk(chunk, domain_info)
        elif domain_category == 'software':
            self._enhance_software_chunk(chunk, domain_info)

    def _enhance_electronics_chunk(self, chunk: Dict[str, Any], domain_info: DomainInfo):
        """Add electronics-specific enhancements"""

        content = chunk['content'].lower()

        # Add electronics-specific success indicators
        if 'led' in content or 'light' in content:
            chunk['metadata']['success_indicators'].append("LED shows expected color/pattern")

        if 'connect' in content or 'wifi' in content:
            chunk['metadata']['success_indicators'].append("Device shows connected status")

        # Add common electronics errors
        chunk['metadata']['common_errors'].extend([
            "User doesn't wait for LED indicators to stabilize",
            "Cables connected to wrong ports",
            "Device not fully powered on"
        ])

    def _enhance_automotive_chunk(self, chunk: Dict[str, Any], domain_info: DomainInfo):
        """Add automotive-specific enhancements"""

        content = chunk['content'].lower()

        # Add automotive-specific success indicators
        if 'engine' in content:
            chunk['metadata']['success_indicators'].append("Engine runs smoothly without warning lights")

        if 'brake' in content:
            chunk['metadata']['success_indicators'].append("Brake pedal feels firm and responsive")

        # Add common automotive errors
        chunk['metadata']['common_errors'].extend([
            "User ignores warning lights on dashboard",
            "Procedure attempted with engine running",
            "Safety precautions not followed"
        ])

    def _enhance_appliance_chunk(self, chunk: Dict[str, Any], domain_info: DomainInfo):
        """Add appliance-specific enhancements"""

        content = chunk['content'].lower()

        # Add appliance-specific success indicators
        if 'cycle' in content or 'program' in content:
            chunk['metadata']['success_indicators'].append("Cycle completes without error codes")

        # Add common appliance errors
        chunk['metadata']['common_errors'].extend([
            "User selects wrong cycle for load type",
            "Appliance not properly leveled",
            "Filters not cleaned regularly"
        ])

    def _enhance_software_chunk(self, chunk: Dict[str, Any], domain_info: DomainInfo):
        """Add software-specific enhancements"""

        content = chunk['content'].lower()

        # Add software-specific success indicators
        if 'install' in content:
            chunk['metadata']['success_indicators'].append("Installation completes without error messages")

        if 'login' in content:
            chunk['metadata']['success_indicators'].append("Successfully logged into account")

        # Add common software errors
        chunk['metadata']['common_errors'].extend([
            "User enters incorrect credentials",
            "Browser cache causes display issues",
            "Pop-up blockers prevent functionality"
        ])

    def _generate_cross_reference_chunks(self,
                                       extracted_content: List[ExtractedContent],
                                       domain_info: DomainInfo,
                                       section_title: str) -> List[Dict[str, Any]]:
        """Generate L4 cross-reference chunks that combine related content"""

        l4_chunks = []

        # Group related procedures
        procedures = [c for c in extracted_content if 'procedure' in c.content_type]
        if len(procedures) > 1:
            # Create workflow chunk
            workflow_content = f"Complete {section_title} workflow:\n"
            workflow_content += "\n".join([f"• {proc.text}" for proc in procedures[:3]])

            l4_chunks.append({
                'id': f"{section_title.lower().replace(' ', '_')}_workflow_l4",
                'content': workflow_content,
                'metadata': {
                    'level': 'L4',
                    'content_type': 'workflow_chain',
                    'related_procedures': [proc.metadata for proc in procedures],
                    'user_questions': [
                        f"What's the complete process for {section_title.lower()}?",
                        f"Can you walk me through all steps for {section_title.lower()}?"
                    ],
                    'difficulty_level': 'intermediate',
                    'estimated_time': f"{len(procedures) * 2}-{len(procedures) * 3} minutes",
                    'support_category': 'operation',
                    'quality_flag': 'high'
                }
            })

        # Group troubleshooting content
        troubleshooting = [c for c in extracted_content if 'troubleshooting' in c.content_type]
        if troubleshooting:
            trouble_content = f"{section_title} troubleshooting guide:\n"
            trouble_content += "\n".join([f"• {trouble.text}" for trouble in troubleshooting[:3]])

            l4_chunks.append({
                'id': f"{section_title.lower().replace(' ', '_')}_troubleshooting_l4",
                'content': trouble_content,
                'metadata': {
                    'level': 'L4',
                    'content_type': 'troubleshooting_guide',
                    'related_problems': [trouble.metadata for trouble in troubleshooting],
                    'user_questions': [
                        f"What should I do if {section_title.lower()} isn't working?",
                        f"How do I troubleshoot {section_title.lower()} problems?"
                    ],
                    'difficulty_level': 'intermediate',
                    'estimated_time': "5-15 minutes",
                    'support_category': 'troubleshooting',
                    'urgency_level': 'medium',
                    'quality_flag': 'high'
                }
            })

        return l4_chunks

    def _generate_basic_section_questions(self, section_title: str, content: str) -> List[str]:
        """Generate basic questions for a section"""

        questions = [
            f"How do I {section_title.lower()}?",
            f"What do I need to know about {section_title.lower()}?",
            f"Can you explain {section_title.lower()}?"
        ]

        # Add content-specific questions
        content_lower = content.lower()
        if 'step' in content_lower:
            questions.append(f"What are the steps for {section_title.lower()}?")
        if 'problem' in content_lower or 'error' in content_lower:
            questions.append(f"What problems might occur with {section_title.lower()}?")
        if 'time' in content_lower or 'minute' in content_lower:
            questions.append(f"How long does {section_title.lower()} take?")

        return questions[:5]

    def _assess_section_difficulty(self, content: str) -> str:
        """Assess difficulty level of a section"""

        content_lower = content.lower()

        # Count complexity indicators
        beginner_indicators = ['basic', 'simple', 'easy', 'first', 'quick', 'overview']
        intermediate_indicators = ['configure', 'setup', 'install', 'adjust', 'advanced']
        advanced_indicators = ['troubleshoot', 'diagnose', 'technical', 'complex', 'expert']

        beginner_score = sum(1 for word in beginner_indicators if word in content_lower)
        intermediate_score = sum(1 for word in intermediate_indicators if word in content_lower)
        advanced_score = sum(1 for word in advanced_indicators if word in content_lower)

        # Consider length
        word_count = len(content.split())
        if word_count > 500:
            advanced_score += 1
        elif word_count < 200:
            beginner_score += 1

        # Determine level
        if advanced_score > max(beginner_score, intermediate_score):
            return 'advanced'
        elif intermediate_score > beginner_score:
            return 'intermediate'
        else:
            return 'beginner'

    def _estimate_section_time(self, content: str) -> str:
        """Estimate time to complete section"""

        word_count = len(content.split())

        # Look for time indicators in content
        time_match = re.search(r'(\d+)\s*(?:minute|min|second|sec)', content.lower())
        if time_match:
            return f"{time_match.group(1)} minutes"

        # Estimate based on word count and complexity
        if word_count < 100:
            return "1-2 minutes"
        elif word_count < 300:
            return "3-5 minutes"
        elif word_count < 600:
            return "5-10 minutes"
        else:
            return "10-15 minutes"

    def _categorize_section_for_support(self, section_title: str, content: str) -> str:
        """Categorize section for customer support"""

        title_lower = section_title.lower()
        content_lower = content.lower()

        # Category keywords from config
        categories = self.config.metadata_enhancement.get('support_categories', {})

        scores = {}
        for category, keywords in categories.items():
            score = 0
            for keyword in keywords:
                if keyword in title_lower:
                    score += 2  # Title matches are stronger
                if keyword in content_lower:
                    score += 1
            scores[category] = score

        # Return highest scoring category, or 'operation' as default
        if scores:
            return max(scores, key=scores.get)
        else:
            return 'operation'

    def print_processing_statistics(self):
        """Print comprehensive processing statistics"""

        print("\n" + "="*60)
        print("UNIVERSAL CHUNKING STATISTICS")
        print("="*60)
        print(f"Sections processed: {self.stats['sections_processed']}")
        print(f"Domain detected: {self.stats['domain_detected']}")
        print(f"Content items extracted: {self.stats['total_extracted_content']}")
        print(f"Questions generated: {self.stats['questions_generated']}")
        print()
        print("CHUNK DISTRIBUTION:")
        print(f"  • L0 chunks (quick facts): {self.stats['l0_chunks']}")
        print(f"  • L1 chunks (sections): {self.stats['l1_chunks']}")
        print(f"  • L2 chunks (summaries): {self.stats['l2_chunks']}")
        print(f"  • QA chunks (questions): {self.stats['qa_chunks']}")
        print(f"  • L3 chunks (document): {self.stats['l3_chunks']}")
        print(f"  • L4 chunks (cross-refs): {self.stats['l4_chunks']}")

        total_chunks = (self.stats['l0_chunks'] + self.stats['l1_chunks'] +
                       self.stats['l2_chunks'] + self.stats['qa_chunks'] +
                       self.stats['l3_chunks'] + self.stats['l4_chunks'])
        print(f"  >> TOTAL CHUNKS: {total_chunks}")

        if self.stats['errors']:
            print(f"\nERROR: Processing errors: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:3]:
                print(f"  - {error}")

        print("="*60)

# Test function
if __name__ == "__main__":
    orchestrator = UniversalChunkingOrchestrator()

    # Test with sample section
    test_content = """
    ## Router LED Status

    Router LED (front): Pulsing white = booting or Sync pressed; Solid white = factory reset in progress; Solid magenta = cannot connect to Internet; Off = finished booting/working normally.

    Step 1: Check the LED color and pattern.
    Step 2: Compare with the status meanings above.
    Step 3: Take appropriate action based on the status.

    If the LED shows solid magenta, check your internet connection.
    """

    test_metadata = {
        'title': 'Router LED Status',
        'section_id': 'led_status_001',
        'source_type': 'manual'
    }

    chunks = orchestrator.process_section(test_content, test_metadata, "Router LED Status")

    print(f"Generated {len(chunks)} chunks:")
    for chunk in chunks:
        level = chunk['metadata']['level']
        content_type = chunk['metadata']['content_type']
        questions = len(chunk['metadata'].get('user_questions', []))
        print(f"  [{level}] {content_type} - {questions} questions")

    orchestrator.print_processing_statistics()