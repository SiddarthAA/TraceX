"""Trace graph analysis and gap detection."""

from typing import Dict, List, Any, Set, Tuple
from datetime import datetime
from src.utils.id_utils import get_expected_parent_type, get_expected_child_type


# Expected trace chain depths
EXPECTED_CHAIN_DEPTH = {
    'SYSTEM_REQ': 5,
    'SYSTEM_REQ_DECOMPOSED': 4,
    'HLR': 3,
    'LLR': 2,
    'CODE_VAR': 1
}

EXPECTED_TERMINAL_TYPE = {
    'SYSTEM_REQ': 'CODE_VAR',
    'SYSTEM_REQ_DECOMPOSED': 'CODE_VAR',
    'HLR': 'CODE_VAR',
    'LLR': 'CODE_VAR'
}


def build_trace_graph(artifacts: Dict[str, Any], links: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build in-memory graph structure from artifacts and links."""
    
    graph = {
        'nodes': artifacts,
        'edges_down': {},  # parent_id -> [child_ids]
        'edges_up': {}     # child_id -> [parent_ids]
    }
    
    # Build edges from links
    for link in links:
        source_id = link['source_id']
        target_id = link['target_id']
        
        # Forward edges (down)
        if source_id not in graph['edges_down']:
            graph['edges_down'][source_id] = []
        graph['edges_down'][source_id].append(target_id)
        
        # Backward edges (up)
        if target_id not in graph['edges_up']:
            graph['edges_up'][target_id] = []
        graph['edges_up'][target_id].append(source_id)
    
    return graph


def trace_chain_forward(graph: Dict[str, Any], start_id: str) -> List[List[str]]:
    """Find all complete trace chains from a starting node using DFS."""
    
    chains = []
    
    def dfs(node_id: str, path: List[str]):
        current_path = path + [node_id]
        children = graph['edges_down'].get(node_id, [])
        
        if not children:
            # Leaf node - complete chain
            chains.append(current_path)
        else:
            # Continue traversal
            for child_id in children:
                dfs(child_id, current_path)
    
    dfs(start_id, [])
    return chains


def classify_chain(chain: List[str], graph: Dict[str, Any]) -> str:
    """
    Classify a trace chain as COMPLETE, PARTIAL, or INCOMPLETE.
    """
    if not chain:
        return 'INCOMPLETE'
    
    start_id = chain[0]
    terminal_id = chain[-1]
    
    start_type = graph['nodes'][start_id]['type']
    terminal_type = graph['nodes'][terminal_id]['type']
    
    expected_depth = EXPECTED_CHAIN_DEPTH.get(start_type, 1)
    expected_terminal = EXPECTED_TERMINAL_TYPE.get(start_type, 'CODE_VAR')
    
    actual_depth = len(chain)
    
    # Complete: reaches expected terminal type and depth
    if terminal_type == expected_terminal and actual_depth >= expected_depth:
        return 'COMPLETE'
    
    # Partial: has some depth but not complete
    elif actual_depth > 1 and actual_depth < expected_depth:
        return 'PARTIAL'
    
    # Incomplete: no children at all
    elif actual_depth == 1:
        return 'INCOMPLETE'
    
    # Broken: unexpected terminal type
    else:
        return 'BROKEN'


def compute_coverage_metrics(
    graph: Dict[str, Any],
    artifacts: Dict[str, Any]
) -> Dict[str, Any]:
    """Compute coverage metrics at each level."""
    
    metrics = {}
    
    # Group artifacts by type
    by_type = {}
    for art_id, artifact in artifacts.items():
        art_type = artifact['type']
        if art_type not in by_type:
            by_type[art_type] = []
        by_type[art_type].append(artifact)
    
    # System Requirement Coverage
    sys_reqs = by_type.get('SYSTEM_REQ', [])
    sys_with_children = [s for s in sys_reqs if graph['edges_down'].get(s['id'], [])]
    metrics['system_req_coverage'] = {
        'total': len(sys_reqs),
        'with_decomposition': len(sys_with_children),
        'percentage': (len(sys_with_children) / len(sys_reqs) * 100) if sys_reqs else 0.0
    }
    
    # Decomposed to HLR Coverage
    decomposed = by_type.get('SYSTEM_REQ_DECOMPOSED', [])
    decomposed_with_hlr = [d for d in decomposed if graph['edges_down'].get(d['id'], [])]
    metrics['decomposed_to_hlr'] = {
        'total': len(decomposed),
        'with_hlr_link': len(decomposed_with_hlr),
        'percentage': (len(decomposed_with_hlr) / len(decomposed) * 100) if decomposed else 0.0
    }
    
    # HLR Coverage
    hlrs = by_type.get('HLR', [])
    hlrs_with_parent = [h for h in hlrs if graph['edges_up'].get(h['id'], [])]
    hlrs_with_child = [h for h in hlrs if graph['edges_down'].get(h['id'], [])]
    hlrs_fully_linked = [h for h in hlrs if h in hlrs_with_parent and h in hlrs_with_child]
    metrics['hlr_coverage'] = {
        'total': len(hlrs),
        'with_parent': len(hlrs_with_parent),
        'with_children': len(hlrs_with_child),
        'fully_linked': len(hlrs_fully_linked),
        'parent_percentage': (len(hlrs_with_parent) / len(hlrs) * 100) if hlrs else 0.0,
        'child_percentage': (len(hlrs_with_child) / len(hlrs) * 100) if hlrs else 0.0
    }
    
    # LLR Coverage
    llrs = by_type.get('LLR', [])
    llrs_with_parent = [l for l in llrs if graph['edges_up'].get(l['id'], [])]
    llrs_with_child = [l for l in llrs if graph['edges_down'].get(l['id'], [])]
    llrs_fully_linked = [l for l in llrs if l in llrs_with_parent and l in llrs_with_child]
    metrics['llr_coverage'] = {
        'total': len(llrs),
        'with_parent': len(llrs_with_parent),
        'with_children': len(llrs_with_child),
        'fully_linked': len(llrs_fully_linked),
        'parent_percentage': (len(llrs_with_parent) / len(llrs) * 100) if llrs else 0.0,
        'child_percentage': (len(llrs_with_child) / len(llrs) * 100) if llrs else 0.0
    }
    
    # Variable Coverage
    variables = by_type.get('CODE_VAR', [])
    vars_with_parent = [v for v in variables if graph['edges_up'].get(v['id'], [])]
    metrics['variable_coverage'] = {
        'total': len(variables),
        'traced': len(vars_with_parent),
        'orphaned': len(variables) - len(vars_with_parent),
        'percentage': (len(vars_with_parent) / len(variables) * 100) if variables else 0.0
    }
    
    return metrics


def find_orphans(graph: Dict[str, Any], artifacts: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Identify orphaned artifacts."""
    
    orphans = {
        'no_parent': [],
        'no_children': [],
        'isolated': []
    }
    
    TYPES_REQUIRING_PARENT = ['HLR', 'LLR', 'CODE_VAR']
    TYPES_REQUIRING_CHILDREN = ['SYSTEM_REQ', 'SYSTEM_REQ_DECOMPOSED', 'HLR', 'LLR']
    
    for art_id, artifact in artifacts.items():
        art_type = artifact['type']
        parents = graph['edges_up'].get(art_id, [])
        children = graph['edges_down'].get(art_id, [])
        
        # Check for missing parent
        if art_type in TYPES_REQUIRING_PARENT and not parents:
            orphans['no_parent'].append({
                'artifact_id': art_id,
                'type': art_type,
                'expected_parent_type': get_expected_parent_type(art_type),
                'reason': f"{art_type} has no parent link"
            })
        
        # Check for missing children
        if art_type in TYPES_REQUIRING_CHILDREN and not children:
            orphans['no_children'].append({
                'artifact_id': art_id,
                'type': art_type,
                'expected_child_type': get_expected_child_type(art_type),
                'reason': f"{art_type} has no child links"
            })
        
        # Check for isolation
        if not parents and not children and art_type != 'SYSTEM_REQ':
            orphans['isolated'].append({
                'artifact_id': art_id,
                'type': art_type,
                'reason': "Artifact has no links at all"
            })
    
    return orphans


def identify_gaps(
    graph: Dict[str, Any],
    artifacts: Dict[str, Any],
    orphans: Dict[str, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """Identify all traceability gaps."""
    
    gaps = []
    gap_counter = 1
    
    # Gap Type 1: Orphaned artifacts with no parent
    for orphan in orphans['no_parent']:
        gap = {
            'gap_id': f"GAP-{gap_counter:03d}",
            'type': 'orphan_no_parent',
            'severity': 'high',
            'artifact_id': orphan['artifact_id'],
            'artifact_type': orphan['type'],
            'expected_parent_type': orphan['expected_parent_type'],
            'description': f"{orphan['type']} has no parent link",
            'reason': orphan['reason']
        }
        gaps.append(gap)
        gap_counter += 1
    
    # Gap Type 2: Artifacts with no children (dead ends)
    for orphan in orphans['no_children']:
        # Determine severity based on type
        severity = 'medium'
        if orphan['type'] in ['SYSTEM_REQ', 'SYSTEM_REQ_DECOMPOSED']:
            severity = 'critical'
        elif orphan['type'] == 'HLR':
            severity = 'high'
        
        gap = {
            'gap_id': f"GAP-{gap_counter:03d}",
            'type': 'orphan_no_children',
            'severity': severity,
            'artifact_id': orphan['artifact_id'],
            'artifact_type': orphan['type'],
            'expected_child_type': orphan['expected_child_type'],
            'description': f"{orphan['type']} has no child links",
            'reason': orphan['reason']
        }
        gaps.append(gap)
        gap_counter += 1
    
    # Gap Type 3: Incomplete chains
    sys_reqs = [a for a in artifacts.values() if a['type'] == 'SYSTEM_REQ']
    for sys_req in sys_reqs:
        chains = trace_chain_forward(graph, sys_req['id'])
        for chain in chains:
            classification = classify_chain(chain, graph)
            if classification in ['INCOMPLETE', 'PARTIAL', 'BROKEN']:
                gap = {
                    'gap_id': f"GAP-{gap_counter:03d}",
                    'type': 'incomplete_chain',
                    'severity': 'high' if classification == 'INCOMPLETE' else 'medium',
                    'chain': chain,
                    'classification': classification,
                    'break_point': chain[-1],
                    'expected_depth': EXPECTED_CHAIN_DEPTH[sys_req['type']],
                    'actual_depth': len(chain),
                    'description': f"Incomplete trace chain from {sys_req['id']}"
                }
                gaps.append(gap)
                gap_counter += 1
    
    return gaps


def analyze_traceability(
    artifacts: Dict[str, Any],
    links: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Perform complete traceability analysis.
    
    Returns analysis report.
    """
    print("Analyzing traceability...")
    
    # Build graph
    graph = build_trace_graph(artifacts, links)
    
    # Compute coverage metrics
    metrics = compute_coverage_metrics(graph, artifacts)
    
    # Find orphans
    orphans = find_orphans(graph, artifacts)
    
    # Identify gaps
    gaps = identify_gaps(graph, artifacts, orphans)
    
    # Compute end-to-end coverage
    sys_reqs = [a for a in artifacts.values() if a['type'] == 'SYSTEM_REQ']
    complete_chains = 0
    partial_chains = 0
    incomplete_chains = 0
    
    for sys_req in sys_reqs:
        chains = trace_chain_forward(graph, sys_req['id'])
        for chain in chains:
            classification = classify_chain(chain, graph)
            if classification == 'COMPLETE':
                complete_chains += 1
            elif classification == 'PARTIAL':
                partial_chains += 1
            else:
                incomplete_chains += 1
    
    total_chains = complete_chains + partial_chains + incomplete_chains
    
    metrics['end_to_end'] = {
        'total_chains': total_chains,
        'complete': complete_chains,
        'partial': partial_chains,
        'incomplete': incomplete_chains,
        'complete_percentage': (complete_chains / total_chains * 100) if total_chains else 0.0
    }
    
    # Build analysis report
    analysis = {
        'analysis_timestamp': datetime.utcnow().isoformat() + 'Z',
        'artifact_counts': {
            'system_req': len([a for a in artifacts.values() if a['type'] == 'SYSTEM_REQ']),
            'system_req_decomposed': len([a for a in artifacts.values() if a['type'] == 'SYSTEM_REQ_DECOMPOSED']),
            'hlr': len([a for a in artifacts.values() if a['type'] == 'HLR']),
            'llr': len([a for a in artifacts.values() if a['type'] == 'LLR']),
            'code_var': len([a for a in artifacts.values() if a['type'] == 'CODE_VAR']),
            'total': len(artifacts)
        },
        'link_counts': {
            'total': len(links)
        },
        'coverage_metrics': metrics,
        'orphans': orphans,
        'gaps': gaps,
        'gap_summary': {
            'total': len(gaps),
            'critical': len([g for g in gaps if g['severity'] == 'critical']),
            'high': len([g for g in gaps if g['severity'] == 'high']),
            'medium': len([g for g in gaps if g['severity'] == 'medium']),
            'low': len([g for g in gaps if g['severity'] == 'low'])
        }
    }
    
    print(f"  Found {len(gaps)} gaps")
    print(f"  Coverage: {metrics['end_to_end']['complete_percentage']:.1f}% complete chains")
    
    return analysis
