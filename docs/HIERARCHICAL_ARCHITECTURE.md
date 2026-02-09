# Hierarchical Layer-by-Layer Linking Architecture
## February 4, 2026

## 🎯 Major Architecture Changes

This update represents a **fundamental redesign** of the traceability linking approach, moving from all-at-once linking to **hierarchical layer-by-layer linking with LLM reasoning**.

---

## 📋 Overview of Changes

### 1. **Layer-by-Layer Linking Strategy**

#### Old Approach (Legacy)
- All links established simultaneously
- Single pass through all artifact pairs
- Same threshold applied across all layers
- No differentiation between layer transitions

#### New Approach (Hierarchical)
```
LAYER 1: SYSTEM_REQ → SYSTEM_REQ_DECOMPOSED (deterministic)
    ↓
LAYER 2: SYSTEM_REQ_DECOMPOSED → HLR (multi-signal + LLM)
    ↓
LAYER 3: HLR → LLR (multi-signal + LLM)
    ↓
LAYER 4: LLR → CODE_VAR (multi-signal + LLM)
    ↓
CHAIN FORMATION: Connect layers into end-to-end traces
```

**Benefits:**
- More deliberate and accurate linking at each level
- LLM reasoning validates that target truly implements source
- Prevents false positives from superficial semantic similarity
- Better handling of multi-level decomposition
- Clearer separation of concerns

---

### 2. **LLM-Based Target Selection**

Each layer now uses **LLM reasoning** to select which candidate targets actually implement the source requirement.

#### Selection Process:
1. **Multi-signal matching** generates ranked candidates (top 10-20)
2. **LLM analyzes** each candidate against source requirement
3. **LLM selects** targets that truly implement (not just similar)
4. **Confidence scoring** from LLM (must be ≥0.6 to accept)

#### LLM Selection Prompt:
```
Given:
- Source requirement at higher abstraction level
- Candidate targets with match scores
- Match details (embedding, keywords, quantities, ID relationships)

Task:
- Determine which candidates ACTUALLY implement the source
- Provide reasoning for selections and rejections
- Assign confidence scores (0.0-1.0)
```

**Example:**
```json
{
  "selected_targets": [
    {
      "target_id": "HLR-001-A",
      "reasoning": "Directly addresses altitude control requirement with specific control law implementation",
      "confidence": 0.85
    }
  ],
  "rejected_targets": [
    {
      "target_id": "HLR-002-B",
      "reason": "Related to navigation but doesn't implement altitude control"
    }
  ]
}
```

---

### 3. **Unified Graph Visualization**

The graph remains **unified and non-redundant**:
- **No duplicate nodes** for the same requirement
- **Single source of truth** for each artifact
- **Bidirectional tracing** (up and down the hierarchy)

#### Interactive Features:
- **Node selector dropdown** organized by artifact type
- **Trace path highlighting** when node selected
- **Upward trace**: Follow node → parents → ancestors (to SYSTEM_REQ)
- **Downward trace**: Follow node → children → descendants (to CODE_VAR)
- **"Show Only Trace"** filter to isolate selected chain
- **Real-time statistics** (visible nodes/links)

---

### 4. **Enhanced Analysis with Orphan Detection**

New `hierarchical_analyzer.py` provides comprehensive analysis:

#### System Requirements Analysis:
- **Complete**: Fully traced to variables through HLR→LLR
- **Partial**: Decomposed but chain doesn't reach variables
- **No Decomposition**: Not broken down

#### HLR/LLR Layer Analysis:
- **Complete**: Has parent links AND child links
- **Partial**: Has parent OR children (not both)
- **Orphaned**: No parent and no children (isolated)

#### Variable Analysis:
- **Traced**: Linked to at least one LLR
- **Orphaned**: No LLR parent (not traced)

#### Chain Analysis:
- **Complete chains**: Reach from SYSTEM_REQ to CODE_VAR (depth ≥4)
- **Partial chains**: Some depth but don't reach variables
- **Broken chains**: Too short (depth <2)

