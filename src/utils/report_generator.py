"""Generate comprehensive traceability reports."""

from typing import Dict, List, Any
from pathlib import Path
import json
from datetime import datetime


def generate_traceability_matrix(
    artifacts: Dict[str, Any],
    links: List[Dict[str, Any]],
    analysis: Dict[str, Any],
    output_dir: str
) -> None:
    """
    Generate comprehensive traceability matrix showing:
    - System requirements
    - Their decomposed children
    - Linked HLRs
    - Linked LLRs
    - Trace status (FULL, PARTIAL, NONE)
    """
    
    # Build link graph for fast lookup
    link_graph = {}
    for link in links:
        source = link['source_id']
        target = link['target_id']
        if source not in link_graph:
            link_graph[source] = []
        link_graph[source].append(target)
    
    # Process each system requirement
    matrix_rows = []
    
    sys_reqs = [a for a in artifacts.values() if a['type'] == 'SYSTEM_REQ']
    sys_reqs.sort(key=lambda x: x['id'])
    
    for sys_req in sys_reqs:
        sys_id = sys_req['id']
        sys_text = sys_req['text']
        
        # Get decomposed children
        decomposed_ids = link_graph.get(sys_id, [])
        decomposed = [artifacts[d] for d in decomposed_ids if d in artifacts and artifacts[d]['type'] == 'SYSTEM_REQ_DECOMPOSED']
        
        if not decomposed:
            # No decomposition - check direct links
            matrix_rows.append({
                'system_req_id': sys_id,
                'system_req_text': sys_text,
                'decomposed_ids': [],
                'hlr_ids': [],
                'llr_ids': [],
                'variable_ids': [],
                'trace_status': 'NONE',
                'trace_depth': 0,
                'completeness': 0.0
            })
            continue
        
        # For each decomposed requirement, trace down
        all_hlrs = set()
        all_llrs = set()
        all_vars = set()
        
        for decomp in decomposed:
            decomp_id = decomp['id']
            
            # Get HLRs
            hlr_ids = link_graph.get(decomp_id, [])
            hlrs = [h for h in hlr_ids if h in artifacts and artifacts[h]['type'] == 'HLR']
            all_hlrs.update(hlrs)
            
            # Get LLRs from HLRs
            for hlr_id in hlrs:
                llr_ids = link_graph.get(hlr_id, [])
                llrs = [l for l in llr_ids if l in artifacts and artifacts[l]['type'] == 'LLR']
                all_llrs.update(llrs)
                
                # Get variables from LLRs
                for llr_id in llrs:
                    var_ids = link_graph.get(llr_id, [])
                    vars_ = [v for v in var_ids if v in artifacts and artifacts[v]['type'] == 'CODE_VAR']
                    all_vars.update(vars_)
        
        # Determine trace status
        trace_depth = 0
        if decomposed:
            trace_depth = 1
        if all_hlrs:
            trace_depth = 2
        if all_llrs:
            trace_depth = 3
        if all_vars:
            trace_depth = 4
        
        # FULL = reaches variables (depth 4)
        # PARTIAL = reaches HLR or LLR but not variables (depth 2-3)
        # NONE = no links beyond decomposition (depth 0-1)
        if trace_depth == 4:
            trace_status = 'FULL'
            completeness = 1.0
        elif trace_depth >= 2:
            trace_status = 'PARTIAL'
            completeness = trace_depth / 4.0
        else:
            trace_status = 'NONE'
            completeness = 0.0
        
        matrix_rows.append({
            'system_req_id': sys_id,
            'system_req_text': sys_text,
            'decomposed_ids': [d['id'] for d in decomposed],
            'hlr_ids': sorted(list(all_hlrs)),
            'llr_ids': sorted(list(all_llrs)),
            'variable_ids': sorted(list(all_vars)),
            'trace_status': trace_status,
            'trace_depth': trace_depth,
            'completeness': completeness
        })
    
    # Generate CSV
    csv_path = Path(output_dir) / "traceability_matrix.csv"
    with open(csv_path, 'w') as f:
        # Header
        f.write("System Req ID,System Req Text,Status,Decomposed IDs,HLR IDs,LLR IDs,Variable IDs,Completeness\n")
        
        for row in matrix_rows:
            f.write(f'"{row["system_req_id"]}",')
            f.write(f'"{row["system_req_text"][:100]}...",')
            f.write(f'"{row["trace_status"]}",')
            f.write(f'"{"; ".join(row["decomposed_ids"])}",')
            f.write(f'"{"; ".join(row["hlr_ids"])}",')
            f.write(f'"{"; ".join(row["llr_ids"])}",')
            f.write(f'"{"; ".join(row["variable_ids"])}",')
            f.write(f'{row["completeness"]:.2f}\n')
    
    print(f"✓ Traceability matrix saved to: {csv_path}")
    
    # Generate detailed JSON
    json_path = Path(output_dir) / "traceability_matrix.json"
    with open(json_path, 'w') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'matrix': matrix_rows,
            'summary': {
                'total_system_reqs': len(sys_reqs),
                'full_trace': sum(1 for r in matrix_rows if r['trace_status'] == 'FULL'),
                'partial_trace': sum(1 for r in matrix_rows if r['trace_status'] == 'PARTIAL'),
                'no_trace': sum(1 for r in matrix_rows if r['trace_status'] == 'NONE'),
                'average_completeness': sum(r['completeness'] for r in matrix_rows) / len(matrix_rows) if matrix_rows else 0.0
            }
        }, f, indent=2)
    
    print(f"✓ Detailed matrix saved to: {json_path}")
    
    return matrix_rows


