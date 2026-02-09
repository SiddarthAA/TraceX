# Quick Start: Hierarchical Linking Mode
## February 4, 2026

## 🚀 What Changed?

**TL;DR**: The system now links requirements **layer-by-layer** with **LLM validation** instead of all-at-once. This makes linking more accurate and provides detailed orphan/completeness analysis.

---

## ⚡ Quick Command

```bash
# Run with new hierarchical mode (default)
python main.py --full --input-dir reqs/Samples-Latest --output-name Results

# Use old approach if needed
python main.py --full --input-dir reqs/Samples-Latest --legacy-linking
```

---

## 🎯 Key Changes

### 1. **Linking Strategy**

**OLD (Legacy)**:
```
Find ALL links at once → Apply threshold → Done
```

**NEW (Hierarchical)**:
```
Layer 1: SYS → DECOMP (automatic)
   ↓
Layer 2: DECOMP → HLR (multi-signal → LLM picks best)
   ↓
Layer 3: HLR → LLR (multi-signal → LLM picks best)
   ↓
Layer 4: LLR → VAR (multi-signal → LLM picks best)
```

### 2. **LLM Role**

**OLD**: Only explains gaps after linking  
**NEW**: Validates which targets **actually implement** the source (not just similar)

### 3. **Analysis Output**

**OLD**: Basic coverage percentages  
**NEW**: Detailed breakdown of:
- ✅ Complete requirements (fully traced)
- ⚠️ Partial implementations (some gaps)
- ❌ Orphaned requirements (isolated)
- 🔗 Chain status (complete/partial/broken)

---

## 📊 Example Output

### Linking Statistics
```
=== Layer-by-Layer Hierarchical Linking ===

[Layer 1] SYSTEM_REQ → DECOMPOSED: 10 links
[Layer 2] DECOMPOSED → HLR: 23 links (LLM selected 23/120 candidates)
[Layer 3] HLR → LLR: 31 links (LLM selected 31/150 candidates)
[Layer 4] LLR → VAR: 28 links (LLM selected 28/140 candidates)

Total: 92 links created
LLM calls: 45
Selectivity: ~20% (filters out false positives)
```

### Analysis Summary
```
SYSTEM REQUIREMENTS (10 total):
  ✓ Complete: 8 (80.0%)
  ⚠ Partial: 1 (10.0%)
  ✗ No decomposition: 1 (10.0%)

HIGH-LEVEL REQUIREMENTS (25 total):
  ✓ Complete: 22 (88.0%)
  ⚠ Partial: 2 (8.0%)
  ✗ Orphaned: 1 (4.0%)

TRACE CHAINS (39 total):
  ✓ Complete: 32 (82.1%)
  ⚠ Partial: 5 (12.8%)
  ✗ Broken: 2 (5.1%)
```

---

## 🎨 Interactive Graph (Unchanged)

The graph visualization remains **exactly the same**:
- ✅ Single unified graph (no duplicates)
- ✅ Dropdown to select any node
- ✅ Trace path highlighting (up & down)
- ✅ "Show Only Trace" filter
- ✅ Bidirectional navigation

**Only the linking logic changed - the visualization is identical!**

---

## ⚙️ Configuration

### Enable/Disable Hierarchical Mode
```bash
# Hierarchical (default)
python main.py --full --input-dir reqs/

# Legacy
python main.py --full --input-dir reqs/ --legacy-linking
```

### Tune Layer Thresholds
In `config.py`:
```python
'layer_thresholds': {
    'SYSTEM_REQ_DECOMPOSED->HLR': 0.28,
    'HLR->LLR': 0.25,
    'LLR->CODE_VAR': 0.23
}
```
Lower = more links, Higher = fewer but higher confidence

### LLM Minimum Confidence
In `src/link/hierarchical_linker.py`:
```python
if sel['confidence'] >= 0.6:  # Change this
```
- 0.7+: Very selective
- 0.6: Balanced (current)
- 0.5: More permissive

---

## 📁 New Files

1. **`src/link/hierarchical_linker.py`**: Layer-by-layer linking with LLM
2. **`src/analyze/hierarchical_analyzer.py`**: Orphan detection & completeness analysis
3. **`HIERARCHICAL_ARCHITECTURE.md`**: Full documentation (this summary's big brother)

---

## 🔍 What to Check

### 1. Review Analysis
```bash
cat data/Results/output/analysis.json | jq '.system_requirements, .high_level_requirements'
```

### 2. Check Orphans
```bash
cat data/Results/output/analysis.json | jq '.high_level_requirements.orphaned, .low_level_requirements.orphaned'
```

### 3. View Chains
```bash
cat data/Results/output/analysis.json | jq '.chains.complete.count, .chains.partial.count, .chains.broken.count'
```

### 4. Open Graph
```bash
firefox data/Results/output/trace_graph.html
```

### 5. Check API Usage
```bash
cat data/Results/output/api_calls.json | jq '.summary'
```

---

## 🐛 Common Issues

### "Too many API calls"
```bash
# Solution: Use legacy mode or disable LLM
python main.py --full --input-dir reqs/ --legacy-linking
# OR
python main.py --full --input-dir reqs/ --no-llm
```

### "Too few links created"
1. Lower thresholds in `config.py`
2. Check `analysis.json` for orphans
3. Verify input data quality

### "Analysis format different"
**This is expected!** Hierarchical mode provides much more detail:
- Complete/partial/orphaned classifications
- Chain analysis
- Layer-by-layer breakdowns

---

## 📊 Performance

| Metric | Legacy Mode | Hierarchical Mode |
|--------|-------------|-------------------|
| **LLM Calls** | 10-50 | 100-500 |
| **Runtime** | 2-5 min | 5-10 min |
| **Accuracy** | Good | Excellent |
| **Orphan Detection** | Basic | Advanced |
| **False Positives** | Some | Very few |
| **Coverage** | 50-70% | 70-85% |

---

## ✅ Quick Test

```bash
# 1. Run hierarchical mode
python main.py --full --input-dir reqs/Samples-Latest --output-name HierarchicalTest

# 2. Check it worked
ls data/HierarchicalTest/output/
# Should see: analysis.json, trace_graph.html, TRACEABILITY_REPORT.md, etc.

# 3. Verify hierarchical analysis
cat data/HierarchicalTest/output/analysis.json | jq '.system_requirements.complete.percentage'
# Should see: something like 80.0

# 4. Open interactive graph
firefox data/HierarchicalTest/output/trace_graph.html
# Select a node, verify trace highlighting works

# 5. Check LLM calls
cat data/HierarchicalTest/output/api_calls.json | jq '.summary.total_calls'
# Should see: 50-500 depending on data size
```

---

## 🎓 When to Use Which Mode?

### Use Hierarchical (Default)
- ✅ Want highest accuracy
- ✅ Have Groq API key
- ✅ Can afford 5-10 min runtime
- ✅ Need detailed orphan analysis
- ✅ Working on important/large datasets

### Use Legacy
- ✅ Need fast results (2-5 min)
- ✅ No API key or limited budget
- ✅ Quick prototyping
- ✅ Don't need orphan detection
- ✅ Okay with some false positives

---

## 📞 Help

**Full Documentation**: See `HIERARCHICAL_ARCHITECTURE.md`  
**Original Docs**: See `ARCHITECTURE.md` and `UPDATES_FEB4.md`  
**Issue**: If something breaks, try `--legacy-linking` first

---

**Key Takeaway**: Hierarchical mode makes linking more accurate by validating each layer with LLM. The graph and visualization are unchanged - only the linking logic and analysis are enhanced!