---

## 📁 New Files Created

### 1. `src/link/hierarchical_linker.py`
**Purpose**: Layer-by-layer hierarchical linking with LLM reasoning

**Key Class**: `HierarchicalLinker`

**Methods:**
- `establish_all_links()`: Run all layers sequentially
- `_link_decomposition()`: Layer 1 (deterministic)
- `_link_layer()`: Generic layer linker with LLM
- `_find_candidates()`: Multi-signal candidate generation
- `_llm_select_targets()`: LLM-based target selection
- `_passes_quality_filters()`: Quality validation

**Statistics Tracked:**
- Candidates evaluated per layer
- LLM calls made
- Links created
- Selectivity percentage (selected/candidates)

### 2. `src/analyze/hierarchical_analyzer.py`
**Purpose**: Comprehensive hierarchical analysis with orphan detection

**Main Function**: `analyze_hierarchical_traceability()`

**Analysis Functions:**
- `_analyze_system_requirements()`: Completeness of system reqs
- `_analyze_hlr_layer()`: HLR orphans and partial implementations
- `_analyze_llr_layer()`: LLR orphans and partial implementations
- `_analyze_variable_layer()`: Variable traceability
- `_analyze_chains()`: End-to-end trace chain analysis
- `_compute_coverage_summary()`: Overall coverage metrics
- `_compute_quality_metrics()`: Link quality statistics

**Output Format:**
```json
{
  "system_requirements": {
    "total": 10,
    "complete": {"count": 7, "percentage": 70.0, "requirements": [...]},
    "partial": {"count": 2, "percentage": 20.0, "requirements": [...]},
    "no_decomposition": {"count": 1, "percentage": 10.0, "requirements": [...]}
  },
  "high_level_requirements": {
    "total": 25,
    "complete": {"count": 20, "percentage": 80.0, ...},
    "partial": {"count": 3, "percentage": 12.0, ...},
    "orphaned": {"count": 2, "percentage": 8.0, ...}
  },
  "chains": {
    "total_chains": 45,
    "complete": {"count": 35, "percentage": 77.8, ...},
    "partial": {"count": 8, "percentage": 17.8, ...},
    "broken": {"count": 2, "percentage": 4.4, ...}
  }
}
```

---

## 🔧 Modified Files

### 1. `src/pipeline/orchestrator.py`

#### Updated `establish_links()`:
```python
def establish_links(self, use_hierarchical: bool = True) -> None:
    if use_hierarchical:
        # New hierarchical linker
        hierarchical_linker = HierarchicalLinker(
            self.artifacts, self.indexer, self.config, self.groq_client
        )
        self.links = hierarchical_linker.establish_all_links()
    else:
        # Legacy linker (fallback)
        link_manager = LinkManager(self.artifacts, self.indexer, self.config)
        self.links = link_manager.establish_links()
```

#### Updated `analyze()`:
```python
def analyze(self, use_llm_reasoning: bool = True, use_hierarchical: bool = True) -> None:
    if use_hierarchical:
        # New hierarchical analyzer
        self.analysis = analyze_hierarchical_traceability(self.artifacts, self.links)
    else:
        # Legacy analyzer (fallback)
        self.analysis = analyze_traceability(self.artifacts, self.links)
```

#### Updated `run_full_pipeline()`:
```python
def run_full_pipeline(
    self,
    system_reqs_file: str,
    hlr_file: str,
    llr_file: str,
    variables_file: str,
    use_llm_reasoning: bool = True,
    use_hierarchical: bool = True  # NEW PARAMETER
) -> Dict[str, Any]:
    # Shows mode in output
    if use_hierarchical:
        print("🔗 Mode: Hierarchical layer-by-layer linking with LLM reasoning")
    else:
        print("🔗 Mode: Legacy all-at-once linking")
```

### 2. `main.py`

#### New Command-Line Arguments:
```bash
--hierarchical          # Use hierarchical mode (DEFAULT: True)
--legacy-linking        # Use legacy all-at-once linking (disables hierarchical)
```

