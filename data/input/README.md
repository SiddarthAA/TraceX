# Input Data Format Guide

## Overview

TraceX accepts requirements in two formats:
1. **CSV Files** (separate HLR and LLR files)
2. **Excel Workbook** (multiple sheets)

---

## 📝 CSV Format

### HLRs File (High-Level Requirements)

**Filename**: `*_hlrs.csv` or `hlrs.csv`

**Required Columns**:
```csv
id,title,description,type,safety_level
```

**Example** (`my_project_hlrs.csv`):
```csv
id,title,description,type,safety_level
HLR-001,System Stability,"The flight control system shall maintain pitch stability within certified limits during all normal operating conditions.",functional,DAL-B
HLR-002,Emergency Response,"The system shall detect and respond to emergency conditions within 100ms with appropriate failsafe actions.",safety,DAL-A
HLR-003,Data Processing,"The system shall process sensor data from multiple sources and provide accurate attitude information.",functional,DAL-B
```

### LLRs File (Low-Level Requirements)

**Filename**: `*_llrs.csv` or `llrs.csv`

**Required Columns**:
```csv
id,title,description,type,component,safety_level
```

**Example** (`my_project_llrs.csv`):
```csv
id,title,description,type,component,safety_level
LLR-001,Actuator Response,"The elevator actuator shall respond to control commands within 30 ms.",performance,Actuator,DAL-B
LLR-002,Control Law Update,"The pitch control law shall execute at a minimum rate of 100 Hz.",performance,Control Software,DAL-B
LLR-003,IMU Latency,"The IMU shall provide pitch rate measurements with latency not exceeding 10ms.",performance,IMU,DAL-B
LLR-004,Data Logging,"The system shall log all critical flight data to non-volatile memory every 100ms.",diagnostic,Data Logger,DAL-D
```

---

## 📊 Excel Format

### Excel Workbook Structure

**Filename**: `requirements.xlsx` or `*_requirements.xlsx`

**Required Sheets**:
1. **HLRs** - High-level requirements
2. **LLRs** - Low-level requirements

**Sheet Names**: Must be exactly "HLRs" and "LLRs" (or specify custom names)

### HLRs Sheet

| id | title | description | type | safety_level |
|----|-------|-------------|------|--------------|
| HLR-001 | System Stability | The flight control system shall... | functional | DAL-B |
| HLR-002 | Emergency Response | The system shall detect... | safety | DAL-A |

### LLRs Sheet

| id | title | description | type | component | safety_level |
|----|-------|-------------|------|-----------|--------------|
| LLR-001 | Actuator Response | The elevator actuator shall... | performance | Actuator | DAL-B |
| LLR-002 | Control Law Update | The pitch control law shall... | performance | Control Software | DAL-B |

---

## 📋 Column Definitions

### Common Columns (HLRs & LLRs)

| Column | Type | Required | Description | Example Values |
|--------|------|----------|-------------|----------------|
| `id` | string | ✅ Yes | Unique identifier | HLR-001, LLR-042 |
| `title` | string | ✅ Yes | Short descriptive title | "System Stability" |
| `description` | string | ✅ Yes | Full requirement text | "The system shall..." |
| `type` | string | ✅ Yes | Requirement category | functional, performance, safety, interface, diagnostic, other |
| `safety_level` | string | ✅ Yes | Safety/criticality level | DAL-A, DAL-B, DAL-C, DAL-D, ASIL-A to ASIL-D, QM, not_specified |

### LLR-Only Columns

| Column | Type | Required | Description | Example Values |
|--------|------|----------|-------------|----------------|
| `component` | string | ⚠️ Recommended | Component/subsystem name | "Actuator", "Control Software", "IMU" |

---

## 🏷️ Valid Values

### Requirement Types

- `functional` - What the system does
- `performance` - Speed, timing, throughput
- `safety` - Safety-critical behavior
- `interface` - External interfaces
- `diagnostic` - Monitoring, logging, debugging
- `other` - Miscellaneous

