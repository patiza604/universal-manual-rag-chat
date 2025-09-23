import time
import random
from typing import List
from vertexai.language_models import TextEmbeddingInput
from google.api_core import exceptions as gcp_exceptions

def get_query_embedding(embedding_model, query_text: str, max_retries: int = 3) -> List[float]:
    """Generates an embedding for a user query with retry logic."""
    print(f"DEBUG: Generating embedding for query: '{query_text[:100]}...'")
    
    for attempt in range(max_retries):
        try:
            response = embedding_model.get_embeddings([TextEmbeddingInput(query_text)])
            embedding_values = response[0].values
            print(f"DEBUG: Query embedding generated (first 5 values): {embedding_values[:5]}...")
            return embedding_values
        except gcp_exceptions.InternalServerError as e:
            print(f"WARNING: Internal server error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"DEBUG: Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                print(f"ERROR: Failed to embed query after {max_retries} attempts")
                return None
        except Exception as e:
            print(f"ERROR: Failed to embed query: {e}")
            return None
    
    return None

def get_embedding_model():
    from vertexai.language_models import TextEmbeddingModel
    return TextEmbeddingModel.from_pretrained("text-embedding-004")