#### Examples:
```bash
# Run with hierarchical linking (default)
python main.py --full --input-dir reqs/Samples-Latest

# Run with legacy linking
python main.py --full --input-dir reqs/Samples-Latest --legacy-linking

# Skip LLM reasoning (uses only multi-signal matching)
python main.py --full --input-dir reqs/Samples-Latest --no-llm
```

---

## 🎯 Key Differences: Hierarchical vs Legacy

| Aspect | Legacy Mode | Hierarchical Mode |
|--------|-------------|-------------------|
| **Linking Strategy** | All-at-once | Layer-by-layer |
| **LLM Usage** | Optional gap reasoning only | Mandatory for link selection |
| **Target Selection** | Top-K by score | LLM validates implementation |
| **Layer Awareness** | Single threshold | Per-layer thresholds + reasoning |
| **False Positive Prevention** | Quality filters only | Quality filters + LLM validation |
| **Orphan Detection** | Basic (no parent/children) | Advanced (complete/partial/orphaned) |
| **Chain Analysis** | Simple depth counting | Complete/partial/broken classification |
| **Analysis Output** | Coverage metrics | Comprehensive layer-by-layer breakdown |
| **API Calls** | ~10-50 (gap reasoning) | ~100-500 (link selection + gaps) |
| **Accuracy** | Good | Excellent |
| **Speed** | Fast | Moderate (LLM calls) |

---

## 🚀 Usage Guide

### Running Hierarchical Mode (Recommended)

```bash
# Full pipeline with hierarchical linking
python main.py --full --input-dir reqs/Samples-Latest --output-name Results

# What happens:
# 1. Loads requirements files
# 2. Decomposes system requirements with LLM
# 3. Builds embedding index
# 4. Links layer-by-layer:
#    - SYS → DECOMP (deterministic)
#    - DECOMP → HLR (multi-signal + LLM selects best)
#    - HLR → LLR (multi-signal + LLM selects best)
#    - LLR → VAR (multi-signal + LLM selects best)
# 5. Analyzes completeness, orphans, chains
# 6. Generates interactive graph + reports
```

### Expected Output Structure

```
data/Results/
├── intermediate/
│   ├── raw_artifacts.json
│   ├── decomposed_artifacts.json
│   ├── embeddings.index
│   ├── embeddings.ids.json
│   └── links.json
└── output/
    ├── analysis.json                    # ← New hierarchical analysis
    ├── traceability_matrix.csv
    ├── traceability_matrix.json
    ├── trace_graph.html                 # ← Unified interactive graph
    ├── trace_table.html
    ├── api_calls.json                   # ← Shows LLM call statistics
    └── TRACEABILITY_REPORT.md
```

### Interpreting Hierarchical Analysis

Open `data/Results/output/analysis.json` and look for:

```json
{
  "system_requirements": {
    "complete": {"count": 8, "percentage": 80.0},
    "partial": {"count": 1, "percentage": 10.0},
    "no_decomposition": {"count": 1, "percentage": 10.0}
  },
  "high_level_requirements": {
    "complete": {"count": 22, "percentage": 88.0},
    "partial": {"count": 2, "percentage": 8.0},
    "orphaned": {"count": 1, "percentage": 4.0}
  },
  "chains": {
    "complete": {"count": 32, "percentage": 82.1},
    "partial": {"count": 5, "percentage": 12.8},
    "broken": {"count": 2, "percentage": 5.1}
  }
}
```

**Interpretation:**
- **80% of system requirements** are completely traced to variables
- **88% of HLRs** have both parent and child links (not orphaned)
- **82% of trace chains** reach from system requirements to code variables
- **1 HLR is orphaned** (needs investigation)
- **2 chains are broken** (need repair)

---

## 🔍 Understanding the Interactive Graph

### Node Selection
1. **Open** `trace_graph.html` in browser
2. **Select node** from dropdown (organized by type)
3. **Graph highlights**:
   - Selected node in **yellow**
   - Trace path nodes in **full opacity**
   - Unrelated nodes **dimmed**