def generate_final_report(
    artifacts: Dict[str, Any],
    links: List[Dict[str, Any]],
    analysis: Dict[str, Any],
    matrix_rows: List[Dict[str, Any]],
    output_dir: str,
    api_stats: Dict[str, Any] = None
) -> None:
    """Generate clean final report."""
    
    report_path = Path(output_dir) / "TRACEABILITY_REPORT.md"
    
    # Calculate statistics
    sys_reqs = [a for a in artifacts.values() if a['type'] == 'SYSTEM_REQ']
    decomposed = [a for a in artifacts.values() if a['type'] == 'SYSTEM_REQ_DECOMPOSED']
    hlrs = [a for a in artifacts.values() if a['type'] == 'HLR']
    llrs = [a for a in artifacts.values() if a['type'] == 'LLR']
    vars_ = [a for a in artifacts.values() if a['type'] == 'CODE_VAR']
    
    full_trace = sum(1 for r in matrix_rows if r['trace_status'] == 'FULL')
    partial_trace = sum(1 for r in matrix_rows if r['trace_status'] == 'PARTIAL')
    no_trace = sum(1 for r in matrix_rows if r['trace_status'] == 'NONE')
    
    avg_completeness = sum(r['completeness'] for r in matrix_rows) / len(matrix_rows) if matrix_rows else 0.0
    
    gaps = analysis.get('gaps', [])
    critical_gaps = [g for g in gaps if g.get('severity') == 'critical']
    high_gaps = [g for g in gaps if g.get('severity') == 'high']
    
    # Link quality statistics
    high_conf_links = sum(1 for l in links if l['confidence'] >= 0.70)
    med_conf_links = sum(1 for l in links if 0.50 <= l['confidence'] < 0.70)
    low_conf_links = sum(1 for l in links if 0.35 <= l['confidence'] < 0.50)
    avg_link_confidence = sum(l['confidence'] for l in links) / len(links) if links else 0.0
    
    # Generate report
    with open(report_path, 'w') as f:
        f.write("# Requirements Traceability Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        # Executive Summary
        f.write("## Executive Summary\n\n")
        f.write(f"This report provides a comprehensive analysis of requirements traceability ")
        f.write(f"from system-level requirements down to implementation variables.\n\n")
        
        status_emoji = "🟢" if avg_completeness >= 0.8 else "🟡" if avg_completeness >= 0.5 else "🔴"
        quality_emoji = "🟢" if avg_link_confidence >= 0.65 else "🟡" if avg_link_confidence >= 0.50 else "🔴"
        
        f.write(f"**Overall Traceability Status:** {status_emoji} **{avg_completeness*100:.1f}%** complete\n\n")
        f.write(f"**Link Quality:** {quality_emoji} **{avg_link_confidence:.2f}** average confidence\n\n")
        
        # Artifact Summary
        f.write("## Artifact Inventory\n\n")
        f.write("| Artifact Type | Count |\n")
        f.write("|---------------|-------|\n")
        f.write(f"| System Requirements | {len(sys_reqs)} |\n")
        f.write(f"| Decomposed Requirements | {len(decomposed)} |\n")
        f.write(f"| High-Level Requirements (HLR) | {len(hlrs)} |\n")
        f.write(f"| Low-Level Requirements (LLR) | {len(llrs)} |\n")
        f.write(f"| Code Variables | {len(vars_)} |\n")
        f.write(f"| **Total Artifacts** | **{len(artifacts)}** |\n")
        f.write(f"| **Total Links** | **{len(links)}** |\n\n")
        
        # Link Quality Distribution
        f.write("### Link Quality Distribution\n\n")
        f.write(f"The system uses multi-dimensional quality validation requiring at least 2 independent ")
        f.write(f"signals (embedding similarity, keywords, ID hierarchy, variable names, quantities) ")
        f.write(f"before establishing a link.\n\n")
        f.write("| Quality Band | Count | Percentage |\n")
        f.write("|--------------|-------|------------|\n")
        f.write(f"| 🟢 High Confidence (≥0.70) | {high_conf_links} | {high_conf_links/len(links)*100:.1f}% |\n")
        f.write(f"| 🟡 Medium Confidence (0.50-0.69) | {med_conf_links} | {med_conf_links/len(links)*100:.1f}% |\n")
        f.write(f"| 🔴 Low Confidence (0.35-0.49) | {low_conf_links} | {low_conf_links/len(links)*100:.1f}% |\n")
        f.write(f"| **Average Link Confidence** | **{avg_link_confidence:.3f}** | - |\n\n")
        
        # Traceability Status
        f.write("## Traceability Status\n\n")
        f.write("### System Requirements Trace Coverage\n\n")
        f.write(f"- 🟢 **FULL Trace** (SYS → DECOMP → HLR → LLR → VAR): **{full_trace}** requirements ({full_trace/len(sys_reqs)*100:.1f}%)\n")
        f.write(f"- 🟡 **PARTIAL Trace** (incomplete chain): **{partial_trace}** requirements ({partial_trace/len(sys_reqs)*100:.1f}%)\n")
        f.write(f"- 🔴 **NO Trace** (orphaned): **{no_trace}** requirements ({no_trace/len(sys_reqs)*100:.1f}%)\n\n")
        
        # Coverage bar chart
        f.write("```\n")
        f.write("Coverage Distribution:\n")
        full_bar = "█" * int(full_trace / len(sys_reqs) * 40)
        partial_bar = "█" * int(partial_trace / len(sys_reqs) * 40)
        none_bar = "█" * int(no_trace / len(sys_reqs) * 40)
        f.write(f"FULL:    [{full_bar:<40}] {full_trace}/{len(sys_reqs)}\n")
        f.write(f"PARTIAL: [{partial_bar:<40}] {partial_trace}/{len(sys_reqs)}\n")
        f.write(f"NONE:    [{none_bar:<40}] {no_trace}/{len(sys_reqs)}\n")
        f.write("```\n\n")
        
        # Detailed Traceability Matrix
        f.write("## Detailed Traceability Matrix\n\n")
        f.write("| System Req | Status | HLRs | LLRs | Variables | Completeness |\n")
        f.write("|------------|--------|------|------|-----------|-------------|\n")
        
        for row in matrix_rows:
            status_icon = "🟢" if row['trace_status'] == 'FULL' else "🟡" if row['trace_status'] == 'PARTIAL' else "🔴"
            f.write(f"| {row['system_req_id']} | {status_icon} {row['trace_status']} | ")
            f.write(f"{len(row['hlr_ids'])} | {len(row['llr_ids'])} | {len(row['variable_ids'])} | ")
            f.write(f"{row['completeness']*100:.0f}% |\n")
        
        f.write("\n")
        
        # Gap Analysis
        f.write("## Gap Analysis\n\n")
        f.write(f"**Total Gaps Identified:** {len(gaps)}\n\n")
        
        if gaps:
            f.write(f"- 🔴 **Critical:** {len(critical_gaps)}\n")
            f.write(f"- 🟠 **High:** {len(high_gaps)}\n")
            f.write(f"- 🟡 **Medium:** {len(gaps) - len(critical_gaps) - len(high_gaps)}\n\n")
            
            if critical_gaps:
                f.write("### Critical Gaps (Immediate Action Required)\n\n")
                for gap in critical_gaps[:10]:  # Top 10
                    f.write(f"**{gap['gap_id']}** - {gap['description']}\n")
                    if gap.get('reasoning'):
                        f.write(f"> {gap['reasoning'][:200]}...\n")
                    f.write("\n")
        else:
            f.write("✅ **No gaps identified!** All requirements are properly traced.\n\n")
        
        # Requirements Details
        f.write("## System Requirements Detail\n\n")
        for row in matrix_rows:
            sys_id = row['system_req_id']
            sys_text = row['system_req_text']
            status = row['trace_status']
            
            status_icon = "🟢" if status == 'FULL' else "🟡" if status == 'PARTIAL' else "🔴"
            
            f.write(f"### {sys_id} {status_icon}\n\n")
            f.write(f"**Requirement:** {sys_text}\n\n")
            f.write(f"**Trace Status:** {status} ({row['completeness']*100:.0f}% complete)\n\n")
            
            if row['decomposed_ids']:
                f.write(f"**Decomposed to:** {', '.join(row['decomposed_ids'])}\n\n")
            
            if row['hlr_ids']:
                f.write(f"**High-Level Requirements ({len(row['hlr_ids'])}):**\n")
                for hlr_id in row['hlr_ids'][:5]:  # Show first 5
                    f.write(f"- {hlr_id}\n")
                if len(row['hlr_ids']) > 5:
                    f.write(f"- ... and {len(row['hlr_ids'])-5} more\n")
                f.write("\n")
            
            if row['llr_ids']:
                f.write(f"**Low-Level Requirements ({len(row['llr_ids'])}):**\n")
                for llr_id in row['llr_ids'][:5]:
                    f.write(f"- {llr_id}\n")
                if len(row['llr_ids']) > 5:
                    f.write(f"- ... and {len(row['llr_ids'])-5} more\n")
                f.write("\n")
            
            if row['variable_ids']:
                f.write(f"**Variables ({len(row['variable_ids'])}):** {', '.join(row['variable_ids'])}\n\n")
            
            f.write("---\n\n")
        
        # API Usage (if available)
        if api_stats:
            f.write("## Analysis Metrics\n\n")
            f.write(f"**API Calls Made:** {api_stats.get('total_calls', 0)}\n\n")
            f.write(f"**Tokens Used:** {api_stats.get('total_tokens', 0):,}\n")
            f.write(f"- Input: {api_stats.get('total_tokens_input', 0):,}\n")
            f.write(f"- Output: {api_stats.get('total_tokens_output', 0):,}\n\n")
            f.write(f"**Analysis Time:** {api_stats.get('elapsed_seconds', 0):.1f} seconds\n\n")
        
        # Recommendations
        f.write("## Recommendations\n\n")
        if full_trace == len(sys_reqs):
            f.write("✅ **Excellent!** All system requirements have complete traceability chains.\n\n")
        elif avg_completeness >= 0.8:
            f.write("🟢 **Good coverage.** Minor gaps exist but overall traceability is strong.\n\n")
            f.write("**Actions:**\n")
            f.write(f"1. Review {partial_trace} partially traced requirements\n")
            f.write(f"2. Complete trace chains to implementation level\n\n")
        elif avg_completeness >= 0.5:
            f.write("🟡 **Moderate coverage.** Significant traceability gaps exist.\n\n")
            f.write("**Actions:**\n")
            f.write(f"1. Address {critical_gaps.__len__()} critical gaps immediately\n")
            f.write(f"2. Review {no_trace} untraced requirements\n")
            f.write(f"3. Strengthen links between HLR and LLR levels\n\n")
        else:
            f.write("🔴 **Poor coverage.** Major traceability issues detected.\n\n")
            f.write("**Immediate Actions Required:**\n")
            f.write(f"1. Establish baseline traceability for {no_trace} orphaned requirements\n")
            f.write(f"2. Address all {len(critical_gaps)} critical gaps\n")
            f.write(f"3. Review requirement structure and linking methodology\n\n")
        
        # Files Generated
        f.write("## Output Files\n\n")
        f.write("This analysis generated the following files:\n\n")
        f.write("- `traceability_matrix.csv` - CSV matrix for Excel/analysis\n")
        f.write("- `traceability_matrix.json` - Detailed JSON with full data\n")
        f.write("- `trace_graph.html` - Interactive visualization\n")
        f.write("- `trace_table.html` - Searchable web table\n")
        f.write("- `analysis.json` - Raw analysis data\n")
        f.write("- `gaps.json` - Detailed gap information\n")
        f.write("- `links.json` - All trace links\n")
        f.write("- `api_calls.json` - API usage tracking\n")
        f.write("- `TRACEABILITY_REPORT.md` - This report\n\n")
        
        f.write("---\n\n")
        f.write("*Report generated by Aerospace Requirements Traceability Engine*\n")
    
    print(f"✓ Final report saved to: {report_path}")
