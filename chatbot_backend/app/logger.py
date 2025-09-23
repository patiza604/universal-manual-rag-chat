# app/logger.py
import logging
import re
from typing import Any

class SecurityFilter(logging.Filter):
    """Filter to sanitize sensitive data from logs"""
    
    SENSITIVE_PATTERNS = [
        r'Bearer\s+[A-Za-z0-9\-_]+',  # Bearer tokens
        r'password["\']?\s*[:=]\s*["\']?[^"\'\s]+',  # Passwords
        r'token["\']?\s*[:=]\s*["\']?[^"\'\s]+',  # Tokens
        r'key["\']?\s*[:=]\s*["\']?[^"\'\s]+',  # API keys
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter sensitive data from log records"""
        if hasattr(record, 'msg') and record.msg:
            msg = str(record.msg)
            for pattern in self.SENSITIVE_PATTERNS:
                msg = re.sub(pattern, '[REDACTED]', msg, flags=re.IGNORECASE)
            record.msg = msg
        return True

def setup_logging():
    """Setup secure logging configuration"""
    # Create security filter
    security_filter = SecurityFilter()
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Add security filter to all handlers
    for handler in logging.root.handlers:
        handler.addFilter(security_filter)
    
    # Disable verbose library logging
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('vertexai').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    
    print("DEBUG: Secure logging configured")