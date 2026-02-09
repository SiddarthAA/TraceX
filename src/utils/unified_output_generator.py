"""
Unified Output Generator
Generates all 5 output files with consistent data.
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


def generate_all_outputs(
    analysis: Dict[str, Any],
    artifacts: Dict[str, Any],
    links: List[Dict[str, Any]],
    output_dir: str
) -> None:
    """
    Generate all 5 unified outputs:
    1. analysis.json - Detailed analysis with reasons
    2. trace_paths.json - Complete trace paths for each requirement
    3. traceability_summary.csv - Summary table
    4. summary_report.md - Markdown report
    5. trace_graph.html - Interactive visualization (delegated to existing function)
    """
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 1. Generate analysis.json
    generate_analysis_json(analysis, output_path / 'analysis.json')
    
    # 2. Generate trace_paths.json
    generate_trace_paths_json(analysis['trace_paths'], artifacts, output_path / 'trace_paths.json')
    
    # 3. Generate traceability_summary.csv
    generate_traceability_summary_csv(analysis, output_path / 'traceability_summary.csv')
    
    # 4. Generate summary_report.md
    generate_summary_report_md(analysis, output_path / 'summary_report.md')
    
    print(f"\n✅ Generated unified outputs:")
    print(f"   1. analysis.json")
    print(f"   2. trace_paths.json")
    print(f"   3. traceability_summary.csv")
    print(f"   4. summary_report.md")
    print(f"   5. trace_graph.html (generated separately)")


def generate_analysis_json(analysis: Dict[str, Any], output_file: Path) -> None:
    """
    Generate analysis.json with detailed implementation status and reasons.
    
    Structure:
    - system_requirements: fully/partially/not implemented with reasons
    - high_level_requirements: fully/partially implemented or orphaned with reasons
    - low_level_requirements: traced or orphaned
    - quality_metrics: overall statistics
    """
    
    output = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'analysis_type': 'unified_traceability',
            'total_artifacts': analysis['metadata']['total_artifacts'],
            'total_links': analysis['metadata']['total_links'],
            'has_variables': analysis['metadata']['has_variables']
        },
        'system_requirements': analysis['system_requirements'],
        'high_level_requirements': analysis['high_level_requirements'],
        'low_level_requirements': analysis['low_level_requirements'],
        'quality_metrics': analysis['quality_metrics']
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Saved analysis.json")


def generate_trace_paths_json(
    trace_paths: Dict[str, Any],
    artifacts: Dict[str, Any],
    output_file: Path
) -> None:
    """
    Generate trace_paths.json with complete paths for each requirement.
    
    For each requirement type, shows:
    - System: forward paths (SYS → DECOMP → HLR → LLR)
    - HLR: backward (to SYS) and forward (to LLR) paths
    - LLR: backward paths (to HLR/SYS)
    """
    
    def format_path(path_ids: List[str]) -> str:
        """Format a path with types for readability."""
        parts = []
        for pid in path_ids:
            art = artifacts.get(pid, {})
            art_type = art.get('type', 'UNKNOWN')
            parts.append(f"{pid} ({art_type})")
        return " → ".join(parts)
    
    # Format system requirement paths
    sys_formatted = {}
    for sys_id, data in trace_paths['system_requirements'].items():
        sys_formatted[sys_id] = {
            'id': sys_id,
            'text': data['text'],
            'forward_paths': [
                {
                    'path_ids': path,
                    'path_formatted': format_path(path),
                    'depth': len(path)
                }
                for path in data['forward_paths']
            ],
            'path_count': data['path_count']
        }
    
    # Format HLR paths
    hlr_formatted = {}
    for hlr_id, data in trace_paths['high_level_requirements'].items():
        hlr_formatted[hlr_id] = {
            'id': hlr_id,
            'text': data['text'],
            'backward_paths': [
                {
                    'path_ids': path,
                    'path_formatted': format_path(path),
                    'depth': len(path)
                }
                for path in data['backward_paths']
            ],
            'forward_paths': [
                {
                    'path_ids': path,
                    'path_formatted': format_path(path),
                    'depth': len(path)
                }
                for path in data['forward_paths']
            ]
        }
    
    # Format LLR paths
    llr_formatted = {}
    for llr_id, data in trace_paths['low_level_requirements'].items():
        llr_formatted[llr_id] = {
            'id': llr_id,
            'text': data['text'],
            'backward_paths': [
                {
                    'path_ids': path,
                    'path_formatted': format_path(path),
                    'depth': len(path)
                }
                for path in data['backward_paths']
            ]
        }
    
    output = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'description': 'Complete trace paths for all requirements'
        },
        'system_requirements': sys_formatted,
        'high_level_requirements': hlr_formatted,
        'low_level_requirements': llr_formatted
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Saved trace_paths.json")


def generate_traceability_summary_csv(
    analysis: Dict[str, Any],
    output_file: Path
) -> None:
    """
    Generate comprehensive traceability_summary.csv with detailed status and reasons.
    
    Columns:
    - Requirement_ID: The unique identifier
    - Requirement_Text: Truncated text (first 100 chars)
    - Type: SYSTEM/HLR/LLR
    - Status: FULLY_IMPLEMENTED/PARTIALLY_IMPLEMENTED/NOT_IMPLEMENTED/TRACED/ORPHANED
    - Implementation_Details: Counts of downstream elements
    - Reason_If_Partial: Why partially implemented (which part is missing)
    - Parent_Info: Parent requirements (for HLR/LLR)
    - Children_Info: Child requirements (for SYSTEM/HLR)
    """
    
    rows = []
    
    # System requirements - detailed breakdown
    sys_analysis = analysis['system_requirements']
    
    for req in sys_analysis['fully_implemented']['requirements']:
        rows.append({
            'Requirement_ID': req['id'],
            'Requirement_Text': req['text'][:100] + '...' if len(req['text']) > 100 else req['text'],
            'Type': 'SYSTEM',
            'Status': '✅ FULLY_IMPLEMENTED',
            'Implementation_Details': f"Decompositions: {req['decomposition_count']}, HLRs: {req['hlr_count']}, LLRs: {req['llr_count']}",
            'Reason_If_Partial': 'N/A - Fully traced to LLRs',
            'Parent_Info': 'N/A - Top level',
            'Children_Info': f"{req['decomposition_count']} decompositions leading to {req['hlr_count']} HLRs"
        })
    
    for req in sys_analysis['partially_implemented']['requirements']:
        missing_parts = ', '.join(req.get('missing', []))
        has_parts = ', '.join(req.get('has', []))
        rows.append({
            'Requirement_ID': req['id'],
            'Requirement_Text': req['text'][:100] + '...' if len(req['text']) > 100 else req['text'],
            'Type': 'SYSTEM',
            'Status': '⚠️ PARTIALLY_IMPLEMENTED',
            'Implementation_Details': f"Decompositions: {req.get('decomposition_count', 0)}, HLRs: {req.get('hlr_count', 0)}, LLRs: {req.get('llr_count', 0)}",
            'Reason_If_Partial': f"{req['reason']} | Has: {has_parts} | Missing: {missing_parts}",
            'Parent_Info': 'N/A - Top level',
            'Children_Info': f"Partial chain - {has_parts}"
        })
    
    for req in sys_analysis['not_implemented']['requirements']:
        missing_parts = ', '.join(req.get('missing', []))
        rows.append({
            'Requirement_ID': req['id'],
            'Requirement_Text': req['text'][:100] + '...' if len(req['text']) > 100 else req['text'],
            'Type': 'SYSTEM',
            'Status': '❌ NOT_IMPLEMENTED',
            'Implementation_Details': 'No implementation found',
            'Reason_If_Partial': f"{req['reason']} | Missing: {missing_parts}",
            'Parent_Info': 'N/A - Top level',
            'Children_Info': 'None'
        })
    
    # High-level requirements - detailed breakdown
    hlr_analysis = analysis['high_level_requirements']
    
    for req in hlr_analysis['fully_implemented']['requirements']:
        rows.append({
            'Requirement_ID': req['id'],
            'Requirement_Text': req['text'][:100] + '...' if len(req['text']) > 100 else req['text'],
            'Type': 'HLR',
            'Status': '✅ FULLY_IMPLEMENTED',
            'Implementation_Details': f"Has {req['llr_count']} LLR(s) implementing this requirement",
            'Reason_If_Partial': 'N/A - Has parent link and LLR children',
            'Parent_Info': f"Linked to {req['parent_count']} parent(s) (system requirements)",
            'Children_Info': f"{req['llr_count']} LLR(s)"
        })
    
    for req in hlr_analysis['partially_implemented']['requirements']:
        has_parts = ', '.join(req.get('has', []))
        missing_parts = ', '.join(req.get('missing', []))
        rows.append({
            'Requirement_ID': req['id'],
            'Requirement_Text': req['text'][:100] + '...' if len(req['text']) > 100 else req['text'],
            'Type': 'HLR',
            'Status': '⚠️ PARTIALLY_IMPLEMENTED',
            'Implementation_Details': f"Parents: {req.get('parent_count', 0)}, LLRs: {req.get('llr_count', 0)}",
            'Reason_If_Partial': f"{req['reason']} | Has: {has_parts} | Missing: {missing_parts}",
            'Parent_Info': f"{req['parent_count']} parent(s)" if req.get('parent_count', 0) > 0 else 'No parent link (orphaned upstream)',
            'Children_Info': f"{req['llr_count']} LLR(s)" if req.get('llr_count', 0) > 0 else 'No LLR children (not decomposed)'
        })
    
    for req in hlr_analysis['orphaned']['requirements']:
        rows.append({
            'Requirement_ID': req['id'],
            'Requirement_Text': req['text'][:100] + '...' if len(req['text']) > 100 else req['text'],
            'Type': 'HLR',
            'Status': '❌ ORPHANED',
            'Implementation_Details': 'Completely isolated',
            'Reason_If_Partial': f"{req['reason']} - Not traceable to system requirements or LLRs",
            'Parent_Info': 'No parent link - cannot trace to system requirements',
            'Children_Info': 'No LLR children - not decomposed to low-level'
        })
    
    # Low-level requirements - traced or orphaned
    llr_analysis = analysis['low_level_requirements']
    
    for req in llr_analysis['traced']['requirements']:
        parent_hlrs = ', '.join(req.get('parent_hlrs', [])[:3])  # Show first 3 HLRs
        if len(req.get('parent_hlrs', [])) > 3:
            parent_hlrs += f" (and {len(req['parent_hlrs']) - 3} more)"
        
        rows.append({
            'Requirement_ID': req['id'],
            'Requirement_Text': req['text'][:100] + '...' if len(req['text']) > 100 else req['text'],
            'Type': 'LLR',
            'Status': '✅ TRACED',
            'Implementation_Details': f"Mapped to {req['hlr_count']} HLR(s)",
            'Reason_If_Partial': 'N/A - Successfully traced to parent HLR(s)',
            'Parent_Info': f"Linked to HLR(s): {parent_hlrs}",
            'Children_Info': 'N/A - Leaf level (no children expected)'
        })
    
    for req in llr_analysis['orphaned']['requirements']:
        rows.append({
            'Requirement_ID': req['id'],
            'Requirement_Text': req['text'][:100] + '...' if len(req['text']) > 100 else req['text'],
            'Type': 'LLR',
            'Status': '❌ ORPHANED',
            'Implementation_Details': 'Not mapped to any HLR',
            'Reason_If_Partial': f"{req['reason']} - Not used or traceable to any high-level requirement",
            'Parent_Info': 'No parent HLR - cannot trace upward',
            'Children_Info': 'N/A - Leaf level (no children expected)'
        })
    
    # Write CSV with comprehensive columns
    if rows:
        fieldnames = [
            'Requirement_ID',
            'Requirement_Text',
            'Type',
            'Status',
            'Implementation_Details',
            'Reason_If_Partial',
            'Parent_Info',
            'Children_Info'
        ]
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    
    print(f"✓ Saved traceability_summary.csv ({len(rows)} rows)")


def generate_summary_report_md(
    analysis: Dict[str, Any],
    output_file: Path
) -> None:
    """
    Generate summary_report.md - Markdown report for PDF conversion.
    
    Sections:
    1. Executive Summary
    2. System Requirements Analysis
    3. High-Level Requirements Analysis
    4. Low-Level Requirements Analysis
    5. Quality Metrics
    6. Issues and Recommendations
    """
    
    sys_analysis = analysis['system_requirements']
    hlr_analysis = analysis['high_level_requirements']
    llr_analysis = analysis['low_level_requirements']
    metrics = analysis['quality_metrics']
    
    report = f"""# Requirements Traceability Analysis Report

