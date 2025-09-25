# app/config.py
import os
from typing import List
from vertexai.generative_models import HarmCategory, HarmBlockThreshold
from pydantic_settings import BaseSettings

# Project Configuration
PROJECT_ID = os.getenv("PROJECT_ID", "ai-chatbot-472322")
LOCATION = os.getenv("LOCATION", "us-central1")
PROJECT_NUMBER = os.getenv("PROJECT_NUMBER", "325296751367")
IS_LOCAL = os.getenv("IS_LOCAL", "false").lower() == "true"

# Local FAISS Configuration
LOCAL_VECTOR_FILES_PATH = os.getenv("LOCAL_VECTOR_FILES_PATH", "app/vector-files")
FAISS_INDEX_TYPE = os.getenv("FAISS_INDEX_TYPE", "IVF")

# RAG Configuration - Enhanced
EMBEDDING_QUANT = int(os.getenv("EMBEDDING_QUANT", "10"))
DYNAMIC_RETRIEVAL = os.getenv("DYNAMIC_RETRIEVAL", "true").lower() == "true"
MIN_CHUNKS_SIMPLE = int(os.getenv("MIN_CHUNKS_SIMPLE", "3"))
MAX_CHUNKS_SIMPLE = int(os.getenv("MAX_CHUNKS_SIMPLE", "5"))
MIN_CHUNKS_DETAILED = int(os.getenv("MIN_CHUNKS_DETAILED", "10"))
MAX_CHUNKS_DETAILED = int(os.getenv("MAX_CHUNKS_DETAILED", "20"))
SECTION_EXPANSION_ENABLED = os.getenv("SECTION_EXPANSION_ENABLED", "true").lower() == "true"

# Enhanced Chunking Configuration (for vector creation only)
ENABLE_LLM_CLASSIFICATION = os.getenv("ENABLE_LLM_CLASSIFICATION", "true").lower() == "true"
CLASSIFICATION_CONFIDENCE_THRESHOLD = float(os.getenv("CLASSIFICATION_CONFIDENCE_THRESHOLD", "0.7"))
ENABLE_MULTI_LEVEL_CHUNKING = os.getenv("ENABLE_MULTI_LEVEL_CHUNKING", "true").lower() == "true"
ENABLE_INDEX_PARTITIONING = os.getenv("ENABLE_INDEX_PARTITIONING", "false").lower() == "true"

# Quality Scoring (for vector creation only)
MIN_COMPLETENESS_SCORE = float(os.getenv("MIN_COMPLETENESS_SCORE", "0.3"))
MIN_TOKEN_EFFICIENCY = float(os.getenv("MIN_TOKEN_EFFICIENCY", "1.5"))

# Chunking Configuration - UNIFIED (removed duplicates)
CHUNK_SIZE_MIN = int(os.getenv("CHUNK_SIZE_MIN", "512"))  # Updated to 512 for enhanced system
CHUNK_SIZE_MAX = int(os.getenv("CHUNK_SIZE_MAX", "1024"))  # Updated to 1024 for enhanced system
CHUNK_OVERLAP_PERCENT = int(os.getenv("CHUNK_OVERLAP_PERCENT", "10"))  # Reduced overlap for enhanced system
SEMANTIC_CHUNKING = os.getenv("SEMANTIC_CHUNKING", "true").lower() == "true"

# Multi-language Configuration
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en-US")
SUPPORTED_LANGUAGES = os.getenv("SUPPORTED_LANGUAGES", "en-US,es-ES,fr-CA").split(",")
AUTO_DETECT_LANGUAGE = os.getenv("AUTO_DETECT_LANGUAGE", "false").lower() == "true"

# Firebase Storage Configuration - UPDATED
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "ai-chatbot-472322")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "ai-chatbot-472322.appspot.com")
# Using Application Default Credentials - no key file needed
# FIREBASE_CREDENTIALS_PATH = os.path.join("gcp-keys", "ai-chatbot-beb8d-firebase-adminsdk-fbsvc-c2ce8b36f1.json")
FIREBASE_STORAGE_BASE_URL = f"https://firebasestorage.googleapis.com/v0/b/{FIREBASE_STORAGE_BUCKET}/o/"
IMAGE_BASE_PATH = os.getenv("IMAGE_BASE_PATH", "manual001/")

# Image storage paths
IMAGE_STORAGE_PATH = "ai_images/manual001"
SIGNED_URL_EXPIRATION_HOURS = int(os.getenv("SIGNED_URL_EXPIRATION_HOURS", "24"))

# Query Classification
QUERY_CLASSIFICATION_ENABLED = os.getenv("QUERY_CLASSIFICATION_ENABLED", "true").lower() == "true"
CLASSIFICATION_MODEL = os.getenv("CLASSIFICATION_MODEL", "gemini-2.5-flash")

# Security Configuration
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
LOG_QUERIES = os.getenv("LOG_QUERIES", "false").lower() == "true"

# CORS Configuration
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:54671,https://ai-chatbot-472322.web.app")
CORS_ORIGINS: List[str] = [origin.strip() for origin in CORS_ORIGINS_STR.split(",")]

# Model Configuration
GENERATIVE_MODEL_NAME = os.getenv("GENERATIVE_MODEL_NAME", "gemini-2.5-flash")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-004")

# Credentials Configuration - Using Application Default Credentials
# No credential files needed when using ADC

# TTS Configuration
DEFAULT_VOICE_NAME = os.getenv("DEFAULT_VOICE_NAME", "en-US-Chirp3-HD-Leda")
DEFAULT_LANGUAGE_CODE = os.getenv("DEFAULT_LANGUAGE_CODE", "en-US")

# Safety Settings
GLOBAL_SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
}

# Product Keywords for Classification
PRODUCT_PROCEDURAL_KEYWORDS = [
    'product', 'feature', 'component', 'accessory', 'settings',
    'setup', 'installation', 'operation', 'guidelines', 'troubleshooting',
    'maintenance', 'safety', 'support', 'diagram', 'model',
    'power', 'indicator'
]

GENERAL_PROCEDURAL_KEYWORDS = [
    "how to", "step by step", "guide", "process", "maintain", "troubleshoot",
    "procedure", "best practices", "detailed explanation", "install", "setup"
]

SIMPLE_QUERY_INDICATORS = [
    "what is", "define", "meaning", "type of", "specification", "model",
    "part number", "weight", "dimension", "capacity", "speed", "pressure"
]


class Settings(BaseSettings):
    PROJECT_ID: str = "ai-chatbot-472322"
    LOCATION: str = "us-central1"
    GENERATIVE_MODEL_NAME: str = "gemini-2.5-flash"
    EMBEDDING_MODEL_NAME: str = "text-embedding-004"
    DEFAULT_VOICE_NAME: str = "en-US-Chirp3-HD-Leda"

    class Config:
        env_file = ".env"