### Trace Navigation
- **Upward trace** (blue arrows): Follow node → parents → SYSTEM_REQ
- **Downward trace** (green arrows): Follow node → children → CODE_VAR
- **Complete path**: Both directions shown simultaneously

### Filtering
- **Show Only Trace**: Hides all nodes not in selected trace path
- **Show All**: Resets to full graph
- **Statistics**: Shows visible nodes/links count in real-time

### No Duplicates
- Each requirement appears **exactly once** in the graph
- No separate nodes for same requirement
- All links connect actual artifacts (single source of truth)

---

## ⚙️ Configuration

### Layer Thresholds
In `config.py`, you can tune per-layer confidence thresholds:

```python
'layer_thresholds': {
    'SYSTEM_REQ_DECOMPOSED->HLR': 0.28,  # Lower = more links
    'HLR->LLR': 0.25,
    'LLR->CODE_VAR': 0.23
}
```

**Tuning Guide:**
- **Higher thresholds** (0.30-0.40): Fewer, higher-confidence links
- **Lower thresholds** (0.20-0.25): More links, catch edge cases
- **Current values** (0.23-0.28): Balanced for good coverage + quality

### LLM Minimum Confidence
In `hierarchical_linker.py`:

```python
if sel['confidence'] >= 0.6:  # Minimum LLM confidence
```

**Tuning:**
- **0.7+**: Very selective, high precision
- **0.6**: Balanced (current)
- **0.5**: More permissive, catch more links

### Quality Filters
Same as before - prevents random matches even if LLM tries to select them:

```python
'quality_filters': {
    'min_text_overlap': 0.05,
    'min_combined_signals': 2,
    'max_links_per_source': 15
}
```

---

## 📊 Performance Expectations

### API Usage
- **Legacy mode**: 10-50 LLM calls (gap reasoning only)
- **Hierarchical mode**: 100-500 LLM calls (link selection + gaps)
- **Rate limiting**: 30 calls/minute (automatic throttling)
- **Cost**: ~$0.05-0.15 per run (Groq llama-3.3-70b-versatile)

### Linking Statistics Example

```
=== Layer-by-Layer Hierarchical Linking ===

[Layer 1] Linking SYSTEM_REQ -> SYSTEM_REQ_DECOMPOSED...
  Created 32 decomposition links

[Layer] Linking SYSTEM_REQ_DECOMPOSED -> HLR...
  Confidence threshold: 0.28
  LLM reasoning: enabled
  Processing 32 SYSTEM_REQ_DECOMPOSED artifacts...
  Created 68 links

[Layer] Linking HLR -> LLR...
  Confidence threshold: 0.25
  LLM reasoning: enabled
  Processing 25 HLR artifacts...
  Created 52 links

[Layer] Linking LLR -> CODE_VAR...
  Confidence threshold: 0.23
  LLM reasoning: enabled
  Processing 32 LLR artifacts...
  Created 45 links

=== Linking Statistics ===
Decomposition links: 32

SYS TO HLR:
  Candidates evaluated: 320
  LLM calls made: 32
  Links created: 68
  Selectivity: 21.3%

HLR TO LLR:
  Candidates evaluated: 250
  LLM calls made: 25
  Links created: 52
  Selectivity: 20.8%

LLR TO VAR:
  Candidates evaluated: 320
  LLM calls made: 32
  Links created: 45
  Selectivity: 14.1%

Total links created: 197
```

**Interpretation:**
- **Selectivity ~20%**: LLM selects 1 in 5 candidates (prevents false positives)
- **89 LLM calls**: Reasonable API usage
- **197 total links**: Good coverage

---

## 🐛 Troubleshooting

### Issue: "Too few links created"
**Solution:**
1. Lower layer thresholds in `config.py`
2. Lower LLM minimum confidence to 0.5
3. Check if requirements have sufficient overlap