**Generated:** {datetime.now().strftime("%B %d, %Y at %H:%M:%S")}

---

## Executive Summary

This report provides a comprehensive analysis of requirements traceability across system, high-level, and low-level requirements.

### Key Metrics

| Metric | Value |
|--------|-------|
| Overall Implementation Rate | {metrics['overall_implementation_rate']:.1f}% |
| Total Requirements | {metrics['total_requirements']} |
| Total Implemented/Traced | {metrics['total_implemented']} |
| Total Orphaned | {metrics['total_orphaned']} |

---

## 1. System Requirements Analysis

**Total System Requirements:** {sys_analysis['total']}

### Implementation Status

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Fully Implemented | {sys_analysis['fully_implemented']['count']} | {sys_analysis['fully_implemented']['percentage']:.1f}% |
| ⚠️ Partially Implemented | {sys_analysis['partially_implemented']['count']} | {sys_analysis['partially_implemented']['percentage']:.1f}% |
| ❌ Not Implemented | {sys_analysis['not_implemented']['count']} | {sys_analysis['not_implemented']['percentage']:.1f}% |

### Fully Implemented System Requirements

"""
    
    if sys_analysis['fully_implemented']['requirements']:
        for req in sys_analysis['fully_implemented']['requirements']:
            report += f"- **{req['id']}**: {req['text'][:100]}...\n"
            report += f"  - Decompositions: {req['decomposition_count']}\n"
            report += f"  - High-Level Requirements: {req['hlr_count']}\n"
            report += f"  - Low-Level Requirements: {req['llr_count']}\n\n"
    else:
        report += "_No fully implemented system requirements found._\n\n"
    
    report += "### Partially Implemented System Requirements\n\n"
    
    if sys_analysis['partially_implemented']['requirements']:
        for req in sys_analysis['partially_implemented']['requirements']:
            report += f"- **{req['id']}**: {req['text'][:100]}...\n"
            report += f"  - **Issue**: {req['reason']}\n"
            report += f"  - Missing: {', '.join(req['missing'])}\n\n"
    else:
        report += "_No partially implemented system requirements._\n\n"
    
    report += "### Not Implemented System Requirements\n\n"
    
    if sys_analysis['not_implemented']['requirements']:
        for req in sys_analysis['not_implemented']['requirements']:
            report += f"- **{req['id']}**: {req['text'][:100]}...\n"
            report += f"  - **Issue**: {req['reason']}\n\n"
    else:
        report += "_All system requirements have at least partial implementation._\n\n"
    
    report += f"""---