### Safety Levels

**Aviation (DO-178C)**:
- `DAL-A` - Catastrophic (most critical)
- `DAL-B` - Hazardous
- `DAL-C` - Major
- `DAL-D` - Minor (least critical)

**Automotive (ISO 26262)**:
- `ASIL-D` - Highest safety integrity
- `ASIL-C`
- `ASIL-B`
- `ASIL-A`
- `QM` - Quality Management (non-safety)

**Generic**:
- `not_specified` - No safety level assigned

---

## ✅ Best Practices

### 1. ID Naming Convention
```
✅ Good:
  HLR-001, HLR-002, HLR-003
  LLR-001, LLR-002, LLR-003

✅ Also Good:
  SYS-REQ-001, SYS-REQ-002
  COMP-REQ-001, COMP-REQ-002

❌ Avoid:
  1, 2, 3 (not descriptive)
  REQ1, REQ2 (HLR vs LLR unclear)
```

### 2. Description Quality

```
✅ Good Description:
"The flight control system shall maintain pitch stability within ±2 degrees 
during normal flight conditions with a maximum recovery time of 500ms."

❌ Poor Description:
"Maintain stability"
```

**Include**:
- What shall be done
- Under what conditions
- Measurable criteria (if applicable)
- Timing/performance constraints

### 3. Type Selection

```
Functional:     "The system shall calculate..."
Performance:    "...within 30ms"
Safety:         "...shall detect fault and activate failsafe..."
Interface:      "...shall communicate with external system via..."
Diagnostic:     "...shall log to memory..."
```

### 4. Safety Level Consistency

```
✅ Valid:
  HLR (DAL-B) → LLR (DAL-B)  ✓
  HLR (DAL-B) → LLR (DAL-A)  ✓ (LLR more critical is OK)

❌ Invalid:
  HLR (DAL-A) → LLR (DAL-C)  ✗ (Can't implement critical with low-safety)
```

---

## 📥 Example Files

Download example files:
```bash
# Generate sample files
./run.sh samples

# Files created in data/samples/:
# - sample_hlrs.csv
# - sample_llrs.csv  
# - sample_requirements.xlsx
```

---

## 🔄 Workflow

### Option 1: CSV Files
```bash
# 1. Place your files
data/input/my_project_hlrs.csv
data/input/my_project_llrs.csv

# 2. Run CLI
./run.sh cli --hlr-csv data/input/my_project_hlrs.csv \
              --llr-csv data/input/my_project_llrs.csv

# 3. Results in
data/output/traceability_matrix_*.xlsx
```

### Option 2: Excel File
```bash
# 1. Place your file
data/input/my_project_requirements.xlsx
  (with sheets: HLRs, LLRs)

# 2. Run CLI
./run.sh cli --excel data/input/my_project_requirements.xlsx

# 3. Results in
data/output/traceability_matrix_*.xlsx
```

### Option 3: Web UI
```bash
# 1. Launch UI
./run.sh ui

# 2. Upload files in browser
#    Tab 1: Load Requirements

# 3. Download results
#    Tab 3: Export button
```

---

## ❓ Troubleshooting

### "Column not found" error
- Check spelling: `id`, `title`, `description`, `type`, `safety_level`
- CSV column names are case-sensitive
- No extra spaces in column names

### "Invalid safety level" warning
- Use exact values: `DAL-A`, `DAL-B`, etc.
- Not: `DALA`, `Dal-A`, `dal-a`

### Excel sheet not found
- Sheet names must be exactly: `HLRs` and `LLRs`
- Or specify custom names: `--hlr-sheet "Requirements-HLR"`

### Empty rows
- Remove empty rows from your files
- Or system will skip them (usually harmless)

---

## 📞 Need Help?

See example files in `data/samples/` for reference format.
