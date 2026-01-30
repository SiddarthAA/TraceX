# TraceX - System Architecture

## Overview

TraceX is a comprehensive HLR-LLR (High-Level Requirements to Low-Level Requirements) traceability system that uses AI to intelligently map requirements with explainable reasoning.

## Design Principles

1. **Explainability First**: Every link decision must be explainable
2. **Multi-dimensional Reasoning**: Not just similarity, but causal reasoning
3. **Human-in-the-loop**: Designed for validation and audit
4. **Model Agnostic**: Works with any LLM provider
5. **Separation of Concerns**: Clean modular architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI (app.py)                     │
│  - Configuration                                             │
│  - Requirements Upload                                       │
│  - Matrix Visualization                                      │
│  - Gap Analysis                                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│          TraceabilitySystem (traceability_system.py)         │
│  - Orchestrates the entire pipeline                          │
│  - Manages state and workflow                                │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────────┐  ┌─────────────────┐
│  Requirement │  │  Candidate Link  │  │ Link Reasoning  │
│ Understanding│  │    Generator     │  │     Engine      │
│    Layer     │  │                  │  │                 │
└──────────────┘  └──────────────────┘  └─────────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
   Structured          Embeddings +         Multi-dim
   Extraction          BM25 Scoring         Reasoning
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  Traceability Matrix  │
                │      Generator        │
                └───────────────────────┘
                            │
                            ▼
                    Excel/CSV Export
```

## Component Details

### 1. Model Provider Layer (`model_provider.py`)

**Purpose**: Abstract interface for different LLM providers

**Supported Providers**:
- Google Gemini (gemini-2.0-flash-exp, gemini-1.5-pro)
- Anthropic Claude (claude-3-5-sonnet, claude-3-5-haiku)
- OpenAI GPT (gpt-4o, gpt-4o-mini)
- Groq (llama-3.3-70b-versatile)
- Ollama (local models)

**Key Methods**:
- `generate()`: Text completion
- `generate_structured()`: JSON-structured output

### 2. Requirements Loader (`requirements_loader.py`)

**Purpose**: Ingest requirements from various sources

**Capabilities**:
- Load from CSV (separate HLR/LLR files)
- Load from Excel (multiple sheets)
- Generate sample data for testing

**Input Schema**:
```python
{
    "id": "HLR-001",
    "title": "Pitch Stability",
    "description": "The system shall...",
    "type": "functional",
    "safety_level": "DAL-B",
    "component": "Control System"  # LLRs only
}
```

### 3. Requirement Understanding Layer (`understanding_layer.py`)

**Purpose**: Extract structured semantic meaning from natural language requirements

**Process**:
1. Parse requirement text
2. Extract using LLM with structured output:
   - Intent verb (what action)
   - Subject (who/what performs)
   - Object (what is acted upon)
   - Constraints (timing, range, accuracy)
   - Requirement type
   - Abstraction level
   - Key concepts

**Output**: `StructuredRequirement` object

**Why This Matters**: Enables explainable reasoning beyond just similarity

### 4. Candidate Link Generator (`candidate_generator.py`)

**Purpose**: Generate high-recall candidate links (over-generate on purpose)

**Methods**:
1. **Semantic Embeddings**
   - Model: sentence-transformers (all-MiniLM-L6-v2)
   - Cosine similarity between HLR and LLR embeddings
   - Fast, captures semantic meaning

2. **Lexical Retrieval (BM25)**
   - Classical information retrieval
   - Catches exact term matches embeddings might miss
   - Good for formal language in requirements

3. **Ontology/Tag Overlap**
   - Simple keyword matching
   - Can be extended with domain ontology

**Output**: Top-K candidates per HLR (default K=10)

**Design Choice**: High recall at this stage. Precision comes later.

### 5. Link Reasoning Engine (`reasoning_engine.py`)

**Purpose**: Make intelligent decisions about which links are valid

**Multi-Dimensional Evaluation**:

1. **Type Compatibility**
   - Rule-based check
   - Example: Functional HLR ❌ Diagnostic-only LLR

2. **Safety Level Consistency**
   - Safety hierarchy enforcement
   - Example: DAL-A HLR requires ≥ DAL-A LLR

3. **LLM Reasoning** (5 dimensions):
   - Intent Alignment: Does LLR action support HLR goal?
   - Conceptual Chain: Is there logical dependency?
   - Type Compatibility: Are types appropriate?
   - Safety Consistency: Are safety levels compatible?
   - Coverage Logic: Full vs partial contribution?

4. **Final Decision**:
   - ACCEPT: Full link
   - PARTIAL: Contributes but not complete
   - REJECT: Not linked

**Output**: `TraceabilityLink` with explanation

**Key Insight**: This is NOT just "best match" - it's causal reasoning about implementation relationships

### 6. Traceability Matrix Generator (`matrix_generator.py`)

**Purpose**: Create audit-ready documentation

**Outputs**:
1. **Traceability Matrix**
   - All accepted links
   - Explanations for each
   - Confidence scores

2. **Gap Report**
   - Orphan HLRs (not implemented)
   - Orphan LLRs (not traced)
   - Partial coverage HLRs
   - Coverage percentage

3. **Export Formats**
   - Excel workbook (multiple sheets)
   - Pivot table view
   - CSV

## Data Models (`models.py`)

### Core Models

```python
Requirement (base)
├── HLR (High-Level Requirement)
└── LLR (Low-Level Requirement)