## 2. High-Level Requirements Analysis

**Total HLRs:** {hlr_analysis['total']}

### Implementation Status

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Fully Implemented | {hlr_analysis['fully_implemented']['count']} | {hlr_analysis['fully_implemented']['percentage']:.1f}% |
| ⚠️ Partially Implemented | {hlr_analysis['partially_implemented']['count']} | {hlr_analysis['partially_implemented']['percentage']:.1f}% |
| ❌ Orphaned | {hlr_analysis['orphaned']['count']} | {hlr_analysis['orphaned']['percentage']:.1f}% |

"""
    
    if hlr_analysis['orphaned']['requirements']:
        report += "### ⚠️ Orphaned High-Level Requirements\n\n"
        report += "_These HLRs are not connected to system requirements or low-level requirements:_\n\n"
        for req in hlr_analysis['orphaned']['requirements']:
            report += f"- **{req['id']}**: {req['text'][:100]}...\n"
            report += f"  - Reason: {req['reason']}\n\n"
    
    if hlr_analysis['partially_implemented']['requirements']:
        report += "### ⚠️ Partially Implemented High-Level Requirements\n\n"
        for req in hlr_analysis['partially_implemented']['requirements']:
            report += f"- **{req['id']}**: {req['text'][:100]}...\n"
            report += f"  - **Issue**: {req['reason']}\n\n"
    
    report += f"""---

