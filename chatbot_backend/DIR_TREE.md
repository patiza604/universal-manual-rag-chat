# AI Assistant Platform - Directory Structure (Embedded FAISS)
# ============================================================================

chatbot_backend/
├── README.md
├── .env
├── requirements.txt
├── .python-version
├── runtime.txt
├── Procfile
├── main.py
│
├── app/
│   ├── __init__.py
│   ├── config.py                       # 🔄 Enhanced with new params
│   ├── startup.py                      # 🔄 Updated for new features
│   ├── faiss_vector_service.py         # 🔄 Enhanced metadata handling
│   └── vector-files/
│       ├── embeddings_enhanced.npy
│       ├── metadata_enhanced.pkl
│       └── index_to_id_enhanced.pkl
│
├── agent/
│   ├── __init__.py
│   ├── chat_manager.py                 # 🔄 Query classification added
│   ├── prompt.py
│   ├── embedding.py                    # 🔄 Multi-language support
│   └── retrieval.py                    # 🔄 Dynamic retrieval logic
│
├── api/
│   ├── __init__.py
│   ├── routes_chat.py
│   ├── routes_tts.py
│   ├── routes_stt.py
│   └── routes_debug.py                 # 🔄 Enhanced debugging
│
├── templates/                          # 🆕 Input templates
│   ├── manual_input_template.md        # 🆕 Markdown template
│   ├── maintenance_guide_template.md   # 🆕 Maintenance template
│   └── faq_template.md                 # 🆕 FAQ template
│
├── training/
│   ├── input/                          # 🆕 Raw documents
│   │   ├── raw_docs/                   # 🆕 Source documents
│   │   └── processed_templates/        # 🆕 Filled templates
│   ├── output/                         # 🆕 Generated content
│   │   ├── chunks/                     # 🆕 JSONL files
│   │   │   ├── manual_chunks.jsonl
│   │   │   ├── maintenance_chunks.jsonl
│   │   │   └── combined_chunks.jsonl
│   │   └── vectors/                    # 🆕 FAISS vectors
│   │       ├── embeddings.npy
│   │       ├── metadata.pkl
│   │       └── index_to_id.pkl
│   └── scripts/                        # 🆕 Automation scripts
│       ├── generate_jsonl.py           # 🆕 Template processor
│       ├── prepare_vectors_faiss.py    # 🔄 Enhanced version
│       ├── validate_chunks.py          # 🆕 Quality assurance
│       └── semantic_chunker.py         # 🆕 Smart text splitting
│
├── deployment/
│   ├── deploy_ai_service.ps1
│   ├── test_ai_service.py
│   └── update_vectors.ps1
│
├── gcp-keys/
│   └── 
│
└── docs/
    ├── API.md
    ├── DEPLOYMENT.md
    ├── VECTOR_MANAGEMENT.md
    └── TROUBLESHOOTING.md