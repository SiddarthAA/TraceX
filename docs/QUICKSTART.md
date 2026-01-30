# TraceX - Quick Start Guide

## Installation

### 1. Install dependencies using uv

```bash
uv pip install -e .
```

### 2. Set up API keys

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
GEMINI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

For Ollama (local models), make sure Ollama is running:
```bash
ollama serve
```

### 3. Generate sample data (optional)

```bash
python generate_samples.py
```

This creates sample HLR and LLR files in the `sample_data/` directory.

## Running the Application

Start the Streamlit UI:
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage Workflow

### Step 1: Configure Models (Sidebar)

1. **Structured Extraction Model**: Choose a model for extracting structured data
   - Recommended: Gemini 2.0 Flash (fast, accurate for structured output)
   - Alternative: GPT-4o, Claude 3.5 Sonnet

2. **Reasoning Model**: Choose a model for link reasoning
   - Recommended: Claude 3.5 Sonnet (excellent reasoning)
   - Alternative: GPT-4o, Gemini 1.5 Pro

3. **Top-K Candidates**: Number of candidate links per HLR (default: 10)

### Step 2: Load Requirements

**Tab 1: Load Requirements**

Option A: Use sample data
- Click "Use Sample Data"
- Click "Load Sample Requirements"

Option B: Upload your own files
- Prepare CSV files or Excel workbook
- Upload HLRs and LLRs
- Click "Load Requirements"

### Step 3: Generate Traceability

**Tab 2: Generate Traceability**

1. Click "🚀 Generate Traceability Matrix"
2. Wait for the process to complete (this may take a few minutes depending on the number of requirements)
3. View the summary metrics

### Step 4: Explore Results

**Tab 3: Traceability Matrix**

View modes:
- **Links List**: All traceability links with explanations
- **By HLR**: See which LLRs implement each HLR
- **By LLR**: See which HLRs each LLR contributes to
- **Pivot Table**: Traditional matrix view

Export: Click "📥 Export Traceability Matrix" to download Excel report

**Tab 4: Gap Analysis**

View:
- Orphan HLRs (no implementing LLRs)
- Orphan LLRs (not traced to HLRs)
- Partial coverage HLRs
- Coverage percentage

## Input File Format

### HLRs CSV/Excel

Required columns:
```
id,title,description,type,safety_level
HLR-001,System Stability,The system shall maintain stability,functional,DAL-B
```

### LLRs CSV/Excel

Required columns:
```
id,title,description,type,component,safety_level
LLR-001,Actuator Response,The actuator shall respond within 30ms,performance,Actuator,DAL-B
```

### Supported Types

- **Requirement Types**: functional, performance, safety, interface, diagnostic, other
- **Safety Levels**: DAL-A, DAL-B, DAL-C, DAL-D, ASIL-A, ASIL-B, ASIL-C, ASIL-D, QM, not_specified

## Model Recommendations

### For Speed (Fast iteration)
- Structured: Gemini 2.0 Flash
- Reasoning: Gemini 2.0 Flash
- Or use Ollama with local models

### For Quality (Best results)
- Structured: GPT-4o or Gemini 2.0 Flash
- Reasoning: Claude 3.5 Sonnet or GPT-4o

### For Cost (Minimal cost)
- Structured: Gemini 1.5 Flash or Groq
- Reasoning: Groq (llama-3.3-70b-versatile)

### For Privacy (Local-only)
- Structured: Ollama (llama3.2)
- Reasoning: Ollama (llama3.2 or llama3.1)

## Troubleshooting

### API Key Issues
- Make sure `.env` file exists in the project root
- Check that API keys are valid and have sufficient credits
- For Gemini: Get key from https://aistudio.google.com/apikey
- For Claude: Get key from https://console.anthropic.com/
- For OpenAI: Get key from https://platform.openai.com/
- For Groq: Get key from https://console.groq.com/

### Ollama Connection Issues
- Ensure Ollama is installed: `curl -fsSL https://ollama.com/install.sh | sh`
- Start Ollama: `ollama serve`
- Pull models: `ollama pull llama3.2`

### Memory Issues
- Reduce Top-K candidates to 5
- Process requirements in smaller batches
- Use smaller models (Gemini Flash, Groq)

### Slow Performance
- Use faster models (Gemini 2.0 Flash, Groq)
- Reduce Top-K candidates
- Use local embeddings are cached after first run

## Advanced Configuration

### Custom Embedding Models

Edit `src/candidate_generator.py`:
```python
CandidateLinkGenerator(embedding_model="your-model-name")
```

Supported models: any sentence-transformers model from HuggingFace

### Adjusting Confidence Thresholds

Edit `src/reasoning_engine.py`, line ~98:
```python
if link.confidence >= 0.3:  # Change this threshold
```

### Custom Ontology/Tags

Add domain-specific tags in `src/understanding_layer.py` to improve matching

## Support

For issues and questions:
- Check the README.md
- Review sample data format
- Ensure API keys are properly configured
