# 🚀 TraceX Command Reference

Complete guide to running TraceX with examples.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Web UI Commands](#web-ui-commands)
3. [CLI Commands](#cli-commands)
4. [Utility Commands](#utility-commands)
5. [Real-World Examples](#real-world-examples)
6. [Output Explanation](#output-explanation)

---

## Quick Start

### First Time Setup

```bash
# 1. Setup environment
./run.sh setup

# 2. Edit .env file with your API keys
nano .env

# 3. Generate sample data
./run.sh samples

# 4. Run tests
./run.sh test

# 5. Try sample data
./run.sh cli --sample
```

---

## Web UI Commands

### Launch Web Interface

```bash
./run.sh              # Default: launches UI
# or
./run.sh ui           # Explicit
```

**What happens**:
- Streamlit server starts on `http://localhost:8501`
- Browser opens automatically
- Interactive web interface loads

**When to use**:
- ✅ First time users
- ✅ Visual exploration of results
- ✅ Interactive configuration
- ✅ Quick experiments

---

## CLI Commands

### Basic Syntax

```bash
./run.sh cli [options]
# or direct:
uv run python tracex_cli.py run [options]
```

### 📊 Sample Data (Quick Test)

```bash
# Minimal command (uses Gemini for both models)
./run.sh cli --sample

# With specific models
./run.sh cli --sample \
    --struct-provider gemini --struct-model gemini-2.0-flash-exp \
    --reason-provider claude --reason-model claude-3-5-sonnet-20241022
```

**Input**: Built-in sample data (5 HLRs, 10 LLRs)  
**Output**: `data/output/traceability_matrix_YYYYMMDD_HHMMSS.xlsx`  
**Time**: ~7-10 minutes

---

### 📁 CSV Files

```bash
# Basic usage
./run.sh cli \
    --hlr-csv data/input/my_hlrs.csv \
    --llr-csv data/input/my_llrs.csv

# With custom models
./run.sh cli \
    --hlr-csv data/input/project_hlrs.csv \
    --llr-csv data/input/project_llrs.csv \
    --struct-provider gemini \
    --reason-provider claude

# Full control
./run.sh cli \
    --hlr-csv data/input/aerospace_hlrs.csv \
    --llr-csv data/input/aerospace_llrs.csv \
    --struct-provider gpt --struct-model gpt-4o \
    --reason-provider claude --reason-model claude-3-5-sonnet-20241022 \
    --top-k 15 \
    --output data/output/aerospace_project
```

**Input**: Two CSV files (HLRs and LLRs)  
**Output**: Excel file in specified output directory  

---

### 📊 Excel File

```bash
# Default sheet names (HLRs, LLRs)
./run.sh cli --excel data/input/requirements.xlsx

# Custom sheet names
./run.sh cli --excel data/input/project_reqs.xlsx \
    --hlr-sheet "High-Level" \
    --llr-sheet "Low-Level"

# With specific models
./run.sh cli --excel data/input/requirements.xlsx \
    --struct-provider gemini --struct-model gemini-2.0-flash-exp \
    --reason-provider gpt --reason-model gpt-4o
```

**Input**: Single Excel file with multiple sheets  
**Output**: Excel traceability matrix  

---

### 🤖 Model Selection

#### Available Providers

```bash
# Gemini (Google) - Fast, good for structured output
./run.sh cli --sample \
    --struct-provider gemini --struct-model gemini-2.0-flash-exp \
    --reason-provider gemini --reason-model gemini-1.5-pro

# Claude (Anthropic) - Best reasoning
./run.sh cli --sample \
    --struct-provider claude --struct-model claude-3-5-sonnet-20241022 \
    --reason-provider claude --reason-model claude-3-5-sonnet-20241022

# GPT (OpenAI) - Reliable, well-tested
./run.sh cli --sample \
    --struct-provider gpt --struct-model gpt-4o \
    --reason-provider gpt --reason-model gpt-4o

# Groq (Fast inference) - Low cost, high speed
./run.sh cli --sample \
    --struct-provider groq --struct-model llama-3.3-70b-versatile \
    --reason-provider groq --reason-model llama-3.3-70b-versatile

# Ollama (Local) - Privacy, offline
./run.sh cli --sample \
    --struct-provider ollama --struct-model llama3.2 \
    --reason-provider ollama --reason-model llama3.2
```

#### Model Combinations (Recommended)

```bash
# Best Quality (slower, more expensive)
./run.sh cli --sample \
    --struct-provider gpt --struct-model gpt-4o \
    --reason-provider claude --reason-model claude-3-5-sonnet-20241022

# Best Speed (faster, good quality)
./run.sh cli --sample \
    --struct-provider gemini --struct-model gemini-2.0-flash-exp \
    --reason-provider gemini --reason-model gemini-2.0-flash-exp

# Best Cost (cheapest, good quality)
./run.sh cli --sample \
    --struct-provider groq --struct-model llama-3.3-70b-versatile \
    --reason-provider groq --reason-model llama-3.3-70b-versatile

# Privacy/Offline (fully local, no API)
./run.sh cli --sample \
    --struct-provider ollama --struct-model llama3.2 \
    --reason-provider ollama --reason-model llama3.2
```

---

### ⚙️ Advanced Options

```bash
# Custom Top-K candidates (default: 10)
./run.sh cli --sample --top-k 15

# Custom output directory
./run.sh cli --sample --output results/phase1

# Combine all options
./run.sh cli \
    --hlr-csv data/input/hlrs.csv \
    --llr-csv data/input/llrs.csv \
    --struct-provider gemini --struct-model gemini-2.0-flash-exp \
    --reason-provider claude --reason-model claude-3-5-sonnet-20241022 \
    --top-k 12 \
    --output data/output/final_analysis
```

---

## Utility Commands

### Generate Sample Data

```bash
./run.sh samples
```

**Output**:
```
data/samples/
├── sample_hlrs.csv              (5 HLRs)
├── sample_llrs.csv              (10 LLRs)
└── sample_requirements.xlsx     (Combined)
```

### Run System Tests

```bash
./run.sh test
```

**Tests**:
- ✅ All imports work
- ✅ Sample data loads
- ✅ CSV/Excel loading
- ✅ Embeddings generate
- ✅ System initializes

### List Available Models

```bash
uv run python tracex_cli.py list-models
```

**Shows**: All providers and their available models

### Show Help

```bash
./run.sh help
# or
./run.sh cli --help
```

---

## Real-World Examples

### Example 1: Aerospace Project (DO-178C)

```bash
# Input files:
# - data/input/flight_control_hlrs.csv (25 HLRs)
# - data/input/flight_control_llrs.csv (120 LLRs)

./run.sh cli \
    --hlr-csv data/input/flight_control_hlrs.csv \
    --llr-csv data/input/flight_control_llrs.csv \
    --struct-provider gemini --struct-model gemini-2.0-flash-exp \
    --reason-provider claude --reason-model claude-3-5-sonnet-20241022 \
    --top-k 12 \
    --output data/output/flight_control_v1

# Time: ~20-30 minutes
# Output: data/output/flight_control_v1/traceability_matrix_*.xlsx
```

### Example 2: Automotive Project (ISO 26262)

```bash
# Input: Single Excel file with HLRs and LLRs sheets

./run.sh cli \
    --excel data/input/adas_requirements.xlsx \
    --hlr-sheet "System_Requirements" \
    --llr-sheet "Software_Requirements" \
    --struct-provider gpt --struct-model gpt-4o \
    --reason-provider gpt --reason-model gpt-4o \
    --top-k 10 \
    --output data/output/adas_analysis

# Time: ~15-25 minutes
# Output: data/output/adas_analysis/traceability_matrix_*.xlsx
```

### Example 3: Medical Device (IEC 62304)

```bash
# Using local models for privacy (HIPAA compliance)

./run.sh cli \
    --excel data/input/medical_device_reqs.xlsx \
    --struct-provider ollama --struct-model llama3.2 \
    --reason-provider ollama --reason-model llama3.1 \
    --top-k 8 \
    --output data/output/medical_device

# Time: ~30-45 minutes (local models slower)
# Output: Fully private, no data leaves your machine
```

### Example 4: Quick Iteration (Development)

```bash
# Fast turnaround for development

./run.sh cli --sample \
    --struct-provider gemini --struct-model gemini-2.0-flash-exp \
    --reason-provider gemini --reason-model gemini-2.0-flash-exp \
    --top-k 5

# Time: ~5-8 minutes
# Use for: Testing changes, quick validation
```

---

## Output Explanation

### Console Output

```
======================================================================
🔗 TraceX - HLR-LLR Requirements Traceability System
   AI-Powered Requirements Mapping with Explainable Reasoning
======================================================================

📥 Loading requirements...
   Using built-in sample data
✅ Loaded 5 HLRs and 10 LLRs

🤖 Initializing AI models...
   Structured Model: gemini/gemini-2.0-flash-exp
   Reasoning Model: claude/claude-3-5-sonnet-20241022
✅ Models initialized

🔧 Initializing traceability system...
✅ System ready

======================================================================
Step 1/3: Understanding Requirements
======================================================================
Understanding HLRs...
Understanding LLRs...
✅ Semantic understanding complete

======================================================================
Step 2/3: Generating Traceability Links
======================================================================

=== Step 1: Generating Candidate Links ===
Generating embeddings...
Building BM25 index...
Generated 50 candidate links

=== Step 2: Evaluating Candidates with Reasoning ===
Evaluated 50 links

=== Step 3: Generating Traceability Matrix ===
Final matrix: 15 accepted links
Coverage: 85.7%

======================================================================
Step 3/3: Saving Results
======================================================================
💾 Saving to: data/output/traceability_matrix_20260126_143022.xlsx
✅ Export complete

======================================================================
📊 SUMMARY
======================================================================
Total HLRs:           5
Total LLRs:           10
Traceability Links:   15
Coverage:             85.7%
Orphan HLRs:          1
Orphan LLRs:          2
Partial Coverage:     3

⚠️  WARNING: Orphan HLRs detected (not implemented):
   - HLR-005

✅ Results saved to: data/output/traceability_matrix_20260126_143022.xlsx
======================================================================
```

### Output Excel File

**File**: `data/output/traceability_matrix_YYYYMMDD_HHMMSS.xlsx`

**Sheets**:

1. **Traceability Links**
   - All HLR↔LLR mappings
   - Link type (Supports, Implements, Contributes)
   - Coverage (Full, Partial)
   - Confidence scores
   - Full explanations

2. **Summary**
   - Total counts
   - Coverage percentage
   - Gap statistics

3. **Orphan HLRs** (if any)
   - HLRs with no implementing LLRs
   - ⚠️ Critical for certification

4. **Orphan LLRs** (if any)
   - LLRs not traced to any HLR
   - ℹ️ May indicate scope creep

---

## Performance Guidelines

### Typical Processing Times

| Requirements Count | Time (Fast Models) | Time (Quality Models) |
|-------------------|-------------------|----------------------|
| 5 HLRs, 10 LLRs | 5-8 min | 8-12 min |
| 20 HLRs, 80 LLRs | 15-20 min | 25-35 min |
| 50 HLRs, 200 LLRs | 30-45 min | 60-90 min |
| 100 HLRs, 400 LLRs | 60-90 min | 120-180 min |

**Fast Models**: Gemini 2.0 Flash, Groq  
**Quality Models**: Claude 3.5 Sonnet, GPT-4o

### Cost Estimates

**API-based** (per 100 requirements):
- Gemini: ~$0.20-0.50
- Groq: ~$0.10-0.30 (or free tier)
- GPT-4o: ~$1.00-2.00
- Claude: ~$1.50-3.00

**Ollama**: Free (local compute only)

---

## Troubleshooting

### Command Not Found
```bash
# Make run.sh executable
chmod +x run.sh
```

### API Key Errors
```bash
# Check .env exists
ls -la .env

# Verify format (no quotes)
cat .env
# Should show: GEMINI_API_KEY=your_key_here
```

### Ollama Connection Failed
```bash
# Start Ollama
ollama serve

# Pull model
ollama pull llama3.2

# Test connection
curl http://localhost:11434/api/tags
```

### Out of Memory
```bash
# Use smaller top-k
./run.sh cli --sample --top-k 5

# Use faster/smaller models
./run.sh cli --sample \
    --struct-provider gemini --struct-model gemini-2.0-flash-exp
```

---

## 📚 See Also

- [Input Format Guide](../data/input/README.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [Quick Start Guide](QUICKSTART.md)
