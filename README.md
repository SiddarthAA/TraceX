# Aerospace Requirements Traceability Engine

A Comprehensive end-to-end requirements traceability system for aerospace applications. This system traces from system-level requirements down to code variables, identifies gaps, and provides LLM-powered reasoning for incomplete or missing links.

## Features

- ✈️ **Aerospace-Focused**: Built for DO-178C/ARP4754A compliance
- 🤖 **LLM-Powered**: Uses Groq API for requirement decomposition and gap analysis
- 🔍 **Hybrid Matching**: Combines embeddings, keyword matching, quantity matching, and variable name matching
- 📊 **Complete Analysis**: Coverage metrics, gap detection, and trace chain visualization
- 💡 **Actionable Insights**: Detailed reasoning for each gap with specific remediation suggestions

## Installation

### Prerequisites

- Python 3.11 or higher
- Groq API key (get one at https://console.groq.com)

### Setup

1. **Install dependencies using uv:**

```bash
uv pip install -e .
```

2. **Set up environment variables:**

```bash
export GROQ_API_KEY='your-api-key-here'
```

## Quick Start

Run the complete analysis:

```bash
python main.py --full
```

## Usage Examples

```bash
# Run full pipeline
python main.py --full

# Export trace matrix
python main.py --full --export-matrix

# Show gaps
python main.py --gaps

# Show trace chain
python main.py --trace SYS-001
```

## Output Files

Results are saved in `data/output/`:
- `analysis.json` - Complete analysis report
- `gaps.json` - Detailed gap analysis
- `trace_matrix.csv` - Trace matrix

See full documentation in comments and docstrings.
