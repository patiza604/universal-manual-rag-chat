# check_vectors.py
import numpy as np
import pickle
import os

vector_path = os.path.join(os.path.dirname(__file__), "..", "app", "vector-files")
vector_path = os.path.abspath(vector_path)

# Load and check embeddings
embeddings_file = os.path.join(vector_path, "embeddings_enhanced.npy")
embeddings = np.load(embeddings_file)
print(f"✅ Embeddings shape: {embeddings.shape}")

# Load and check metadata
metadata_file = os.path.join(vector_path, "metadata_enhanced.pkl")
with open(metadata_file, 'rb') as f:
    metadata = pickle.load(f)

print(f"✅ Metadata entries: {len(metadata)}")

# Show first few entries
print("\n📄 First 3 metadata entries:")
for i, meta in enumerate(metadata[:3]):
    if isinstance(meta, dict):
        print(f"\nEntry {i}:")
        print(f"  Title: {meta.get('title', 'N/A')}")
        print(f"  Content preview: {meta.get('content', meta.get('original_text_chunk', ''))[:100]}...")
        print(f"  Source type: {meta.get('source_type', 'N/A')}")
        print(f"  Section ID: {meta.get('section_id', 'N/A')}")

# Search for pump mentions
print("\n🔍 Searching for 'pump' in metadata:")
pump = False
for i, meta in enumerate(metadata):
    if isinstance(meta, dict):
        content = str(meta.get('content', '')) + str(meta.get('original_text_chunk', ''))
        if 'pump' in content.lower():
            print(f"  Found in entry {i}: {meta.get('title', 'N/A')} - {meta.get('section_id', 'N/A')}")
            pump = True

if not pump:
    print("  ❌ No 'pump' mentions found in metadata!")