## 3. Low-Level Requirements Analysis

**Total LLRs:** {llr_analysis['total']}

### Traceability Status

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Traced | {llr_analysis['traced']['count']} | {llr_analysis['traced']['percentage']:.1f}% |
| ❌ Orphaned | {llr_analysis['orphaned']['count']} | {llr_analysis['orphaned']['percentage']:.1f}% |

"""
    
    if llr_analysis['orphaned']['requirements']:
        report += "### ⚠️ Orphaned Low-Level Requirements\n\n"
        report += "_These LLRs are not mapped to any high-level requirements:_\n\n"
        for req in llr_analysis['orphaned']['requirements']:
            report += f"- **{req['id']}**: {req['text'][:100]}...\n\n"
    
    report += f"""---

## 4. Quality Metrics Summary

| Layer | Implementation/Traceability Rate |
|-------|----------------------------------|
| System Requirements | {metrics['system_requirements_rate']:.1f}% |
| High-Level Requirements | {metrics['hlr_implementation_rate']:.1f}% |
| Low-Level Requirements | {metrics['llr_traceability_rate']:.1f}% |
| **Overall** | **{metrics['overall_implementation_rate']:.1f}%** |

---

## 5. Issues and Recommendations

### Critical Issues

"""
    
    issues = []
    
    if sys_analysis['not_implemented']['count'] > 0:
        issues.append(f"- {sys_analysis['not_implemented']['count']} system requirement(s) have no implementation")
    
    if hlr_analysis['orphaned']['count'] > 0:
        issues.append(f"- {hlr_analysis['orphaned']['count']} high-level requirement(s) are orphaned")
    
    if llr_analysis['orphaned']['count'] > 0:
        issues.append(f"- {llr_analysis['orphaned']['count']} low-level requirement(s) are orphaned")
    
    if issues:
        for issue in issues:
            report += issue + "\n"
    else:
        report += "_No critical issues found._\n"
    
    report += """