### Issue: "Too many API calls / slow"
**Solution:**
1. Use `--no-llm` flag (disables LLM reasoning, faster)
2. Use `--legacy-linking` (original approach, fewer calls)
3. Reduce `top_k` candidates in config (default: 20)

### Issue: "Many orphaned requirements"
**Solution:**
1. Check if requirements files are correctly formatted
2. Verify ID patterns match expected hierarchy (e.g., HLR-001-A)
3. Lower embedding threshold to catch more semantic matches
4. Inspect orphaned requirements in `analysis.json`

### Issue: "LLM selections seem wrong"
**Solution:**
1. Check API call logs in `api_calls.json`
2. Verify LLM temperature is low (0.1) for consistency
3. Update LLM selection prompt if needed
4. Fall back to legacy mode for comparison

---

## 🎓 Design Rationale

### Why Layer-by-Layer?

1. **Conceptual Clarity**: Each layer represents a clear abstraction level
2. **Focused Reasoning**: LLM can better judge "does HLR implement SYS?" than "find all links"
3. **Error Isolation**: Problems at one layer don't cascade
4. **Traceability**: Clear provenance of each link decision

### Why LLM Selection?

1. **Semantic Understanding**: Embeddings capture similarity, not implementation
2. **False Positive Prevention**: Many semantically similar reqs don't implement each other
3. **Expert Judgment**: LLM acts as domain expert validating matches
4. **Explainability**: Each link has reasoning ("implements altitude control with PID")

### Why Unified Graph?

1. **Single Source of Truth**: Each requirement exists once
2. **Bidirectional Tracing**: Navigate up/down hierarchy naturally
3. **No Data Duplication**: Efficient, consistent
4. **User-Friendly**: Select any node, see its complete context

---

## 🔮 Future Enhancements

### Potential Improvements:
1. **Confidence Calibration**: Learn optimal thresholds from user feedback
2. **Batch LLM Calls**: Process multiple layers in parallel
3. **Incremental Updates**: Re-link only changed requirements
4. **Custom Layer Rules**: User-defined layer transition logic
5. **Multi-LLM Validation**: Use multiple models for consensus
6. **Interactive Link Editing**: Manual override of LLM decisions in UI

---

## 📝 Migration Guide

### From Legacy to Hierarchical

**No changes needed!** Hierarchical mode is now the default.

To temporarily use legacy mode:
```bash
python main.py --full --input-dir reqs/Samples-Latest --legacy-linking
```

### Existing Data
- Old `links.json` files are compatible
- Analysis format is different (hierarchical provides more detail)
- Graphs remain unified (no duplication in either mode)

### Configuration
- All existing config values still work
- New `layer_thresholds` are optional (defaults to `confidence_threshold`)
- Quality filters apply to both modes

---

## ✅ Testing Checklist

- [ ] Run hierarchical mode on sample data
- [ ] Verify LLM calls are reasonable (<500 per run)
- [ ] Check analysis.json has hierarchical structure
- [ ] Open trace_graph.html and test node selector
- [ ] Confirm no duplicate nodes in graph
- [ ] Verify upward and downward tracing works
- [ ] Check for orphaned requirements in analysis
- [ ] Compare results with legacy mode (if available)
- [ ] Review TRACEABILITY_REPORT.md for completeness
- [ ] Verify API costs are acceptable

---

## 📞 Support

**Issue**: Hierarchical mode not working
**Check**: 
1. `GROQ_API_KEY` environment variable set
2. Internet connection for LLM API calls
3. `src/link/hierarchical_linker.py` exists
4. No syntax errors in new files

**Issue**: Analysis looks different
**Explanation**: This is expected! Hierarchical analysis provides much more detail:
- Complete/partial/orphaned classifications
- Layer-by-layer breakdowns
- Chain analysis (complete/partial/broken)

**Issue**: Graph looks the same
**Explanation**: Also expected! The graph visualization is unchanged (unified, no duplicates). Only the linking and analysis logic changed.

---

**Created**: February 4, 2026  
**Author**: Aerospace Traceability Engine Team  
**Version**: 2.0.0 (Hierarchical)
