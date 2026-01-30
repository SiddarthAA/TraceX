# 🔗 TraceX - HLR-LLR Traceability System

> *AI-powered requirements traceability with explainable reasoning for safety-critical systems*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.53+-red.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive requirements traceability system for mapping High-Level Requirements (HLRs) to Low-Level Requirements (LLRs) with explainable AI reasoning. Built for **DO-178C**, **ISO 26262**, and **IEC 62304** compliance.

## ✨ Features

- 🧠 **Intelligent Understanding**: Extract structured meaning from natural language requirements
- 🔍 **Multi-Method Retrieval**: Combines semantic embeddings (transformers) + lexical search (BM25)
- 🤔 **Explainable Reasoning**: Multi-dimensional AI reasoning (not just similarity)
- ✅ **Rule-Based Validation**: Type compatibility, safety level consistency checks
- 📊 **Gap Analysis**: Identify orphan requirements and coverage gaps
- 📋 **Audit-Ready Output**: Traceability matrix with explanations for every link
- 🔌 **Model Agnostic**: Support for Gemini, Claude, GPT, Groq, and Ollama
- 🎨 **Clean UI**: Streamlit-based interface for easy interaction

## 🏗️ Architecture

```
Requirements Ingestion
        ↓
Requirement Understanding (Structured Extraction)
        ↓
Candidate Link Generation (Embeddings + BM25)
        ↓
Link Reasoning Engine (Multi-Dimensional AI Reasoning)
        ↓
Explainability Engine
        ↓
Traceability Matrix + Gap Reports
```

**Key Differentiator**: This system doesn't just find "similar" requirements—it reasons about *causal relationships* and *implementation dependencies* with explainable logic.

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical documentation.

## 🚀 Quick Start

### Installation

```bash
# Install dependencies using uv
uv pip install -e .

# Copy environment template
cp .env.example .env

# Add your API keys to .env (or use Ollama for local models)
```

### Run the Application

```bash
# Quick start
./run.sh

# Or manually
uv run streamlit run app.py
```

### First Time Setup

1. **Configure Models** (sidebar)
   - Choose structured extraction model (e.g., Gemini 2.0 Flash)
   - Choose reasoning model (e.g., Claude 3.5 Sonnet)

2. **Load Requirements** (Tab 1)
   - Click "Use Sample Data" → "Load Sample Requirements"
   - Or upload your own CSV/Excel files

3. **Generate Traceability** (Tab 2)
   - Click "🚀 Generate Traceability Matrix"
   - Wait 5-10 minutes for processing

4. **Explore Results** (Tabs 3-4)
   - View links with explanations
   - Check gap analysis
   - Export to Excel

See [QUICKSTART.md](QUICKSTART.md) for detailed guide.

## 💡 Why TraceX?

### The Problem with Traditional Approaches

Most traceability tools use simple similarity matching:
```
"Find the most similar LLR for this HLR"
```

This fails because:
- ❌ Doesn't understand **causal relationships**
- ❌ Can't explain **why** requirements are linked
- ❌ Misses **many-to-many** relationships
- ❌ No validation of **safety level consistency**
- ❌ Can't detect **gaps** in coverage

### TraceX's Approach

```
"Which set of LLRs together provide evidence that this HLR is implemented—and why?"
```

TraceX uses:
- ✅ **Structured understanding** of requirement semantics
- ✅ **Multi-dimensional reasoning** (intent, causality, type, safety)
- ✅ **Explainable decisions** with human-readable justifications
- ✅ **Rule-based validation** for compliance
- ✅ **Gap detection** and coverage analysis

### Real Example

**HLR-001**: *"The flight control system shall maintain pitch stability"*

**Traditional tool might link to**:
- LLR-088 (Flight data logging) ← Wrong! Just similar words

**TraceX correctly links to**:
1. LLR-001 (Elevator actuator response time) - **Partial Coverage**
2. LLR-002 (Control law update rate) - **Partial Coverage**  
3. LLR-003 (IMU pitch rate latency) - **Partial Coverage**

**With explanation**:
```
Pitch stability requires a closed control loop:
  Sensor (LLR-003) → Control Law (LLR-002) → Actuator (LLR-001)
  
Each LLR contributes partial coverage. Together they implement HLR-001.
Safety levels compatible (all DAL-B).
```

This is **certification-grade** traceability.