### Recommendations

1. **Review orphaned requirements**: Orphaned HLRs and LLRs should either be linked to parent requirements or removed if obsolete.
2. **Complete partial implementations**: Partially implemented system requirements should have complete trace chains established.
3. **Validate trace paths**: Use the `trace_paths.json` file to verify that all requirements have appropriate forward and backward traceability.
4. **Regular audits**: Conduct periodic traceability audits to maintain requirements integrity.

---

## Appendices

### A. Output Files

This analysis generated the following output files:

1. **analysis.json** - Detailed JSON analysis with all requirements and reasons
2. **trace_paths.json** - Complete trace paths for forward and backward traceability
3. **traceability_summary.csv** - Tabular summary of all requirements and their status
4. **summary_report.md** - This report (can be converted to PDF)
5. **trace_graph.html** - Interactive visualization of requirement relationships

### B. Conversion to PDF

To convert this report to PDF, use one of the following tools:

```bash
# Using pandoc
pandoc summary_report.md -o summary_report.pdf --pdf-engine=xelatex

# Using markdown-pdf (Node.js)
markdown-pdf summary_report.md

# Using grip (GitHub-flavored markdown)
grip summary_report.md --export summary_report.html
# Then print to PDF from browser
```

---

**End of Report**
"""
    
    with open(output_file, 'w') as f:
        f.write(report)
    
    print(f"✓ Saved summary_report.md")
