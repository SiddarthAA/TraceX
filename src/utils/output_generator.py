"""
Unified Output Generator
Generates all required outputs with consistent data.
"""

import json
import csv
from typing import Dict, Any
from pathlib import Path


def generate_all_outputs(
    analysis: Dict[str, Any],
    artifacts: Dict[str, Any],
    output_dir: str
) -> None:
    """Generate all 5 required outputs."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 1. Analysis JSON
    generate_analysis_json(analysis, output_path / 'analysis.json')
    
    # 2. Trace Paths JSON
    generate_trace_paths_json(analysis['trace_paths'], artifacts, output_path / 'trace_paths.json')
    
    # 3. Traceability Summary CSV
    generate_traceability_csv(analysis, output_path / 'traceability_summary.csv')
    
    # 4. Summary Report Markdown
    generate_summary_report(analysis, artifacts, output_path / 'summary_report.md')
    
    print(f"\n✅ Generated outputs:")
    print(f"   1. {output_path / 'analysis.json'}")
    print(f"   2. {output_path / 'trace_paths.json'}")
    print(f"   3. {output_path / 'traceability_summary.csv'}")
    print(f"   4. {output_path / 'summary_report.md'}")
    print(f"   5. trace_graph.html (generated separately)")


def generate_analysis_json(analysis: Dict[str, Any], output_file: Path) -> None:
    """Generate detailed analysis JSON report."""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)


def generate_trace_paths_json(
    trace_paths: Dict[str, Any],
    artifacts: Dict[str, Any],
    output_file: Path
) -> None:
    """Generate trace paths JSON with human-readable format."""
    
    formatted_paths = {
        'system_requirements': {},
        'high_level_requirements': {},
        'low_level_requirements': {}
    }
    
    # Format system requirement paths
    for sys_id, sys_data in trace_paths['system_requirements'].items():
        formatted_paths['system_requirements'][sys_id] = {
            'id': sys_id,
            'text': sys_data['text'],
            'paths': [
                {
                    'path_string': ' → '.join(path),
                    'path_details': [
                        {
                            'id': node_id,
                            'type': artifacts[node_id]['type'],
                            'text': artifacts[node_id]['text'][:100]
                        }
                        for node_id in path
                    ]
                }
                for path in sys_data['forward_paths']
            ],
            'total_paths': sys_data['path_count']
        }
    
    # Format HLR paths
    for hlr_id, hlr_data in trace_paths['high_level_requirements'].items():
        formatted_paths['high_level_requirements'][hlr_id] = {
            'id': hlr_id,
            'text': hlr_data['text'],
            'backward_paths': [
                {
                    'path_string': ' → '.join(path),
                    'path_details': [
                        {
                            'id': node_id,
                            'type': artifacts[node_id]['type'],
                            'text': artifacts[node_id]['text'][:100]
                        }
                        for node_id in path
                    ]
                }
                for path in hlr_data['backward_paths']
            ],
            'forward_paths': [
                {
                    'path_string': ' → '.join(path),
                    'path_details': [
                        {
                            'id': node_id,
                            'type': artifacts[node_id]['type'],
                            'text': artifacts[node_id]['text'][:100]
                        }
                        for node_id in path
                    ]
                }
                for path in hlr_data['forward_paths']
            ]
        }
    
    # Format LLR paths
    for llr_id, llr_data in trace_paths['low_level_requirements'].items():
        formatted_paths['low_level_requirements'][llr_id] = {
            'id': llr_id,
            'text': llr_data['text'],
            'backward_paths': [
                {
                    'path_string': ' → '.join(path),
                    'path_details': [
                        {
                            'id': node_id,
                            'type': artifacts[node_id]['type'],
                            'text': artifacts[node_id]['text'][:100]
                        }
                        for node_id in path
                    ]
                }
                for path in llr_data['backward_paths']
            ]
        }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_paths, f, indent=2, ensure_ascii=False)


def generate_traceability_csv(analysis: Dict[str, Any], output_file: Path) -> None:
    """Generate traceability summary CSV table."""
    
    rows = []
    
    # System Requirements section
    sys_reqs = analysis['system_requirements']
    for req in sys_reqs['fully_implemented']['requirements']:
        rows.append({
            'Type': 'SYSTEM_REQ',
            'ID': req['id'],
            'Status': '✅ FULLY_IMPLEMENTED',
            'Details': f"Decomp: {req['decomposition_count']}, HLRs: {req['hlr_count']}, LLRs: {req['llr_count']}",
            'Issues': ''
        })
    
    for req in sys_reqs['partially_implemented']['requirements']:
        rows.append({
            'Type': 'SYSTEM_REQ',
            'ID': req['id'],
            'Status': '⚠️ PARTIALLY_IMPLEMENTED',
            'Details': f"Decomp: {req['decomposition_count']}, HLRs: {req['hlr_count']}, LLRs: {req['llr_count']}",
            'Issues': req['reason']
        })
    
    for req in sys_reqs['not_implemented']['requirements']:
        rows.append({
            'Type': 'SYSTEM_REQ',
            'ID': req['id'],
            'Status': '❌ NOT_IMPLEMENTED',
            'Details': '',
            'Issues': req['reason']
        })
    
    # HLR section
    hlrs = analysis['high_level_requirements']
    for req in hlrs['fully_implemented']['requirements']:
        rows.append({
            'Type': 'HLR',
            'ID': req['id'],
            'Status': '✅ FULLY_IMPLEMENTED',
            'Details': f"Parents: {req['parent_count']}, LLRs: {req['llr_count']}",
            'Issues': ''
        })
    
    for req in hlrs['partially_implemented']['requirements']:
        rows.append({
            'Type': 'HLR',
            'ID': req['id'],
            'Status': '⚠️ PARTIALLY_IMPLEMENTED',
            'Details': f"Parents: {req['parent_count']}, LLRs: {req['llr_count']}",
            'Issues': req['reason']
        })
    
    for req in hlrs['orphaned']['requirements']:
        rows.append({
            'Type': 'HLR',
            'ID': req['id'],
            'Status': '🔴 ORPHANED',
            'Details': '',
            'Issues': req['reason']
        })
    
    # LLR section
    llrs = analysis['low_level_requirements']
    for req in llrs['traced']['requirements']:
        rows.append({
            'Type': 'LLR',
            'ID': req['id'],
            'Status': '✅ TRACED',
            'Details': f"HLR Parents: {req['hlr_count']}",
            'Issues': ''
        })
    
    for req in llrs['orphaned']['requirements']:
        rows.append({
            'Type': 'LLR',
            'ID': req['id'],
            'Status': '🔴 ORPHANED',
            'Details': '',
            'Issues': req['reason']
        })
    
    # Write CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Type', 'ID', 'Status', 'Details', 'Issues'])
        writer.writeheader()
        writer.writerows(rows)


def generate_summary_report(
    analysis: Dict[str, Any],
    artifacts: Dict[str, Any],
    output_file: Path
) -> None:
    """Generate markdown summary report."""
    
    sys_reqs = analysis['system_requirements']
    hlrs = analysis['high_level_requirements']
    llrs = analysis['low_level_requirements']
    metrics = analysis['quality_metrics']
    
    report = f"""# Requirements Traceability Analysis Report

