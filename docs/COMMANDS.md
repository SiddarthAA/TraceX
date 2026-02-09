# Command Reference

## Quick Commands

```bash
# Simplest run (default paths)
uv run python3 main.py --full

# With custom input directory
uv run python3 main.py --full --input-dir reqs/Without_Gaps

# With custom output name
uv run python3 main.py --full --input-dir reqs/Without_Gaps --output-name BrakeSystem_v1

# Using the helper script
./run_analysis.sh reqs/Without_Gaps BrakeSystem_v1
```

## Complete Command Structure

```bash
uv run python3 main.py [MODE] [INPUT] [OUTPUT] [OPTIONS]
```

### Modes

```bash
--full                    # Run complete pipeline (recommended)
--stage <name>           # Run specific stage: load|decompose|index|link|analyze
```

### Input Options

```bash
--input-dir <path>       # Directory containing CSV files (auto-detects filenames)
--sys-reqs <file>        # Specific System Requirements CSV
--hlr <file>             # Specific High-Level Requirements CSV
--llr <file>             # Specific Low-Level Requirements CSV
--vars <file>            # Specific Variables CSV
```

### Output Options

```bash
--data-dir <path>        # Base data directory (default: ./data)
--output-name <name>     # Custom folder name (default: run_<timestamp>)
```

### Analysis Options

```bash
--no-llm                 # Skip LLM reasoning (faster, cheaper)
--export-matrix          # Force CSV matrix export (done by default now)
```

### Query Options (after run)

```bash
--trace <ID>            # Show trace chain for artifact
--gaps                   # Show all gaps
--coverage              # Show coverage metrics
```

## Common Workflows

### 1. Analyze New Requirements

```bash
# First time
uv run python3 main.py --full \
  --input-dir path/to/new/reqs \
  --output-name baseline_analysis

# View report
cat data/baseline_analysis/output/TRACEABILITY_REPORT.md
```

### 2. Compare Two Versions

```bash
# Analyze v1.0
uv run python3 main.py --full \
  --input-dir reqs/v1.0 \
  --output-name version_1.0

# Analyze v1.1
uv run python3 main.py --full \
  --input-dir reqs/v1.1 \
  --output-name version_1.1

# Compare coverage
diff data/version_1.0/output/traceability_matrix.csv \
     data/version_1.1/output/traceability_matrix.csv
```

### 3. Quick Check (No LLM)

```bash
# Fast analysis without gap reasoning
uv run python3 main.py --full --no-llm \
  --input-dir reqs/test \
  --output-name quick_check
```

### 4. Specific Files

```bash
# When files have non-standard names
uv run python3 main.py --full \
  --sys-reqs requirements/system.csv \
  --hlr requirements/high_level.csv \
  --llr requirements/low_level.csv \
  --vars requirements/variables.csv \
  --output-name custom_analysis
```

### 5. Query Existing Results

```bash
# After running --full, query specific items
uv run python3 main.py --trace SYS-001
uv run python3 main.py --gaps
uv run python3 main.py --coverage
```

## Output Files Reference

### Always Generated

| File | Description | Format |
|------|-------------|--------|
| `artifacts.json` | All requirements and metadata | JSON |
| `links.json` | All trace links with confidence | JSON |
| `analysis.json` | Coverage and gap analysis | JSON |
| `gaps.json` | Detailed gap information | JSON |
| `traceability_matrix.csv` | Main traceability matrix | CSV |
| `traceability_matrix.json` | Matrix with full details | JSON |
| `trace_graph.html` | Interactive visual graph | HTML |
| `trace_table.html` | Searchable table | HTML |
| `api_calls.json` | API usage tracking | JSON |
| `TRACEABILITY_REPORT.md` | Executive summary report | Markdown |

### View Commands

```bash
# Report (best to start here)
cat data/<run>/output/TRACEABILITY_REPORT.md
less data/<run>/output/TRACEABILITY_REPORT.md

# Matrix in Excel/LibreOffice
libreoffice data/<run>/output/traceability_matrix.csv

# Interactive visualizations
firefox data/<run>/output/trace_graph.html
firefox data/<run>/output/trace_table.html
chromium data/<run>/output/trace_graph.html

# JSON data
cat data/<run>/output/analysis.json | jq '.coverage_metrics'
cat data/<run>/output/api_calls.json | jq '.total_calls'
```

## Examples by Use Case

### For Certification (DO-178C)