StructuredRequirement
├── intent_verb
├── subject
├── object
├── constraint
├── requirement_type
├── abstraction_level
└── key_concepts[]

CandidateLink
├── hlr_id
├── llr_id
├── embedding_score
├── bm25_score
├── ontology_overlap[]
└── combined_score

TraceabilityLink
├── hlr_id
├── llr_id
├── link_type (enum)
├── coverage (enum)
├── confidence
├── explanation
├── reasoning_trace
└── accepted (bool)

TraceabilityMatrix
├── links[]
├── gap_report
└── metadata
```

## Workflow Pipeline

```
1. Load Requirements
   └─> Parse CSV/Excel
   └─> Create HLR/LLR objects

2. Understand Requirements (per requirement)
   └─> Call structured extraction model
   └─> Extract semantic structure
   └─> Store in StructuredRequirement

3. Generate Candidates (per HLR)
   └─> Generate embeddings (both HLR and LLRs)
   └─> Build BM25 index
   └─> Score all HLR-LLR pairs
   └─> Return top-K per HLR

4. Evaluate Links (per candidate)
   └─> Check type compatibility
   └─> Check safety compatibility
   └─> LLM multi-dimensional reasoning
   └─> Make decision (ACCEPT/PARTIAL/REJECT)
   └─> Generate explanation

5. Create Matrix
   └─> Filter to accepted links
   └─> Analyze gaps
   └─> Calculate metrics
   └─> Format for export
```

## Model Selection Strategy

### Two-Model Architecture

**Why separate models?**
- Structured extraction needs reliability and format adherence
- Reasoning needs depth and nuance
- Different models excel at different tasks
- Cost optimization

**Recommended Combinations**:

| Use Case | Structured Model | Reasoning Model | Why |
|----------|-----------------|-----------------|-----|
| Best Quality | GPT-4o | Claude 3.5 Sonnet | GPT-4o reliable for JSON, Claude best reasoning |
| Best Speed | Gemini 2.0 Flash | Gemini 2.0 Flash | Very fast, good quality |
| Best Cost | Groq Llama 3.3 | Groq Llama 3.3 | Fast inference, low cost |
| Privacy | Ollama | Ollama | Fully local |

## Explainability

Every link has:

```
HLR-014 → LLR-014.2 (LINKED)

Intent Alignment:
  Pitch stability requires timely actuator response

Conceptual Chain:
  Pitch stability → Control loop → Actuator latency
  LLR-014.2 constrains elevator response latency

Type Compatibility:
  Functional HLR + Performance LLR = Compatible

Safety Consistency:
  Both DAL-B = Compatible

Coverage:
  Partial - part of larger control chain

Confidence: 0.87
```

This is what auditors need to see.

## Gap Analysis

The system identifies:

1. **Orphan HLRs**: Requirements with no implementation
   - Critical for certification
   - Must be addressed before release

2. **Orphan LLRs**: Implementation not traced to requirements
   - May indicate scope creep
   - Or documentation gap

3. **Partial Coverage**: Requirements only partially implemented
   - Needs additional LLRs
   - Or may be acceptable

4. **Coverage Percentage**: Overall traceability health metric

## Extension Points

### Custom Ontology
Add domain-specific knowledge in `understanding_layer.py`:
```python
AVIATION_ONTOLOGY = {
    "pitch_stability": ["elevator", "control_law", "imu"],
    "safety": ["redundancy", "failsafe", "monitor"]
}
```

### Custom Rules
Add business rules in `reasoning_engine.py`:
```python
def _check_custom_rules(self, hlr, llr):
    # Your domain-specific logic
    pass
```

### Custom Embeddings
Use domain-specific embedding models:
```python
CandidateLinkGenerator(
    embedding_model="your-domain-specific-model"
)
```

## Performance Characteristics

**Small Projects** (< 50 HLRs, < 200 LLRs):
- Runtime: 5-10 minutes
- Memory: < 2GB
- Recommended: Gemini 2.0 Flash

**Medium Projects** (50-200 HLRs, 200-1000 LLRs):
- Runtime: 15-30 minutes
- Memory: 2-4GB
- Recommended: GPT-4o + Claude

**Large Projects** (> 200 HLRs):
- Consider batching
- Use local embeddings (cached)
- Parallelize where possible

## Security & Privacy

**API Keys**:
- Stored in `.env` (never committed)
- Loaded via python-dotenv
- Never logged or exposed

**Data Privacy**:
- Requirements stay on your machine
- Only sent to chosen LLM provider
- Use Ollama for fully local processing

**Audit Trail**:
- All decisions logged
- Reasoning traces preserved
- Human validation supported

## Limitations & Future Work

**Current Limitations**:
- English language only
- No incremental updates (full reprocessing)
- Limited ontology support
- No automated test generation

**Future Enhancements**:
- Incremental traceability updates
- Multi-language support
- Rich domain ontologies
- Automated test case generation from links
- Change impact analysis
- Integration with ALM tools (DOORS, Jira)

## References

**Standards Addressed**:
- DO-178C (Aviation software)
- ISO 26262 (Automotive safety)
- IEC 62304 (Medical device software)

**Key Concepts**:
- Requirements traceability
- Safety-critical systems
- Explainable AI
- Hybrid retrieval (semantic + lexical)
