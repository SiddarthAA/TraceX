# 📁 TraceX - Organized Project Structure

```
tracex/
│
├── 📄 README.md                    # Main documentation
├── 📄 pyproject.toml                # Python dependencies
├── 📄 uv.lock                       # Locked dependencies
├── 📄 .gitignore                    # Git ignore rules
├── 📄 run.sh                        # Main launcher script
├── 📄 app.py                        # Streamlit web UI
├── 📄 tracex_cli.py                 # Command-line interface
│
├── 📂 src/                          # Core system code
│   ├── __init__.py
│   ├── models.py                    # Data models (Pydantic)
│   ├── model_provider.py            # Multi-LLM abstraction
│   ├── requirements_loader.py       # File ingestion
│   ├── understanding_layer.py       # Semantic extraction
│   ├── candidate_generator.py       # Link candidates (embeddings + BM25)
│   ├── reasoning_engine.py          # AI reasoning (CORE LOGIC)
│   ├── matrix_generator.py          # Report generation
│   └── traceability_system.py       # Main orchestrator
│
├── 📂 config/                       # Configuration files
│   └── .env.example                 # API keys template
│
├── 📂 data/                         # All data files
│   ├── input/                       # Your input requirements
│   │   ├── README.md               # Input format guide
│   │   └── (place your CSV/Excel files here)
│   │
│   ├── output/                      # Generated traceability matrices
│   │   └── (Excel reports saved here)
│   │
│   └── samples/                     # Sample/demo data
│       ├── sample_hlrs.csv
│       ├── sample_llrs.csv
│       └── sample_requirements.xlsx
│
├── 📂 scripts/                      # Utility scripts
│   └── generate_samples.py          # Generate demo data
│
├── 📂 tests/                        # Test files
│   └── test_system.py               # System verification
│
├── 📂 docs/                         # Documentation
│   ├── QUICKSTART.md                # Getting started guide
│   ├── ARCHITECTURE.md              # Technical architecture
│   └── IMPLEMENTATION_SUMMARY.md    # What was built
│
└── 📂 logs/                         # Application logs (future)
    └── (log files)
```

## 📂 Directory Purposes

### `/src` - Core System
The heart of the traceability system. All AI logic, reasoning, and processing happens here.

### `/config` - Configuration
Environment-specific settings, API keys, model configurations.

### `/data` - All Data Files
- **`/data/input/`** - Put your requirement files here
- **`/data/output/`** - Traceability matrices saved here
- **`/data/samples/`** - Demo data for testing

### `/scripts` - Utilities
Helper scripts for data generation, maintenance, etc.

### `/tests` - Testing
System tests and validation scripts.

### `/docs` - Documentation
Detailed guides and architecture documentation.

### `/logs` - Logs
Application logs (currently unused, available for future logging).

## 🎯 Key Files

| File | Purpose |
|------|---------|
| `run.sh` | Main entry point - launches UI or CLI |
| `app.py` | Streamlit web interface |
| `tracex_cli.py` | Command-line interface |
| `src/reasoning_engine.py` | **Core AI logic** - where links are evaluated |
| `src/traceability_system.py` | Orchestrates the entire pipeline |
| `pyproject.toml` | Dependencies and project metadata |

## 📋 File Naming Conventions

### Input Files
```
data/input/
├── my_project_hlrs.csv           # High-level requirements
├── my_project_llrs.csv           # Low-level requirements
└── my_project_requirements.xlsx  # Combined Excel file
```

### Output Files
```
data/output/
├── traceability_matrix_20260126_143022.xlsx   # Timestamped
├── traceability_matrix_20260126_151445.xlsx   # Multiple runs
└── ...
```

## 🔄 Data Flow

```
data/input/              src/                data/output/
    *.csv        →    Processing      →    *_matrix.xlsx
    *.xlsx             (AI + Rules)         (Report)
```

---

This structure separates concerns cleanly:
- **Code** stays in `/src`
- **Data** stays in `/data`
- **Docs** stay in `/docs`
- **Tests** stay in `/tests`

Easy to navigate, maintain, and scale!
