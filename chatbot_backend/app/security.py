# app/security.py
import os
import secrets
import hashlib
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader
import logging

logger = logging.getLogger(__name__)

# API Key authentication
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Bearer token authentication
security = HTTPBearer(auto_error=False)

# Load API keys from environment
VALID_API_KEYS = set()
api_keys_env = os.getenv("API_KEYS", "")
if api_keys_env:
    VALID_API_KEYS = set(key.strip() for key in api_keys_env.split(",") if key.strip())

# Admin API key for sensitive operations
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

def hash_api_key(api_key: str) -> str:
    """Hash API key for secure comparison"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key(api_key: str) -> bool:
    """Verify API key against valid keys"""
    if not api_key or not VALID_API_KEYS:
        return False

    # Check both plain and hashed versions for compatibility
    return api_key in VALID_API_KEYS or hash_api_key(api_key) in VALID_API_KEYS

def verify_admin_key(api_key: str) -> bool:
    """Verify admin API key for sensitive operations"""
    if not api_key or not ADMIN_API_KEY:
        return False
    return api_key == ADMIN_API_KEY

async def get_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """Get and validate API key from header"""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide X-API-Key header."
        )

    if not verify_api_key(api_key):
        logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return api_key

async def get_admin_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """Get and validate admin API key"""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Admin API key required"
        )

    if not verify_admin_key(api_key):
        logger.warning(f"Invalid admin API key attempted: {api_key[:8]}...")
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return api_key

async def get_bearer_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> str:
    """Get and validate bearer token (for Firebase Auth integration)"""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Bearer token required"
        )

    # For now, just return the token - can be extended for Firebase Auth validation
    return credentials.credentials

# Rate limiting setup (basic implementation)
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, max_requests: int = 100, time_window: int = 3600):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()

        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key]
                            if now - req_time < self.time_window]

        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            return False

        # Add current request
        self.requests[key].append(now)
        return True

# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=100, time_window=3600)  # 100 requests per hour

def check_rate_limit(key: str):
    """Check rate limit and raise exception if exceeded"""
    if not rate_limiter.is_allowed(key):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later."
        )

# Security configuration
SECURITY_CONFIG = {
    "api_key_required": bool(VALID_API_KEYS),
    "admin_key_configured": bool(ADMIN_API_KEY),
    "rate_limiting_enabled": True,
    "cors_restricted": True
}

def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def get_security_status() -> dict:
    """Get current security status for monitoring"""
    return {
        "api_keys_configured": len(VALID_API_KEYS),
        "admin_key_configured": bool(ADMIN_API_KEY),
        "rate_limiting_active": True,
        "total_requests_tracked": sum(len(requests) for requests in rate_limiter.requests.values())
    }