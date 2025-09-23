---
name: Enhanced RAG System Issue
about: Report issues with the Universal Customer Support RAG System
title: '[RAG] '
labels: 'rag-system'
assignees: ''

---

**RAG System Component**
- [ ] Query Classification (75% accuracy target)
- [ ] Level-Aware Search (L0-L4 hierarchy)
- [ ] Multi-Embedding System
- [ ] Search Strategies (quick_facts, troubleshooting, setup, progressive)
- [ ] Vector Processing
- [ ] Manual Content Processing
- [ ] Performance (<1ms target)

**Issue Description**
A clear and concise description of the RAG system issue.

**Query Information**
- **Query text**: "..."
- **Expected search strategy**: [quick_facts/troubleshooting/setup/progressive]
- **Expected chunk levels**: [L0, L1, L2, QA, L3, L4]
- **Actual behavior**:

**Performance Metrics**
- **Search response time**: ___ms
- **Number of relevant chunks returned**: ___
- **Classification accuracy**: ___%

**Manual Content**
- **Manual domain**: [Electronics/Software/Automotive/Other]
- **Manual sections affected**:
- **Chunk hierarchy issues**:

**Environment**
- **Vector files version**:
- **FAISS index size**:
- **Embeddings model**: [text-embedding-004/other]
- **Python version**:

**Expected vs Actual Results**
**Expected:**
- Search strategy:
- Chunk levels:
- Response time:
- Accuracy:

**Actual:**
- Search strategy:
- Chunk levels:
- Response time:
- Accuracy:

**Testing Commands**
```bash
# Commands used to reproduce the issue
python test_simple.py
# or
curl -X POST "http://localhost:8080/chat/send" -H "Content-Type: application/json" -d '{"message": "your query"}'
```

**Additional Context**
Add any other context about the RAG system issue here.

**Debug Information**
```
Paste any relevant debug output from /debug/faiss-status or logs
```