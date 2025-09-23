# training/scripts/content_extractor.py
import os
import sys
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import vertexai
from vertexai.generative_models import GenerativeModel
from app.config import *

@dataclass
class ExtractedContent:
    """Container for extracted content with metadata"""
    content_type: str
    text: str
    metadata: Dict[str, Any]
    confidence: float
    source_section: str

@dataclass
class DomainInfo:
    """Information about the manual's domain"""
    category: str  # electronics, automotive, software, appliance, etc.
    product_type: str  # router, car, washing machine, etc.
    user_terms: Dict[str, List[str]]  # technical term -> user synonyms
    common_problems: List[str]
    status_mechanisms: List[str]  # LEDs, displays, sounds, etc.
    key_components: List[str]

class UniversalContentExtractor:
    """Universal content extractor that works for any type of manual"""

    def __init__(self, model: GenerativeModel = None):
        self.model = model

        # Universal patterns that work across all manual types
        self.universal_patterns = {
            'status_indicators': [
                # LED/light patterns
                r'([\w\s]+)(?:LED|light|indicator):\s*(solid|blinking|flashing|pulsing|steady|off)\s*([\w\s]+)\s*[=:]\s*([^;.]+)',
                r'([\w\s]+)\s*(?:LED|light|indicator|lamp)\s*(?:is|shows|displays)?\s*(solid|blinking|flashing|pulsing|steady|off|red|blue|green|amber|white|magenta)\s*[=:]?\s*([^;.]+)',

                # Display/screen patterns
                r'(?:display|screen|monitor)\s*(?:shows|displays)?\s*["\']?([^"\']+)["\']?\s*[=:]\s*([^.]+)',

                # Sound patterns
                r'(?:beeps?|sounds?|chimes?|alerts?)\s*(\d+)\s*(?:times?)?\s*[=:]\s*([^.]+)',

                # General status patterns
                r'when\s+([\w\s]+)\s+(?:is|shows|displays)\s+([\w\s]+),?\s*(?:this\s+)?(?:means|indicates)?\s*([^.]+)',
                r'([\w\s]+)\s*status:\s*([^.]+)'
            ],

            'procedures': [
                # Numbered steps
                r'(?:step|Step|STEP)\s+(\d+)[:\.]?\s*([^.]+(?:\.[^.]*)*)',
                r'^(\d+)\.\s*([A-Z][^.]*(?:\.[^.]*)*)',

                # Sequential indicators
                r'(?:first|First|FIRST)[,:]?\s*([^.]+)',
                r'(?:next|Next|NEXT|then|Then)[,:]?\s*([^.]+)',
                r'(?:finally|Finally|FINALLY|last|Last)[,:]?\s*([^.]+)',

                # Action verbs (universal)
                r'((?:press|push|click|tap|turn|rotate|pull|push|connect|disconnect|plug|unplug|insert|remove|check|verify|ensure|confirm|wait|hold)\s+[^.]+)',
                r'((?:open|close|start|stop|begin|end|activate|deactivate|enable|disable|set|adjust|configure|install|uninstall)\s+[^.]+)'
            ],

            'troubleshooting': [
                # If-then patterns
                r'if\s+([^,]+),?\s*(?:then\s+)?([^.]+)',
                r'when\s+([^,]+),?\s*(?:try\s+|check\s+|verify\s+)?([^.]+)',

                # Problem-solution patterns
                r'problem:\s*([^.]+)\.?\s*solution:\s*([^.]+)',
                r'issue:\s*([^.]+)\.?\s*(?:fix|resolution):\s*([^.]+)',

                # Symptom patterns
                r'(?:error|fault|problem|issue)\s*[:\-]?\s*([^.]+)',
                r'(?:cannot|can\'t|unable\s+to|won\'t|doesn\'t)\s+([^.]+)'
            ],

            'specifications': [
                # Technical specs
                r'([\w\s]+):\s*(\d+[\w\s/%\-]+)',
                r'(maximum|minimum|max|min|up\s+to|supports?|requires?|compatible\s+with)\s+([^.]+)',
                r'(dimensions?|weight|size|capacity|speed|frequency|voltage|power)\s*[:\-]?\s*([^.]+)',

                # Feature lists
                r'(?:supports?|includes?|features?|provides?)\s*[:\-]?\s*([^.]+)',
                r'(?:compatible\s+with|works\s+with|requires?)\s*[:\-]?\s*([^.]+)'
            ],

            'safety_warnings': [
                r'\*\*(?:DANGER|WARNING|CAUTION|IMPORTANT|NOTE)\*\*[:\-]?\s*([^.]+)',
                r'(?:DANGER|WARNING|CAUTION|IMPORTANT)[:\-!]\s*([^.]+)',
                r'(?:always|never|do\s+not|don\'t)\s+([^.]+)',
                r'(?:before|prior\s+to|ensure|make\s+sure)\s+([^.]+)'
            ]
        }

    def analyze_domain(self, content: str, section_title: str = "") -> DomainInfo:
        """Analyze manual content to determine domain and extract key information"""

        if not self.model:
            # Fallback to pattern-based analysis
            return self._pattern_based_domain_analysis(content)

        try:
            prompt = f"""
Analyze this manual content and identify the product domain and key characteristics:

Section Title: {section_title}
Content: {content[:2000]}...

Please provide a JSON response with:
{{
    "category": "electronics|automotive|software|appliance|medical|industrial|consumer_goods|other",
    "product_type": "brief description of specific product type",
    "user_terms": {{
        "technical_term1": ["user_synonym1", "user_synonym2"],
        "technical_term2": ["user_synonym1", "user_synonym2"]
    }},
    "common_problems": ["problem1", "problem2", "problem3"],
    "status_mechanisms": ["LEDs", "display", "sounds", "vibration", etc.],
    "key_components": ["component1", "component2", "component3"]
}}

Focus on terms customers actually use vs technical manual language.
"""

            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 800
                }
            )

            if response.candidates and response.candidates[0].content.parts:
                response_text = response.candidates[0].content.parts[0].text.strip()

                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    domain_data = json.loads(json_match.group())

                    return DomainInfo(
                        category=domain_data.get('category', 'other'),
                        product_type=domain_data.get('product_type', 'unknown'),
                        user_terms=domain_data.get('user_terms', {}),
                        common_problems=domain_data.get('common_problems', []),
                        status_mechanisms=domain_data.get('status_mechanisms', []),
                        key_components=domain_data.get('key_components', [])
                    )

        except Exception as e:
            print(f"WARNING: LLM domain analysis failed: {e}")

        # Fallback to pattern-based analysis
        return self._pattern_based_domain_analysis(content)

    def _pattern_based_domain_analysis(self, content: str) -> DomainInfo:
        """Fallback domain analysis using patterns"""

        content_lower = content.lower()

        # Detect category based on keywords
        category_indicators = {
            'electronics': ['led', 'power', 'wifi', 'bluetooth', 'usb', 'ethernet', 'router', 'device', 'voltage'],
            'automotive': ['engine', 'battery', 'fuel', 'brake', 'tire', 'steering', 'transmission', 'dashboard'],
            'software': ['click', 'menu', 'window', 'install', 'download', 'application', 'browser', 'file'],
            'appliance': ['wash', 'dry', 'heat', 'cool', 'temperature', 'cycle', 'filter', 'maintenance']
        }

        category_scores = {}
        for cat, keywords in category_indicators.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            category_scores[cat] = score

        category = max(category_scores, key=category_scores.get) if category_scores else 'other'

        # Extract basic components mentioned
        component_patterns = [
            r'\b([a-z]+(?:\s+[a-z]+)*)\s+(?:button|switch|port|connector|cable|wire|panel|display|screen|indicator|light|led)\b',
            r'\b(?:the|your|main|primary)\s+([a-z]+(?:\s+[a-z]+)*)\b'
        ]

        components = set()
        for pattern in component_patterns:
            matches = re.findall(pattern, content_lower)
            components.update([match.strip() for match in matches if len(match.strip()) > 2])

        return DomainInfo(
            category=category,
            product_type='unknown',
            user_terms={},
            common_problems=[],
            status_mechanisms=['indicator', 'light', 'display'],
            key_components=list(components)[:10]  # Limit to top 10
        )

    def extract_status_indicators(self, content: str, domain_info: DomainInfo) -> List[ExtractedContent]:
        """Extract status indicator information (LEDs, displays, sounds, etc.)"""

        extracted = []

        for pattern in self.universal_patterns['status_indicators']:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)

            for match in matches:
                groups = match.groups()

                if len(groups) >= 3:
                    indicator = groups[0].strip()
                    state = groups[1].strip() if len(groups) > 1 else ""
                    meaning = groups[-1].strip()

                    # Create clean, standardized text
                    clean_text = f"{indicator} {state} = {meaning}".strip()

                    extracted.append(ExtractedContent(
                        content_type='status_indicator',
                        text=clean_text,
                        metadata={
                            'indicator_name': indicator,
                            'indicator_state': state,
                            'meaning': meaning,
                            'mechanism_type': self._classify_status_mechanism(indicator)
                        },
                        confidence=0.9,
                        source_section='status_indicators'
                    ))

        return extracted

    def extract_procedures(self, content: str, domain_info: DomainInfo) -> List[ExtractedContent]:
        """Extract procedural content with step-by-step instructions"""

        extracted = []

        # Extract numbered steps
        step_pattern = r'(?:step|Step|STEP)\s+(\d+)[:\.]?\s*([^.]+(?:\.[^.]*)*)'
        step_matches = re.finditer(step_pattern, content, re.IGNORECASE | re.MULTILINE)

        steps = []
        for match in step_matches:
            step_num = match.group(1)
            step_text = match.group(2).strip()
            steps.append((int(step_num), step_text))

        # Create procedure summary if we have steps
        if steps:
            steps.sort(key=lambda x: x[0])  # Sort by step number

            # Create individual step chunks
            for step_num, step_text in steps:
                extracted.append(ExtractedContent(
                    content_type='procedure_step',
                    text=f"Step {step_num}: {step_text}",
                    metadata={
                        'step_number': step_num,
                        'total_steps': len(steps),
                        'action_type': self._classify_action_type(step_text)
                    },
                    confidence=0.9,
                    source_section='procedures'
                ))

            # Create procedure summary
            summary_text = f"Procedure with {len(steps)} steps: " + " → ".join([
                step_text[:50] + "..." if len(step_text) > 50 else step_text
                for _, step_text in steps[:3]
            ])

            extracted.append(ExtractedContent(
                content_type='procedure_summary',
                text=summary_text,
                metadata={
                    'total_steps': len(steps),
                    'procedure_type': self._classify_procedure_type(content)
                },
                confidence=0.8,
                source_section='procedures'
            ))

        return extracted

    def extract_troubleshooting(self, content: str, domain_info: DomainInfo) -> List[ExtractedContent]:
        """Extract troubleshooting information (problems and solutions)"""

        extracted = []

        # Extract if-then patterns
        if_then_pattern = r'if\s+([^,]+),?\s*(?:then\s+)?([^.]+)'
        matches = re.finditer(if_then_pattern, content, re.IGNORECASE)

        for match in matches:
            condition = match.group(1).strip()
            action = match.group(2).strip()

            extracted.append(ExtractedContent(
                content_type='troubleshooting',
                text=f"If {condition}, then {action}",
                metadata={
                    'problem_condition': condition,
                    'solution_action': action,
                    'severity': self._assess_problem_severity(condition)
                },
                confidence=0.8,
                source_section='troubleshooting'
            ))

        # Extract problem-solution patterns
        problem_pattern = r'(?:problem|issue|error)\s*[:\-]?\s*([^.]+)'
        problems = re.finditer(problem_pattern, content, re.IGNORECASE)

        for match in problems:
            problem_text = match.group(1).strip()

            extracted.append(ExtractedContent(
                content_type='problem_description',
                text=f"Problem: {problem_text}",
                metadata={
                    'problem_type': self._classify_problem_type(problem_text),
                    'urgency': self._assess_problem_urgency(problem_text)
                },
                confidence=0.7,
                source_section='troubleshooting'
            ))

        return extracted

    def extract_specifications(self, content: str, domain_info: DomainInfo) -> List[ExtractedContent]:
        """Extract technical specifications and features"""

        extracted = []

        # Extract key specifications
        spec_pattern = r'([\w\s]+):\s*([^.]+)'
        matches = re.finditer(spec_pattern, content)

        for match in matches:
            spec_name = match.group(1).strip()
            spec_value = match.group(2).strip()

            # Filter out non-specification content
            if self._is_specification(spec_name, spec_value):
                extracted.append(ExtractedContent(
                    content_type='specification',
                    text=f"{spec_name}: {spec_value}",
                    metadata={
                        'spec_category': self._classify_spec_category(spec_name),
                        'measurable': self._has_measurement(spec_value)
                    },
                    confidence=0.8,
                    source_section='specifications'
                ))

        return extracted

    def extract_all_content(self, content: str, section_title: str = "") -> Tuple[DomainInfo, List[ExtractedContent]]:
        """Extract all types of content from a section"""

        # First, analyze the domain
        domain_info = self.analyze_domain(content, section_title)

        all_extracted = []

        # Extract each content type
        all_extracted.extend(self.extract_status_indicators(content, domain_info))
        all_extracted.extend(self.extract_procedures(content, domain_info))
        all_extracted.extend(self.extract_troubleshooting(content, domain_info))
        all_extracted.extend(self.extract_specifications(content, domain_info))

        return domain_info, all_extracted

    # Helper methods for classification
    def _classify_status_mechanism(self, indicator: str) -> str:
        """Classify the type of status mechanism"""
        indicator_lower = indicator.lower()

        if any(term in indicator_lower for term in ['led', 'light', 'lamp']):
            return 'visual_led'
        elif any(term in indicator_lower for term in ['display', 'screen', 'monitor']):
            return 'visual_display'
        elif any(term in indicator_lower for term in ['beep', 'sound', 'chime', 'alert']):
            return 'audio'
        elif any(term in indicator_lower for term in ['vibration', 'vibrate']):
            return 'haptic'
        else:
            return 'visual_other'

    def _classify_action_type(self, step_text: str) -> str:
        """Classify the type of action in a procedure step"""
        step_lower = step_text.lower()

        if any(verb in step_lower for verb in ['press', 'push', 'click', 'tap']):
            return 'button_action'
        elif any(verb in step_lower for verb in ['connect', 'plug', 'insert']):
            return 'connection'
        elif any(verb in step_lower for verb in ['check', 'verify', 'confirm', 'ensure']):
            return 'verification'
        elif any(verb in step_lower for verb in ['wait', 'pause']):
            return 'wait'
        elif any(verb in step_lower for verb in ['turn', 'rotate', 'adjust']):
            return 'adjustment'
        else:
            return 'general'

    def _classify_procedure_type(self, content: str) -> str:
        """Classify the overall type of procedure"""
        content_lower = content.lower()

        if any(term in content_lower for term in ['setup', 'install', 'initial', 'first time']):
            return 'setup'
        elif any(term in content_lower for term in ['troubleshoot', 'problem', 'fix', 'resolve']):
            return 'troubleshooting'
        elif any(term in content_lower for term in ['maintain', 'clean', 'care', 'service']):
            return 'maintenance'
        elif any(term in content_lower for term in ['configure', 'setting', 'option']):
            return 'configuration'
        else:
            return 'operation'

    def _assess_problem_severity(self, condition: str) -> str:
        """Assess the severity of a problem condition"""
        condition_lower = condition.lower()

        if any(term in condition_lower for term in ['danger', 'fire', 'explosion', 'death', 'injury']):
            return 'critical'
        elif any(term in condition_lower for term in ['error', 'fail', 'broken', 'damage']):
            return 'high'
        elif any(term in condition_lower for term in ['slow', 'delay', 'intermittent']):
            return 'medium'
        else:
            return 'low'

    def _classify_problem_type(self, problem_text: str) -> str:
        """Classify the type of problem"""
        problem_lower = problem_text.lower()

        if any(term in problem_lower for term in ['connect', 'network', 'wifi', 'internet']):
            return 'connectivity'
        elif any(term in problem_lower for term in ['power', 'battery', 'charge']):
            return 'power'
        elif any(term in problem_lower for term in ['slow', 'performance', 'speed']):
            return 'performance'
        elif any(term in problem_lower for term in ['display', 'screen', 'visual']):
            return 'display'
        elif any(term in problem_lower for term in ['sound', 'audio', 'volume']):
            return 'audio'
        else:
            return 'general'

    def _assess_problem_urgency(self, problem_text: str) -> str:
        """Assess the urgency of a problem"""
        problem_lower = problem_text.lower()

        if any(term in problem_lower for term in ['urgent', 'critical', 'emergency', 'immediately']):
            return 'high'
        elif any(term in problem_lower for term in ['important', 'soon', 'quickly']):
            return 'medium'
        else:
            return 'low'

    def _classify_spec_category(self, spec_name: str) -> str:
        """Classify the category of a specification"""
        spec_lower = spec_name.lower()

        if any(term in spec_lower for term in ['dimension', 'size', 'width', 'height', 'depth', 'weight']):
            return 'physical'
        elif any(term in spec_lower for term in ['power', 'voltage', 'current', 'wattage']):
            return 'electrical'
        elif any(term in spec_lower for term in ['speed', 'frequency', 'bandwidth', 'throughput']):
            return 'performance'
        elif any(term in spec_lower for term in ['temperature', 'humidity', 'environment']):
            return 'environmental'
        elif any(term in spec_lower for term in ['compatible', 'support', 'requirement']):
            return 'compatibility'
        else:
            return 'general'

    def _is_specification(self, name: str, value: str) -> bool:
        """Determine if a name-value pair is actually a specification"""
        # Filter out non-specification content
        name_lower = name.lower()
        value_lower = value.lower()

        # Skip if it looks like regular text
        if len(name.split()) > 5 or len(value.split()) > 10:
            return False

        # Include if it has measurements or technical indicators
        if any(indicator in value_lower for indicator in ['mhz', 'ghz', 'mbps', 'gbps', 'gb', 'mb', 'kg', 'lb', 'cm', 'inch', 'volt', 'amp', 'watt']):
            return True

        # Include if name suggests it's a spec
        if any(term in name_lower for term in ['maximum', 'minimum', 'max', 'min', 'capacity', 'speed', 'frequency', 'power', 'voltage', 'dimension', 'weight', 'size']):
            return True

        return False

    def _has_measurement(self, value: str) -> bool:
        """Check if a value contains a measurement"""
        return bool(re.search(r'\d+\s*[a-zA-Z]+', value))

# Test function
if __name__ == "__main__":
    extractor = UniversalContentExtractor()

    # Test with sample content
    test_content = """
    Router LED (front): Pulsing white = booting or Sync pressed; Solid white = factory reset in progress; Solid magenta = cannot connect to Internet; Off = finished booting/working normally.

    Step 1: Connect the router to your modem using an Ethernet cable.
    Step 2: Press the power button and wait for the LED to turn solid blue.

    If the LED is red, check the power connection.

    Maximum speed: 1.2 Gbps
    Dimensions: 10 x 8 x 3 inches
    """

    domain_info, extracted_content = extractor.extract_all_content(test_content, "Router Setup")

    print(f"Domain: {domain_info.category} - {domain_info.product_type}")
    print(f"Extracted {len(extracted_content)} content items:")

    for item in extracted_content:
        print(f"  - {item.content_type}: {item.text[:80]}...")