## Executive Summary

**Overall Implementation Rate:** {metrics['overall_implementation_rate']:.1f}%

- Total Requirements Analyzed: {metrics['total_requirements']}
- Successfully Implemented/Traced: {metrics['total_implemented']}
- Orphaned Requirements: {metrics['total_orphaned']}

---

## 1. System-Level Requirements

**Total:** {sys_reqs['total']}

### 1.1 Fully Implemented ({sys_reqs['fully_implemented']['count']} - {sys_reqs['fully_implemented']['percentage']:.1f}%)

"""
    
    for req in sys_reqs['fully_implemented']['requirements']:
        report += f"""
#### {req['id']}
- **Text:** {req['text'][:200]}...
- **Decomposition Count:** {req['decomposition_count']}
- **High-Level Requirements:** {req['hlr_count']}
- **Low-Level Requirements:** {req['llr_count']}
- **Trace Depth:** {req['trace_depth']}

"""
    
    report += f"""
### 1.2 Partially Implemented ({sys_reqs['partially_implemented']['count']} - {sys_reqs['partially_implemented']['percentage']:.1f}%)

"""
    
    for req in sys_reqs['partially_implemented']['requirements']:
        report += f"""
#### {req['id']}
- **Text:** {req['text'][:200]}...
- **Reason:** {req['reason']}
- **Has:** {', '.join(req['has'])}
- **Missing:** {', '.join(req['missing'])}
- **Current Counts:** Decomp: {req['decomposition_count']}, HLRs: {req['hlr_count']}, LLRs: {req['llr_count']}

"""
    
    report += f"""
### 1.3 Not Implemented ({sys_reqs['not_implemented']['count']} - {sys_reqs['not_implemented']['percentage']:.1f}%)

"""
    
    for req in sys_reqs['not_implemented']['requirements']:
        report += f"""
