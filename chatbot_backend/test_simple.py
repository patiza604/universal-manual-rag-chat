#!/usr/bin/env python3
"""
Simple test of enhanced customer support RAG system
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.faiss_vector_service import EnhancedFAISSVectorService
from app.config import LOCAL_VECTOR_FILES_PATH

def test_enhanced_system():
    """Test the enhanced customer support system"""
    print("Testing Enhanced Customer Support RAG System")
    print("=" * 50)

    # Initialize FAISS service
    faiss_service = EnhancedFAISSVectorService(
        vector_files_path=LOCAL_VECTOR_FILES_PATH,
        embeddings_file="embeddings_enhanced.npy",
        metadata_file="metadata_enhanced.pkl",
        id_map_file="index_to_id_enhanced.pkl"
    )

    print("Loading enhanced FAISS index...")
    if not faiss_service.load_index():
        print("ERROR: Failed to load FAISS index")
        return False

    print(f"SUCCESS: Loaded {faiss_service.faiss_index.ntotal} vectors")

    # Test query classification
    print("\n1. Testing Query Classification:")
    test_queries = {
        "What does red LED mean?": "quick_facts",
        "WiFi not working": "troubleshooting",
        "How to setup router": "setup",
        "Router problems": "progressive"
    }

    for query, expected in test_queries.items():
        classified = faiss_service.classify_query_from_text(query)
        status = "PASS" if classified == expected else "FAIL"
        print(f"  {status}: '{query}' -> {classified} (expected {expected})")

    # Test level-aware search
    print("\n2. Testing Level-Aware Search:")

    # Create a simple embedding for testing (random vector)
    import random
    test_embedding = [random.random() for _ in range(768)]

    # Test different search strategies
    strategies = ["quick_facts", "troubleshooting", "setup", "progressive"]

    for strategy in strategies:
        print(f"\n  Testing {strategy} strategy:")
        start_time = time.time()

        results = faiss_service.search_level_aware(
            query_embedding=test_embedding,
            query_type=strategy,
            max_results=3
        )

        search_time = time.time() - start_time

        if results:
            levels_found = set(r.get('level', 'unknown') for r in results)
            print(f"    Results: {len(results)} chunks from levels {sorted(levels_found)}")
            print(f"    Response time: {search_time:.3f}s")

            # Show level distribution
            for result in results:
                level = result.get('level', '?')
                title = result.get('title', 'Unknown')[:40]
                category = result.get('support_category', 'unknown')
                print(f"      [{level}] {title}... ({category})")
        else:
            print(f"    No results found")

    # Test health check
    print("\n3. Testing System Health:")
    health = faiss_service.health_check()
    print(f"  Status: {health.get('status', 'unknown')}")
    print(f"  Total vectors: {health.get('total_vectors', 0)}")
    print(f"  Total sections: {health.get('total_sections', 0)}")
    print(f"  Features: {health.get('features', {})}")

    print("\n4. Testing Customer Support Metadata:")
    # Check if enhanced metadata is present
    if faiss_service.metadata and len(faiss_service.metadata) > 0:
        sample_metadata = faiss_service.metadata[0]

        # Check for customer support fields
        cs_fields = [
            'user_questions', 'difficulty_level', 'support_category',
            'domain_category', 'search_weight', 'escalation_path'
        ]

        present_fields = [field for field in cs_fields if field in sample_metadata]
        print(f"  Customer support fields present: {len(present_fields)}/{len(cs_fields)}")

        for field in present_fields:
            value = sample_metadata.get(field)
            print(f"    {field}: {value}")

    print("\nSUCCESS: Enhanced Customer Support RAG System test completed!")
    return True

if __name__ == "__main__":
    try:
        success = test_enhanced_system()
        exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: Test failed: {e}")
        exit(1)