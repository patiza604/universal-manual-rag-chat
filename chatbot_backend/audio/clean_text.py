import re

def clean_for_tts(text: str) -> str:
    """
    Clean text for TTS by removing markdown, special characters, and formatting
    that would cause the AI to speak unwanted characters.
    """
    if not text:
        return ""
    
    cleaned = text
    
    # Remove asterisks used for emphasis (*text*)
    cleaned = re.sub(r'\*([^\*]+)\*', r'\1', cleaned)
    
    # Remove markdown bold (**text**)
    cleaned = re.sub(r'\*\*([^\*]+)\*\*', r'\1', cleaned)
    
    # Remove underscores used for emphasis (_text_)
    cleaned = re.sub(r'_([^_]+)_', r'\1', cleaned)
    
    # Remove markdown headers (# ## ###)
    cleaned = re.sub(r'^#{1,6}\s*', '', cleaned, flags=re.MULTILINE)
    
    # Remove markdown links [text](url) - keep only the text
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)
    
    # Remove backticks for inline code (`code`)
    cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)
    
    # Remove triple backticks for code blocks (```code```)
    cleaned = re.sub(r'```[^`]*```', '', cleaned, flags=re.DOTALL)
    
    # Remove HTML tags
    cleaned = re.sub(r'<[^>]*>', '', cleaned)

    # Explicitly remove apostrophes (single quotes)
    cleaned = re.sub(r"['’]", '', cleaned) 
    
    # Remove special characters that might cause TTS issues
    # Keep basic punctuation that helps with speech flow
    cleaned = re.sub(r'[~`!@#$%^&*()_+=$$ ${}|\\:";<>?/]', ' ', cleaned) 
    
    # Replace multiple dashes with pause
    cleaned = re.sub(r'[-]{2,}', ', ', cleaned)
    
    # Clean up multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Clean up multiple periods (ellipsis)
    cleaned = re.sub(r'\.{3,}', '.', cleaned)
    
    # Remove extra commas
    cleaned = re.sub(r',+', ',', cleaned)
    
    # Trim whitespace
    cleaned = cleaned.strip()
    
    return cleaned