#### {req['id']}
- **Text:** {req['text'][:200]}...
- **Reason:** {req['reason']}
- **Missing:** {', '.join(req['missing'])}

"""
    
    report += f"""
---

## 2. High-Level Requirements

**Total:** {hlrs['total']}

### 2.1 Fully Implemented ({hlrs['fully_implemented']['count']} - {hlrs['fully_implemented']['percentage']:.1f}%)

"""
    
    for req in hlrs['fully_implemented']['requirements']:
        report += f"""
#### {req['id']}
- **Text:** {req['text'][:200]}...
- **Parent Links:** {req['parent_count']}
- **LLR Children:** {req['llr_count']}

"""
    
    report += f"""
### 2.2 Partially Implemented ({hlrs['partially_implemented']['count']} - {hlrs['partially_implemented']['percentage']:.1f}%)

"""
    
    for req in hlrs['partially_implemented']['requirements']:
        report += f"""
#### {req['id']}
- **Text:** {req['text'][:200]}...
- **Reason:** {req['reason']}
- **Has:** {', '.join(req['has'])}
- **Missing:** {', '.join(req['missing'])}

"""
    
    report += f"""
### 2.3 Orphaned ({hlrs['orphaned']['count']} - {hlrs['orphaned']['percentage']:.1f}%)

"""
    
    for req in hlrs['orphaned']['requirements']:
        report += f"""
#### {req['id']}
- **Text:** {req['text'][:200]}...
- **Reason:** {req['reason']}

"""
    
    report += f"""
---

## 3. Low-Level Requirements

**Total:** {llrs['total']}

### 3.1 Traced to HLRs ({llrs['traced']['count']} - {llrs['traced']['percentage']:.1f}%)

"""
    
    for req in llrs['traced']['requirements'][:10]:  # Show first 10
        report += f"""
#### {req['id']}
- **Text:** {req['text'][:200]}...
- **Mapped to HLRs:** {req['hlr_count']}

"""
    
    if len(llrs['traced']['requirements']) > 10:
        report += f"\n*... and {len(llrs['traced']['requirements']) - 10} more traced LLRs*\n"
    
    report += f"""
### 3.2 Orphaned ({llrs['orphaned']['count']} - {llrs['orphaned']['percentage']:.1f}%)

"""
    
    for req in llrs['orphaned']['requirements']:
        report += f"""
#### {req['id']}
- **Text:** {req['text'][:200]}...
- **Reason:** {req['reason']}

"""
    
    report += f"""
---

## 4. Quality Metrics Summary

| Metric | Value |
|--------|-------|
| Overall Implementation Rate | {metrics['overall_implementation_rate']:.1f}% |
| System Requirements Rate | {metrics['system_requirements_rate']:.1f}% |
| HLR Implementation Rate | {metrics['hlr_implementation_rate']:.1f}% |
| LLR Traceability Rate | {metrics['llr_traceability_rate']:.1f}% |
| Total Orphaned Requirements | {metrics['total_orphaned']} |

---

## 5. Recommendations

"""
    
    if sys_reqs['not_implemented']['count'] > 0:
        report += f"- **Action Required:** {sys_reqs['not_implemented']['count']} system requirements have no implementation. Create decomposition and link to HLRs.\n"
    
    if sys_reqs['partially_implemented']['count'] > 0:
        report += f"- **Action Required:** {sys_reqs['partially_implemented']['count']} system requirements are partially implemented. Complete the missing links.\n"
    
    if hlrs['orphaned']['count'] > 0:
        report += f"- **Action Required:** {hlrs['orphaned']['count']} HLRs are orphaned. Link them to system requirements.\n"
    
    if hlrs['partially_implemented']['count'] > 0:
        report += f"- **Improvement Needed:** {hlrs['partially_implemented']['count']} HLRs are partially implemented. Add missing LLR links.\n"
    
    if llrs['orphaned']['count'] > 0:
        report += f"- **Action Required:** {llrs['orphaned']['count']} LLRs are orphaned. Map them to appropriate HLRs.\n"
    
    if metrics['overall_implementation_rate'] >= 80:
        report += f"\n✅ **Overall Status:** Good traceability coverage ({metrics['overall_implementation_rate']:.1f}%)\n"
    elif metrics['overall_implementation_rate'] >= 60:
        report += f"\n⚠️ **Overall Status:** Moderate traceability coverage ({metrics['overall_implementation_rate']:.1f}%) - improvement needed\n"
    else:
        report += f"\n❌ **Overall Status:** Low traceability coverage ({metrics['overall_implementation_rate']:.1f}%) - significant work required\n"
    
    report += """
---

*Generated by Aerospace Traceability Engine*
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
