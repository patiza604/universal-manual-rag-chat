# Universal Customer Support RAG Training System

## 🚀 Quick Start

Process any manual for customer support chatbot optimization:

```bash
# Process your manual (works with ANY domain)
python scripts/generate_jsonl_enhanced.py templates/my_manual_content.md

# Results: 2-3x more chunks with customer support features
# - Auto-generated user questions
# - Difficulty assessment
# - Time estimates
# - Multi-level chunks (L0-L4)
# - Domain detection
```

## 📁 Directory Structure

```
training/
├── scripts/                           # Processing scripts
│   ├── generate_jsonl_enhanced.py     # Main entry point
│   ├── content_extractor.py           # Universal content extraction
│   ├── metadata_enhancer.py           # Customer support metadata
│   ├── chunking_orchestrator.py       # Multi-level coordination
│   └── semantic_chunker_enhanced.py   # Legacy chunking
├── config/                            # Configuration
│   └── manual_config.yaml             # Universal system settings
├── docs/                              # Documentation
│   └── UNIVERSAL_RAG_SYSTEM_GUIDE.md  # Complete guide
├── output/                            # Generated files
│   └── chunks/                        # Enhanced JSONL chunks
└── templates/                         # Manual templates
    └── my_manual_content.md           # Example manual
```

## 🎯 What This System Does

### Before
- 13 basic section chunks
- Manual-structured organization
- Technical language only

### After
- 34+ optimized chunks (2.6x improvement!)
- Customer support optimization
- 126+ auto-generated user questions
- Multi-level granularity (quick facts → detailed procedures)
- Domain-specific enhancements

## 🌍 Universal Compatibility

✅ **Electronics** (routers, devices, computers)
✅ **Automotive** (cars, trucks, equipment)
✅ **Software** (apps, websites, programs)
✅ **Appliances** (washers, dryers, etc.)
✅ **ANY Domain** (automatically adapts)

## 📚 Documentation

- **Quick Reference**: See main `CLAUDE.md`
- **Complete Guide**: `docs/UNIVERSAL_RAG_SYSTEM_GUIDE.md`
- **Configuration**: `config/manual_config.yaml`

## 🔧 Requirements

```bash
pip install PyYAML  # Configuration support
# All other dependencies in main requirements.txt
```

## 🎯 Key Features

- **Universal**: Works with any manual type
- **Intelligent**: LLM-powered content analysis
- **Customer-Oriented**: Generates realistic support questions
- **Configurable**: Domain-specific customization
- **Multi-Level**: Hierarchical chunk organization
- **Rich Metadata**: Time estimates, difficulty, escalation paths

---

*Transform any manual into an intelligent customer support knowledge base!*