```bash
# Complete analysis with all evidence
uv run python3 main.py --full \
  --input-dir certification/reqs \
  --output-name DO178C_baseline

# Review the report
cat data/DO178C_baseline/output/TRACEABILITY_REPORT.md

# Check for critical gaps
cat data/DO178C_baseline/output/gaps.json | jq '.[] | select(.severity=="critical")'
```

### For Development Team

```bash
# Quick iteration check (no LLM)
uv run python3 main.py --full --no-llm \
  --input-dir dev/current \
  --output-name dev_$(date +%Y%m%d)

# Check coverage
cat data/dev_*/output/analysis.json | jq '.coverage_metrics.end_to_end.complete_percentage'
```

### For Management Review

```bash
# Full analysis with all reports
uv run python3 main.py --full \
  --input-dir reqs/Q1_2026 \
  --output-name Q1_Review

# Package for review
cd data/Q1_Review/output
tar -czf Q1_Review_Package.tar.gz \
  TRACEABILITY_REPORT.md \
  traceability_matrix.csv \
  trace_graph.html \
  trace_table.html
```

### For Continuous Integration

```bash
#!/bin/bash
# CI script
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Run analysis
uv run python3 main.py --full --no-llm \
  --input-dir requirements/ \
  --output-name CI_$TIMESTAMP

# Extract coverage
COVERAGE=$(cat data/CI_$TIMESTAMP/output/analysis.json | \
  jq -r '.coverage_metrics.end_to_end.complete_percentage')

echo "Coverage: $COVERAGE%"

# Fail if below threshold
if (( $(echo "$COVERAGE < 80" | bc -l) )); then
    echo "ERROR: Coverage below 80%"
    exit 1
fi

echo "SUCCESS: Coverage acceptable"
```

## Troubleshooting Commands

```bash
# Test imports
uv run python3 -c "from src.pipeline.orchestrator import TraceabilityPipeline; print('OK')"

# Check configuration
uv run python3 -c "from config import Config; c = Config.from_env(); print(c.linking)"

# Verify model cache
ls -lh model_cache/

# Check API key
echo $GROQ_API_KEY

# View last run output
ls -ltr data/run_*/output/

# Check for errors
uv run python3 main.py --full 2>&1 | grep -i error
```

## Performance Tuning

```bash
# Faster (skip reasoning)
uv run python3 main.py --full --no-llm

# More thorough (adjust in config.py)
# confidence_threshold: 0.30  # Lower for more links

# Parallel processing (future enhancement)
# Currently sequential to respect rate limits
```

## Integration Examples

### With Git

```bash
# Track requirement changes
git add reqs/
git commit -m "Updated requirements v1.1"

# Run analysis
uv run python3 main.py --full --input-dir reqs/ --output-name v1.1

# Archive results
git add data/v1.1/output/TRACEABILITY_REPORT.md
git commit -m "Traceability analysis v1.1"
```

### With Jira/Issue Tracker

```bash
# Generate report
uv run python3 main.py --full --output-name sprint_23

# Extract gaps for tickets
cat data/sprint_23/output/gaps.json | \
  jq -r '.[] | select(.severity=="critical") | .description' > critical_gaps.txt
```

### With Excel/BI Tools

```bash
# Generate analysis
uv run python3 main.py --full --output-name monthly_report

# Import CSV to Excel
libreoffice --headless --convert-to xlsx \
  data/monthly_report/output/traceability_matrix.csv
```

## Help and Documentation

```bash
# Command help
uv run python3 main.py --help

# View guides
cat QUICKSTART.md
cat COMPLETE_SUMMARY.md
cat LINKING_IMPROVEMENTS.md

# Check version/status
uv run python3 --version
```

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│  MOST COMMON COMMANDS                                   │
├─────────────────────────────────────────────────────────┤
│  uv run python3 main.py --full                          │
│  → Basic run with defaults                              │
│                                                          │
│  uv run python3 main.py --full \                        │
│    --input-dir reqs/dir \                               │
│    --output-name my_analysis                            │
│  → Custom input and output                              │
│                                                          │
│  ./run_analysis.sh reqs/dir name                        │
│  → Quick script                                         │
│                                                          │
│  firefox data/run_*/output/trace_graph.html             │
│  → View interactive graph                               │
│                                                          │
│  cat data/run_*/output/TRACEABILITY_REPORT.md           │
│  → Read final report                                    │
└─────────────────────────────────────────────────────────┘
```