## 📊 Output Example

### Traceability Link

```
HLR-001 → LLR-002 (LINKED - Partial Coverage)

Intent Alignment:
  Maintaining pitch stability requires timely control law updates.
  LLR-002 ensures 100Hz update rate supporting stability.

Conceptual Chain:
  Pitch Stability (system property)
    → requires Control Loop execution
    → requires Fast Control Law Updates (LLR-002)

Type Compatibility:
  Functional HLR + Performance LLR = Compatible
  Performance constraint enables functional requirement

Safety Consistency:
  Both DAL-B - Compatible

Coverage Logic:
  LLR-002 is necessary but not sufficient alone.
  Forms control chain with sensor (LLR-003) and actuator (LLR-001).

Confidence: 0.87
```

### Gap Report

```
Coverage: 85.7% (6/7 HLRs traced)

Orphan HLRs (Critical):
  - HLR-005: Flight Mode Transitions (no implementing LLRs)

Partial Coverage (Review):
  - HLR-001: Pitch Stability (3 partial LLRs)
  - HLR-003: Sensor Processing (2 partial LLRs)

Orphan LLRs (Informational):
  - LLR-004: Flight Data Logging (not traced to HLR)
```

## 🎯 Supported Use Cases

- ✈️ **Aerospace**: DO-178C compliance (flight control, avionics)
- 🚗 **Automotive**: ISO 26262 functional safety (ADAS, powertrains)
- 🏥 **Medical Devices**: IEC 62304 software lifecycle
- 🏭 **Industrial**: IEC 61508 safety systems
- 🔒 **Any Safety-Critical Domain** requiring traceability

## 🔧 Configuration

### Model Selection

Choose separate models for different tasks:

**For Structured Extraction** (JSON output):
- **Recommended**: Gemini 2.0 Flash (fast, reliable)
- **Alternative**: GPT-4o, Claude 3.5 Sonnet

**For Reasoning** (explanations):
- **Recommended**: Claude 3.5 Sonnet (excellent reasoning)
- **Alternative**: GPT-4o, Gemini 1.5 Pro

**For Speed**: Gemini 2.0 Flash for both  
**For Quality**: GPT-4o + Claude 3.5 Sonnet  
**For Privacy**: Ollama (llama3.2) for both  
**For Cost**: Groq (free tier) for both  

### Supported Providers

| Provider | Models | Best For |
|----------|--------|----------|
| **Gemini** | 2.0-flash, 1.5-pro | Speed + Quality balance |
| **Claude** | 3.5-sonnet, 3.5-haiku | Best reasoning |
| **GPT** | gpt-4o, gpt-4o-mini | Reliable structured output |
| **Groq** | llama-3.3-70b | Fast inference, low cost |
| **Ollama** | llama3.2, mistral | Local/offline, privacy |

## Input Format

### Requirements CSV/Excel Format

**HLRs Sheet**:
```
id,title,description,type,safety_level
HLR-001,System Stability,The system shall maintain pitch stability,functional,DAL-B
```

**LLRs Sheet**:
```
id,title,description,type,component,safety_level
LLR-001,Actuator Response,The elevator actuator shall respond within 30ms,performance,Actuator,DAL-B
```

## Output

- Traceability Matrix (CSV/Excel)
- Link Explanations
- Gap Reports
- Coverage Analysis

## 📁 Organized Project Structure

```
tracex/
├── src/              → Core system (AI reasoning, embeddings, traceability)
├── data/
│   ├── input/        → PUT YOUR FILES HERE ⭐
│   ├── output/       → RESULTS APPEAR HERE ⭐
│   └── samples/      → Demo data
├── docs/             → Complete documentation
├── config/           → Configuration files
├── scripts/          → Utilities
├── tests/            → System tests
├── app.py            → Web UI
├── tracex_cli.py     → CLI interface
└── run.sh            → Main launcher ⭐
```

**See**: [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| [USAGE_GUIDE.md](USAGE_GUIDE.md) | **START HERE** - Complete usage guide with examples |
| [docs/COMMAND_REFERENCE.md](docs/COMMAND_REFERENCE.md) | All commands with real-world examples |
| [data/input/README.md](data/input/README.md) | Input file format specification |
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | Quick start tutorial |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Technical architecture deep-dive |
| [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | File organization explained |

## License

MIT
