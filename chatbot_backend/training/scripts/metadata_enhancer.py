# training/scripts/metadata_enhancer.py
import os
import sys
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
from training.scripts.content_extractor import DomainInfo, ExtractedContent

@dataclass
class CustomerSupportMetadata:
    """Enhanced metadata for customer support scenarios"""
    user_questions: List[str]
    difficulty_level: str  # beginner, intermediate, advanced
    estimated_time: str
    prerequisites: List[str]
    user_synonyms: Dict[str, List[str]]
    urgency_level: str  # low, medium, high
    support_category: str  # setup, troubleshooting, maintenance, operation
    success_indicators: List[str]
    common_errors: List[str]
    escalation_path: List[str]

class UniversalMetadataEnhancer:
    """Universal metadata enhancement system for customer support optimization"""

    def __init__(self, model: GenerativeModel = None):
        self.model = model

        # Universal question templates that work for any domain
        self.universal_question_templates = {
            'status_check': [
                "What does {indicator} mean?",
                "Why is {indicator} {state}?",
                "Is {state} {indicator} normal?",
                "What should I do if {indicator} is {state}?",
                "How do I interpret {indicator}?"
            ],
            'troubleshooting': [
                "What do I do if {problem}?",
                "How do I fix {issue}?",
                "{symptom} - what's wrong?",
                "Why is {problem} happening?",
                "How can I resolve {issue}?"
            ],
            'setup': [
                "How do I set up {component}?",
                "What's the first step to {action}?",
                "How long does {procedure} take?",
                "What do I need to {action}?",
                "Can you walk me through {procedure}?"
            ],
            'operation': [
                "How do I {action}?",
                "Where is the {component}?",
                "Can I {capability}?",
                "What happens when I {action}?",
                "How often should I {action}?"
            ],
            'specification': [
                "What is the {spec_name}?",
                "Does this support {feature}?",
                "What are the requirements for {spec_name}?",
                "Is {value} normal for {spec_name}?",
                "How does {spec_name} compare to other models?"
            ]
        }

        # Universal difficulty indicators
        self.difficulty_indicators = {
            'beginner': [
                'basic', 'simple', 'easy', 'first', 'initial', 'getting started',
                'overview', 'introduction', 'quick', 'press', 'turn on'
            ],
            'intermediate': [
                'configure', 'setup', 'install', 'adjust', 'modify', 'change',
                'advanced settings', 'customize', 'optimize'
            ],
            'advanced': [
                'troubleshoot', 'diagnose', 'repair', 'maintenance', 'technical',
                'complex', 'detailed', 'expert', 'administrator', 'diagnostic'
            ]
        }

        # Universal urgency indicators
        self.urgency_indicators = {
            'high': [
                'emergency', 'urgent', 'critical', 'danger', 'safety', 'fire',
                'explosion', 'injury', 'damage', 'immediate', 'now', 'stop'
            ],
            'medium': [
                'important', 'issue', 'problem', 'error', 'fault', 'fix',
                'resolve', 'soon', 'quickly', 'broken', 'not working'
            ],
            'low': [
                'optimize', 'improve', 'enhance', 'convenience', 'preference',
                'optional', 'recommended', 'suggestion', 'tip', 'hint'
            ]
        }

    def enhance_extracted_content(self, extracted_content: List[ExtractedContent],
                                  domain_info: DomainInfo,
                                  section_title: str = "") -> List[Dict[str, Any]]:
        """Enhance extracted content with customer support metadata"""

        enhanced_chunks = []

        for content in extracted_content:
            # Generate customer support metadata
            support_metadata = self.generate_support_metadata(
                content, domain_info, section_title
            )

            # Create enhanced chunk
            enhanced_chunk = {
                'id': f"{content.content_type}_{len(enhanced_chunks):03d}",
                'content': content.text,
                'metadata': {
                    # Original metadata
                    **content.metadata,

                    # Core content info
                    'content_type': content.content_type,
                    'source_section': content.source_section,
                    'confidence': content.confidence,
                    'level': self._determine_chunk_level(content.content_type),

                    # Customer support metadata
                    'user_questions': support_metadata.user_questions,
                    'difficulty_level': support_metadata.difficulty_level,
                    'estimated_time': support_metadata.estimated_time,
                    'prerequisites': support_metadata.prerequisites,
                    'user_synonyms': support_metadata.user_synonyms,
                    'urgency_level': support_metadata.urgency_level,
                    'support_category': support_metadata.support_category,
                    'success_indicators': support_metadata.success_indicators,
                    'common_errors': support_metadata.common_errors,
                    'escalation_path': support_metadata.escalation_path,

                    # Domain-specific info
                    'domain_category': domain_info.category,
                    'product_type': domain_info.product_type,

                    # Quality metrics
                    'quality_flag': 'high',  # Extracted content is high quality
                    'needs_review': False,
                    'standalone_readable': True,
                    'requires_context': content.content_type == 'procedure_step'
                }
            }

            enhanced_chunks.append(enhanced_chunk)

        return enhanced_chunks

    def generate_support_metadata(self, content: ExtractedContent,
                                  domain_info: DomainInfo,
                                  section_title: str) -> CustomerSupportMetadata:
        """Generate comprehensive customer support metadata"""

        # Generate user questions
        user_questions = self._generate_user_questions(content, domain_info)

        # Assess difficulty level
        difficulty_level = self._assess_difficulty_level(content)

        # Estimate time
        estimated_time = self._estimate_time(content)

        # Identify prerequisites
        prerequisites = self._identify_prerequisites(content, domain_info)

        # Generate user synonyms
        user_synonyms = self._generate_user_synonyms(content, domain_info)

        # Assess urgency
        urgency_level = self._assess_urgency_level(content)

        # Categorize for support
        support_category = self._categorize_for_support(content)

        # Identify success indicators
        success_indicators = self._identify_success_indicators(content)

        # Predict common errors
        common_errors = self._predict_common_errors(content, domain_info)

        # Create escalation path
        escalation_path = self._create_escalation_path(content)

        return CustomerSupportMetadata(
            user_questions=user_questions,
            difficulty_level=difficulty_level,
            estimated_time=estimated_time,
            prerequisites=prerequisites,
            user_synonyms=user_synonyms,
            urgency_level=urgency_level,
            support_category=support_category,
            success_indicators=success_indicators,
            common_errors=common_errors,
            escalation_path=escalation_path
        )

    def _generate_user_questions(self, content: ExtractedContent, domain_info: DomainInfo) -> List[str]:
        """Generate realistic user questions for the content"""

        questions = []
        content_type = content.content_type
        text = content.text.lower()

        # Use LLM if available
        if self.model:
            questions.extend(self._llm_generate_questions(content, domain_info))

        # Template-based generation as backup/supplement
        templates = self.universal_question_templates.get(content_type.split('_')[0], [])

        if content_type == 'status_indicator':
            indicator = content.metadata.get('indicator_name', 'indicator')
            state = content.metadata.get('indicator_state', 'state')

            for template in self.universal_question_templates['status_check']:
                question = template.format(indicator=indicator, state=state)
                questions.append(question)

        elif content_type in ['troubleshooting', 'problem_description']:
            problem = content.metadata.get('problem_condition', 'issue')

            for template in self.universal_question_templates['troubleshooting']:
                question = template.format(problem=problem, issue=problem, symptom=problem)
                questions.append(question)

        elif 'procedure' in content_type:
            # Extract action from procedure
            action_match = re.search(r'(connect|setup|install|configure|press|turn|check)', text)
            action = action_match.group(1) if action_match else 'do this'

            for template in self.universal_question_templates['setup']:
                question = template.format(action=action, procedure='this', component='device')
                questions.append(question)

        elif content_type == 'specification':
            spec_name = content.metadata.get('spec_category', 'feature')

            for template in self.universal_question_templates['specification']:
                question = template.format(spec_name=spec_name, feature=spec_name, value='this')
                questions.append(question)

        # Remove duplicates and limit
        questions = list(dict.fromkeys(questions))[:5]

        return questions

    def _llm_generate_questions(self, content: ExtractedContent, domain_info: DomainInfo) -> List[str]:
        """Use LLM to generate realistic customer questions"""

        try:
            prompt = f"""
Generate 3-5 realistic customer service questions that users would ask about this content.

Content Type: {content.content_type}
Domain: {domain_info.category} - {domain_info.product_type}
Content: {content.text}

Consider:
- How customers actually talk (not technical language)
- Common confusion points
- Different skill levels
- Frustration and urgency

Return as JSON array: ["question1", "question2", "question3"]
"""

            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 400
                }
            )

            if response.candidates and response.candidates[0].content.parts:
                response_text = response.candidates[0].content.parts[0].text.strip()

                # Extract JSON array
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    questions = json.loads(json_match.group())
                    return questions[:5]  # Limit to 5

        except Exception as e:
            print(f"WARNING: LLM question generation failed: {e}")

        return []

    def _assess_difficulty_level(self, content: ExtractedContent) -> str:
        """Assess the difficulty level of the content"""

        text = content.text.lower()

        # Count indicators for each level
        scores = {'beginner': 0, 'intermediate': 0, 'advanced': 0}

        for level, indicators in self.difficulty_indicators.items():
            for indicator in indicators:
                if indicator in text:
                    scores[level] += 1

        # Special rules based on content type
        if content.content_type == 'status_indicator':
            scores['beginner'] += 2  # Status indicators are usually beginner-friendly

        elif content.content_type == 'procedure_step':
            step_num = content.metadata.get('step_number', 1)
            if step_num <= 3:
                scores['beginner'] += 1
            else:
                scores['intermediate'] += 1

        elif 'troubleshooting' in content.content_type:
            scores['intermediate'] += 2  # Troubleshooting is usually intermediate

        elif content.content_type == 'specification':
            scores['beginner'] += 1  # Basic specs are beginner-friendly

        # Determine level
        max_score = max(scores.values())
        if max_score == 0:
            return 'beginner'  # Default

        return max(scores, key=scores.get)

    def _estimate_time(self, content: ExtractedContent) -> str:
        """Estimate time to complete/understand the content"""

        content_type = content.content_type
        text = content.text

        if content_type == 'status_indicator':
            return "30 seconds"
        elif content_type == 'specification':
            return "30 seconds"
        elif content_type == 'procedure_step':
            # Estimate based on step complexity
            if any(word in text.lower() for word in ['wait', 'minute', 'seconds']):
                return "2-3 minutes"
            elif any(word in text.lower() for word in ['connect', 'install', 'setup']):
                return "1-2 minutes"
            else:
                return "1 minute"
        elif content_type == 'procedure_summary':
            total_steps = content.metadata.get('total_steps', 1)
            return f"{total_steps * 2} minutes"
        elif 'troubleshooting' in content_type:
            return "5-10 minutes"
        else:
            return "1-2 minutes"

    def _identify_prerequisites(self, content: ExtractedContent, domain_info: DomainInfo) -> List[str]:
        """Identify prerequisites for the content"""

        prerequisites = []
        text = content.text.lower()
        content_type = content.content_type

        # Universal prerequisites based on content
        if 'power' in text or 'turn on' in text:
            prerequisites.append("Device must be powered on")

        if 'connect' in text and domain_info.category == 'electronics':
            prerequisites.append("Required cables must be available")

        if content_type == 'procedure_step':
            step_num = content.metadata.get('step_number', 1)
            if step_num > 1:
                prerequisites.append(f"Complete steps 1-{step_num-1}")

        if 'troubleshooting' in content_type:
            prerequisites.append("Read basic operation guide first")

        if any(word in text for word in ['configure', 'settings', 'setup']):
            prerequisites.append("Initial setup must be completed")

        return prerequisites[:3]  # Limit to top 3

    def _generate_user_synonyms(self, content: ExtractedContent, domain_info: DomainInfo) -> Dict[str, List[str]]:
        """Generate mapping of technical terms to user-friendly synonyms"""

        synonyms = {}
        text = content.text

        # Universal technical term mappings
        universal_mappings = {
            'LED': ['light', 'indicator', 'lamp'],
            'router': ['main unit', 'base station', 'hub'],
            'satellite': ['extender', 'repeater', 'secondary unit'],
            'ethernet': ['cable', 'wired connection', 'cord'],
            'WiFi': ['wireless', 'internet', 'network'],
            'SSID': ['network name', 'WiFi name'],
            'firmware': ['software', 'system update'],
            'sync': ['connect', 'pair', 'link'],
            'reset': ['restart', 'reboot'],
            'configure': ['setup', 'set up', 'adjust']
        }

        # Domain-specific mappings
        if domain_info.category == 'automotive':
            auto_mappings = {
                'dashboard': ['dash', 'instrument panel'],
                'ignition': ['key', 'start'],
                'transmission': ['gear box'],
                'brake': ['brakes', 'stopping system']
            }
            universal_mappings.update(auto_mappings)

        elif domain_info.category == 'appliance':
            appliance_mappings = {
                'cycle': ['program', 'setting'],
                'filter': ['screen', 'strainer'],
                'temperature': ['temp', 'heat setting']
            }
            universal_mappings.update(appliance_mappings)

        # Find technical terms in content and map them
        for tech_term, user_terms in universal_mappings.items():
            if tech_term.lower() in text.lower():
                synonyms[tech_term] = user_terms

        # Add domain-specific user terms
        if domain_info.user_terms:
            synonyms.update(domain_info.user_terms)

        return synonyms

    def _assess_urgency_level(self, content: ExtractedContent) -> str:
        """Assess the urgency level of the content"""

        text = content.text.lower()

        # Check for urgency indicators
        for level, indicators in self.urgency_indicators.items():
            for indicator in indicators:
                if indicator in text:
                    return level

        # Content type based urgency
        if content.content_type == 'troubleshooting':
            return 'medium'
        elif 'safety' in content.content_type or 'warning' in content.content_type:
            return 'high'
        elif content.content_type == 'specification':
            return 'low'
        else:
            return 'low'

    def _categorize_for_support(self, content: ExtractedContent) -> str:
        """Categorize content for customer support workflow"""

        content_type = content.content_type
        text = content.text.lower()

        if any(word in text for word in ['setup', 'install', 'initial', 'first time', 'getting started']):
            return 'setup'
        elif any(word in text for word in ['troubleshoot', 'problem', 'error', 'fix', 'issue', 'fault']):
            return 'troubleshooting'
        elif any(word in text for word in ['maintain', 'clean', 'care', 'service', 'regular']):
            return 'maintenance'
        elif content_type == 'status_indicator':
            return 'operation'
        elif content_type == 'specification':
            return 'information'
        else:
            return 'operation'

    def _identify_success_indicators(self, content: ExtractedContent) -> List[str]:
        """Identify how users know they've succeeded"""

        indicators = []
        text = content.text.lower()
        content_type = content.content_type

        if content_type == 'status_indicator':
            state = content.metadata.get('indicator_state', '')
            indicator_name = content.metadata.get('indicator_name', 'indicator')
            if state and indicator_name:
                indicators.append(f"{indicator_name} shows {state}")

        # Look for success patterns in text
        success_patterns = [
            r'(?:when|if).*(?:successful|complete|finished|ready|working)',
            r'(?:should see|will show|displays?).*',
            r'(?:indicates?|means).*(?:working|ready|connected|successful)'
        ]

        for pattern in success_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                indicators.append(match.group().strip())

        # Generic success indicators based on content type
        if 'procedure' in content_type:
            indicators.append("Operation completes without errors")
        elif 'troubleshooting' in content_type:
            indicators.append("Problem is resolved")

        return indicators[:3]  # Limit to top 3

    def _predict_common_errors(self, content: ExtractedContent, domain_info: DomainInfo) -> List[str]:
        """Predict common errors users might make"""

        errors = []
        text = content.text.lower()
        content_type = content.content_type

        # Universal common errors
        if 'power' in text:
            errors.append("User forgets to plug in power cable")

        if 'button' in text:
            errors.append("User presses wrong button or doesn't hold long enough")

        if 'connect' in text:
            errors.append("User connects cables to wrong ports")

        if content_type == 'procedure_step':
            errors.append("User skips this step or does it out of order")

        if 'wait' in text:
            errors.append("User doesn't wait long enough for process to complete")

        # Domain-specific errors
        if domain_info.category == 'electronics':
            errors.append("User doesn't check LED indicators")

        return errors[:3]  # Limit to top 3

    def _create_escalation_path(self, content: ExtractedContent) -> List[str]:
        """Create escalation path for customer support"""

        path = []
        content_type = content.content_type

        if content_type == 'status_indicator':
            path = [
                "Check indicator meaning",
                "Follow basic troubleshooting steps",
                "Try device reset",
                "Contact technical support"
            ]
        elif 'procedure' in content_type:
            path = [
                "Review step-by-step instructions",
                "Check prerequisites are met",
                "Try alternative method",
                "Contact technical support"
            ]
        elif 'troubleshooting' in content_type:
            path = [
                "Follow troubleshooting steps",
                "Try factory reset",
                "Check warranty status",
                "Contact technical support"
            ]
        else:
            path = [
                "Review relevant documentation",
                "Try basic troubleshooting",
                "Contact technical support"
            ]

        return path

    def _determine_chunk_level(self, content_type: str) -> str:
        """Determine appropriate chunk level based on content type"""

        if content_type in ['status_indicator', 'specification']:
            return 'L0'  # Quick facts
        elif content_type in ['procedure_summary', 'troubleshooting']:
            return 'L2'  # Summaries
        elif content_type in ['procedure_step']:
            return 'QA'  # Question-answer style
        else:
            return 'L1'  # Standard chunks

# Test function
if __name__ == "__main__":
    from training.scripts.content_extractor import UniversalContentExtractor, DomainInfo

    # Create test content
    test_content = """Router LED (front): Solid blue = good connection to satellite"""

    extractor = UniversalContentExtractor()
    enhancer = UniversalMetadataEnhancer()

    domain_info, extracted = extractor.extract_all_content(test_content, "LED Status")
    enhanced = enhancer.enhance_extracted_content(extracted, domain_info, "LED Status")

    print(f"Enhanced {len(enhanced)} chunks:")
    for chunk in enhanced:
        print(f"\nChunk: {chunk['content']}")
        print(f"Questions: {chunk['metadata']['user_questions'][:2]}")
        print(f"Difficulty: {chunk['metadata']['difficulty_level']}")
        print(f"Category: {chunk['metadata']['support_category']}")