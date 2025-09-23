# training/scripts/content_classifier.py
import os
import sys
import json
import re
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting, HarmCategory, HarmBlockThreshold
from google.oauth2 import service_account
from app.config import *

class ContentClassifier:
    """LLM-based content classification with regex fallback"""
    
    def __init__(self,
                 project_id: str = PROJECT_ID,
                 location: str = LOCATION,
                 model_name: str = "gemini-2.5-pro",  # Updated to current stable model
                 credentials_path: str = None,
                 model: GenerativeModel = None):  # Allow passing pre-initialized model

        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.confidence_threshold = getattr(sys.modules['app.config'], 'CLASSIFICATION_CONFIDENCE_THRESHOLD', 0.7)

        # Use provided model or initialize new one
        if model:
            self.model = model
            print(f"SUCCESS: Content classifier using provided {model_name} model")
        else:
            # Initialize Vertex AI
            self._initialize_vertex_ai(credentials_path)
        
        # Pattern-based fallback definitions
        self.content_patterns = {
            'procedure': [
                r'(?:Step|STEP)\s+\d+[:\.]',
                r'\d+\.\s+[A-Z][^.]*(?:the|to|and|with)',
                r'(?:Instructions?|Procedure|How to|Follow these)',
                r'(?:First|Next|Then|Finally),?\s+[a-z]',
                r'Press.*button|Turn.*switch|Check.*level'
            ],
            'safety_alert': [
                r'\*\*(?:DANGER|WARNING|CAUTION|NOTE|IMPORTANT)\*\*',
                r'(?:DANGER|WARNING|CAUTION)[:!]',
                r'Safety\s+(?:Protocol|Requirements?|Information)',
                r'(?:Always|Never|Ensure|Before).*(?:safety|danger|injury|death)'
            ],
            'troubleshooting': [
                r'(?:Problem|Issue|Error|Fault|Trouble)',
                r'(?:If.*then|When.*occurs|Solution|Fix|Resolve)',
                r'(?:Check|Verify|Inspect|Test).*(?:for|if|that)',
                r'(?:Common|Typical)\s+(?:problems?|issues?|errors?)'
            ],
            'faq': [
                r'(?:Q:|Question:|A:|Answer:)',
                r'(?:What|How|Why|When|Where)\s+(?:is|are|do|does|can|should)',
                r'(?:Frequently|Common)\s+(?:Asked|Questions?)'
            ],
            'reference': [
                r'(?:Specification|Technical Data|Parts? List)',
                r'(?:Contact|Phone|Email|Address)',
                r'(?:Model|Part Number|Serial)',
                r'(?:Copyright|©|All Rights Reserved)'
            ]
        }
        
        self.role_patterns = {
            'procedure_step': [
                r'(?:Step|STEP)\s+\d+',
                r'\d+\.\s+[A-Z]',
                r'(?:Press|Turn|Check|Set|Adjust|Install)'
            ],
            'safety_critical': [
                r'\*\*(?:DANGER|WARNING)\*\*',
                r'(?:DANGER|WARNING)[:!]',
                r'(?:death|injury|serious|critical)'
            ],
            'faq_answer': [
                r'(?:A:|Answer:)',
                r'(?:The answer|To do this|This means)'
            ],
            'overview': [
                r'(?:Introduction|Overview|Summary)',
                r'(?:This section|The following)',
                r'(?:provides|describes|explains|covers)'
            ]
        }
    
    def _initialize_vertex_ai(self, credentials_path: str = None):
        """Initialize Vertex AI with credentials"""
        try:
            if credentials_path and os.path.exists(credentials_path):
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                vertexai.init(project=self.project_id, location=self.location, credentials=credentials)
            else:
                vertexai.init(project=self.project_id, location=self.location)
            
            self.model = GenerativeModel(self.model_name)
            print(f"SUCCESS: Content classifier initialized with {self.model_name}")
            
        except Exception as e:
            print(f"ERROR: Failed to initialize Vertex AI: {e}")
            self.model = None
    
    def classify_chunk(self, 
                      chunk_content: str, 
                      section_title: str = "",
                      chunk_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Classify a chunk using LLM first, then fallback to patterns
        
        Returns:
            Dict with content_type, semantic_role, group_id, completeness_score, confidence
        """
        
        # Try LLM classification first
        if self.model:
            try:
                llm_result = self._classify_with_llm(chunk_content, section_title, chunk_metadata)
                if llm_result['confidence'] >= self.confidence_threshold:
                    llm_result['classification_method'] = 'llm'
                    return llm_result
                else:
                    print(f"INFO: LLM confidence {llm_result['confidence']:.2f} below threshold, using fallback")
            except Exception as e:
                print(f"WARNING: LLM classification failed: {e}")
        
        # Fallback to pattern-based classification
        pattern_result = self._classify_with_patterns(chunk_content, section_title, chunk_metadata)
        pattern_result['classification_method'] = 'pattern_fallback'
        return pattern_result

    def _classify_with_llm(self, chunk_content: str, section_title: str = "", chunk_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Classify using Gemini LLM with safe parsing, retries, and pattern fallback."""

        def safe_parse_json(raw_text: str) -> Dict[str, Any]:
            """Cleans and safely parses JSON from LLM output, handling truncations."""
            cleaned = re.sub(r"```(?:json)?", "", raw_text).strip("` \n")
            # Fix unterminated strings by adding " if missing
            if cleaned.count('"') % 2 != 0:
                cleaned += '"'
            if "}" in cleaned:
                cleaned = cleaned[:cleaned.rfind("}")+1]
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                # Fallback: extract key-value with regex if broken
                result = {
                    "content_type": "manual_section",
                    "semantic_role": "general",
                    "group_id": None,
                    "completeness_score": 0.5,
                    "confidence": 0.5,
                    "reasoning": "Parsed from incomplete response"
                }
                for key in result:
                    match = re.search(rf'"{key}":\s*["\d\w\.\s-]*', cleaned)
                    if match:
                        value = match.group(0).split(":", 1)[1].strip(' "')
                        if key in ["completeness_score", "confidence"]:
                            try:
                                result[key] = float(value)
                            except:
                                pass
                        else:
                            result[key] = value
                return result

        # Stricter prompt to reduce thinking/verbosity
        base_prompt = f"""
Output ONLY the JSON object immediately, nothing else. Keep reasoning to 1-2 short sentences (max 50 words).

Analyze this document chunk:

CHUNK CONTENT:
{chunk_content[:1500]}

SECTION: {section_title}

{{
"content_type": "procedure|faq|troubleshooting|safety_alert|reference|manual_section",
"semantic_role": "procedure_step|faq_answer|safety_critical|overview|general",
"group_id": "descriptive_group_identifier_or_null",
"completeness_score": 0.0-1.0,
"confidence": 0.0-1.0,
"reasoning": "brief explanation"
}}
"""

        # Safety settings
        safety_settings = [
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=HarmBlockThreshold.BLOCK_NONE
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=HarmBlockThreshold.BLOCK_NONE
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=HarmBlockThreshold.BLOCK_NONE
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=HarmBlockThreshold.BLOCK_NONE
            )
        ]

        # Retry classification up to 3 times, with dynamic config
        for attempt in range(3):
            try:
                content_slice = chunk_content[:1000] if attempt == 0 else (chunk_content[:500] if attempt == 1 else chunk_content[:300])
                prompt = base_prompt.replace(chunk_content[:1500], content_slice)

                print(f"DEBUG: Sending classification request (attempt {attempt+1}) to {self.model_name}...", flush=True)

                gen_config = {
                    "temperature": 0.0,  # Lowered for conciseness
                }
                if attempt < 2:
                    gen_config["max_output_tokens"] = 4096  # Increased further
                # On last attempt, no max to avoid cap

                response = self.model.generate_content(
                    prompt,
                    generation_config=gen_config,
                    safety_settings=safety_settings
                )

                # Check for MAX_TOKENS early
                if response.candidates and response.candidates[0].finish_reason == "MAX_TOKENS":
                    print(f"DEBUG: MAX_TOKENS hit (thoughts: {response.usage_metadata.thoughts_token_count if hasattr(response.usage_metadata, 'thoughts_token_count') else 'N/A'})", flush=True)
                    if attempt < 2:
                        continue

                raw_text = getattr(response, "text", None)
                if not raw_text and hasattr(response, "candidates") and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, "content") and candidate.content.parts:
                        raw_text = candidate.content.parts[0].text

                if not raw_text:
                    raise Exception("Gemini returned no usable text.")

                raw_text = raw_text.strip()
                print(f"DEBUG: RAW LLM RESPONSE (attempt {attempt+1}): {raw_text[:300]}...", flush=True)

                result = safe_parse_json(raw_text)
                return self._validate_classification_result(result)

            except json.JSONDecodeError as je:
                print(f"WARNING: JSON parse error (attempt {attempt+1}): {je}", flush=True)
                continue
            except Exception as e:
                print(f"❌ LLM classification error (attempt {attempt+1}): {e}", flush=True)
                continue

        # If all retries fail, fallback
        print("WARNING: LLM failed after retries, falling back to pattern classification.", flush=True)
        return {
            "content_type": "manual_section",
            "semantic_role": "general",
            "group_id": None,
            "completeness_score": 0.5,
            "confidence": 0.0,
            "reasoning": "LLM failed after 3 attempts, using pattern-based fallback."
        }

    def _classify_with_patterns(self, 
                                chunk_content: str, 
                                section_title: str = "",
                                chunk_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fallback pattern-based classification"""
        
        content_lower = chunk_content.lower()
        title_lower = section_title.lower() if section_title else ""
        
        # Determine content type
        content_type = 'manual_section'  # default
        content_scores = {}
        
        for ctype, patterns in self.content_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, chunk_content, re.IGNORECASE | re.MULTILINE))
                score += matches
            content_scores[ctype] = score
        
        # Get highest scoring content type
        if max(content_scores.values()) > 0:
            content_type = max(content_scores, key=content_scores.get)
        
        # Determine semantic role
        semantic_role = 'general'  # default
        role_scores = {}
        
        for role, patterns in self.role_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, chunk_content, re.IGNORECASE | re.MULTILINE))
                score += matches
            role_scores[role] = score
        
        if max(role_scores.values()) > 0:
            semantic_role = max(role_scores, key=role_scores.get)
        
        # Generate group_id for procedures
        group_id = None
        if content_type == 'procedure' or semantic_role == 'procedure_step':
            group_id = self._generate_group_id_from_patterns(chunk_content, section_title)
        
        # Calculate completeness score based on patterns
        completeness_score = self._calculate_pattern_completeness(chunk_content, content_type, semantic_role)
        
        return {
            'content_type': content_type,
            'semantic_role': semantic_role,
            'group_id': group_id,
            'completeness_score': completeness_score,
            'confidence': 0.8,  # Pattern matching is fairly reliable
            'reasoning': f'Pattern-based: {content_type} ({content_scores[content_type]} matches)'
        }
    
    def _generate_group_id_from_patterns(self, content: str, section_title: str) -> Optional[str]:
        """Generate group_id for procedural content"""
        
        # Extract procedure name from section title
        if section_title:
            # Clean section title for group ID
            clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', section_title.lower())
            clean_title = re.sub(r'\s+', '_', clean_title.strip())
            
            if any(keyword in clean_title for keyword in ['startup', 'procedure', 'calibrat', 'setup']):
                return f"procedure_{clean_title}_001"
        
        # Look for procedure indicators in content
        procedure_indicators = [
            (r'calibrat\w*', 'calibration'),
            (r'startup|start.?up', 'startup'),
            (r'maintenance|service', 'maintenance'),
            (r'troubleshoot\w*', 'troubleshooting'),
            (r'setup|set.?up', 'setup')
        ]
        
        for pattern, name in procedure_indicators:
            if re.search(pattern, content, re.IGNORECASE):
                return f"procedure_{name}_001"
        
        return None
    
    def _calculate_pattern_completeness(self, content: str, content_type: str, semantic_role: str) -> float:
        """Calculate completeness score based on content analysis"""
        
        score = 0.5  # baseline
        
        # Check for complete sentences
        sentences = re.split(r'[.!?]+', content.strip())
        complete_sentences = [s for s in sentences if len(s.strip().split()) > 3]
        if len(complete_sentences) > 0:
            score += 0.2
        
        # Content type specific scoring
        if content_type == 'procedure':
            if re.search(r'(?:Step|STEP)\s+\d+', content):
                score += 0.1
            if re.search(r'(?:Press|Turn|Check|Set|Adjust)', content, re.IGNORECASE):
                score += 0.1
        
        elif content_type == 'safety_alert':
            if re.search(r'\*\*(?:DANGER|WARNING)\*\*', content):
                score = 1.0  # Safety content should always be complete
        
        elif semantic_role == 'faq_answer':
            if re.search(r'(?:A:|Answer:)', content):
                score += 0.3
        
        # Penalize very short content
        word_count = len(content.split())
        if word_count < 50:
            score -= 0.3
        elif word_count < 20:
            score -= 0.5
        
        return max(0.0, min(1.0, score))
    
    def _validate_classification_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean LLM classification result"""
        
        valid_content_types = {'procedure', 'faq', 'troubleshooting', 'safety_alert', 'reference', 'manual_section'}
        valid_semantic_roles = {'procedure_step', 'faq_answer', 'safety_critical', 'overview', 'troubleshooting', 'general'}
        
        # Validate content_type
        if result.get('content_type') not in valid_content_types:
            result['content_type'] = 'manual_section'
        
        # Validate semantic_role
        if result.get('semantic_role') not in valid_semantic_roles:
            result['semantic_role'] = 'general'
        
        # Validate numeric fields
        result['completeness_score'] = max(0.0, min(1.0, float(result.get('completeness_score', 0.5))))
        result['confidence'] = max(0.0, min(1.0, float(result.get('confidence', 0.5))))
        
        # Clean group_id
        if result.get('group_id') and result['group_id'].lower() in ['null', 'none', '']:
            result['group_id'] = None
        
        return result

# Test function
if __name__ == "__main__":
    classifier = ContentClassifier()
    
    test_content = """
    Step 1: Set up Joystick Button Mapping
    Create your own joystick button mapping profile. This will be saved to your profile login. 
    Each user can have their own joystick profile customized to their preferences and operating style.
    """
    
    result = classifier.classify_chunk(test_content, "Initial Startup Day Procedures")
    print(json.dumps(result, indent=2))