"""
Unified Analysis Module
Provides consistent analysis across all outputs with detailed reasoning.
"""

from typing import Dict, Any, List, Tuple
from collections import defaultdict


def analyze_unified_traceability(
    artifacts: Dict[str, Any],
    links: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Perform unified traceability analysis with consistent logic.
    
    Returns a comprehensive analysis structure that feeds into all output formats.
    """
    
    # Build graph structures
    graph = _build_graph(artifacts, links)
    
    # Analyze each layer with consistent logic
    system_reqs_analysis = _analyze_system_requirements(artifacts, graph)
    hlr_analysis = _analyze_high_level_requirements(artifacts, graph)
    llr_analysis = _analyze_low_level_requirements(artifacts, graph)
    
    # Build trace paths for all requirements
    trace_paths = _build_all_trace_paths(artifacts, graph)
    
    # Generate quality metrics
    quality_metrics = _calculate_quality_metrics(
        system_reqs_analysis,
        hlr_analysis,
        llr_analysis,
        trace_paths
    )
    
    return {
        'system_requirements': system_reqs_analysis,
        'high_level_requirements': hlr_analysis,
        'low_level_requirements': llr_analysis,
        'trace_paths': trace_paths,
        'quality_metrics': quality_metrics,
        'metadata': {
            'total_artifacts': len(artifacts),
            'total_links': len(links),
            'has_variables': any(a['type'] == 'CODE_VAR' for a in artifacts.values())
        }
    }


def _build_graph(
    artifacts: Dict[str, Any],
    links: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build bidirectional graph from artifacts and links."""
    
    edges_down = defaultdict(list)  # parent -> children
    edges_up = defaultdict(list)    # child -> parents
    
    for link in links:
        # Handle both 'source'/'target' and 'source_id'/'target_id' formats
        source = link.get('source') or link.get('source_id')
        target = link.get('target') or link.get('target_id')
        
        if source and target:
            edges_down[source].append(target)
            edges_up[target].append(source)
    
    return {
        'edges_down': edges_down,
        'edges_up': edges_up,
        'artifacts': artifacts
    }


def _analyze_system_requirements(
    artifacts: Dict[str, Any],
    graph: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze system requirements implementation status.
    
    Classification:
    - FULLY_IMPLEMENTED: Has decomposition → HLRs → LLRs (complete chain)
    - PARTIALLY_IMPLEMENTED: Has some links but chain is incomplete
    - NOT_IMPLEMENTED: No decomposition or no downstream links
    """
    
    sys_reqs = [a for a in artifacts.values() if a['type'] == 'SYSTEM_REQ']
    
    fully_implemented = []
    partially_implemented = []
    not_implemented = []
    
    for sys_req in sys_reqs:
        sys_id = sys_req['id']
        
        # Check for decomposition
        decomp_children = _get_children_of_type(
            sys_id, 'SYSTEM_REQ_DECOMPOSED', graph, artifacts
        )
        
        if not decomp_children:
            not_implemented.append({
                'id': sys_id,
                'text': sys_req['text'],
                'reason': 'No decomposition found',
                'missing': ['decomposition', 'HLRs', 'LLRs']
            })
            continue
        
        # Get all HLRs through decomposition
        all_hlrs = []
        for decomp_id in decomp_children:
            hlrs = _get_children_of_type(decomp_id, 'HLR', graph, artifacts)
            all_hlrs.extend(hlrs)
        
        if not all_hlrs:
            partially_implemented.append({
                'id': sys_id,
                'text': sys_req['text'],
                'reason': 'Has decomposition but no HLRs linked',
                'has': ['decomposition'],
                'missing': ['HLRs', 'LLRs'],
                'decomposition_count': len(decomp_children),
                'hlr_count': 0,
                'llr_count': 0
            })
            continue
        
        # Get all LLRs through HLRs
        all_llrs = []
        for hlr_id in all_hlrs:
            llrs = _get_children_of_type(hlr_id, 'LLR', graph, artifacts)
            all_llrs.extend(llrs)
        
        if not all_llrs:
            partially_implemented.append({
                'id': sys_id,
                'text': sys_req['text'],
                'reason': 'Has decomposition and HLRs but no LLRs linked',
                'has': ['decomposition', 'HLRs'],
                'missing': ['LLRs'],
                'decomposition_count': len(decomp_children),
                'hlr_count': len(all_hlrs),
                'llr_count': 0
            })
            continue
        
        # Fully implemented
        fully_implemented.append({
            'id': sys_id,
            'text': sys_req['text'],
            'decomposition_count': len(decomp_children),
            'hlr_count': len(all_hlrs),
            'llr_count': len(all_llrs),
            'trace_depth': 'SYSTEM → DECOMP → HLR → LLR'
        })
    
    total = len(sys_reqs)
    return {
        'total': total,
        'fully_implemented': {
            'count': len(fully_implemented),
            'percentage': (len(fully_implemented) / total * 100) if total > 0 else 0,
            'requirements': fully_implemented
        },
        'partially_implemented': {
            'count': len(partially_implemented),
            'percentage': (len(partially_implemented) / total * 100) if total > 0 else 0,
            'requirements': partially_implemented
        },
        'not_implemented': {
            'count': len(not_implemented),
            'percentage': (len(not_implemented) / total * 100) if total > 0 else 0,
            'requirements': not_implemented
        }
    }


def _analyze_high_level_requirements(
    artifacts: Dict[str, Any],
    graph: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze HLR implementation status.
    
    Classification:
    - FULLY_IMPLEMENTED: Has parent (decomp/sys) AND has LLR children
    - PARTIALLY_IMPLEMENTED: Has parent OR has LLR children (not both)
    - ORPHANED: No parent and no children
    """
    
    hlrs = [a for a in artifacts.values() if a['type'] == 'HLR']
    
    fully_implemented = []
    partially_implemented = []
    orphaned = []
    
    for hlr in hlrs:
        hlr_id = hlr['id']
        
        # Check for parent (SYSTEM_REQ_DECOMPOSED or SYSTEM_REQ)
        parents = graph['edges_up'].get(hlr_id, [])
        valid_parents = [
            p for p in parents 
            if artifacts[p]['type'] in ['SYSTEM_REQ_DECOMPOSED', 'SYSTEM_REQ']
        ]
        
        # Check for LLR children
        llr_children = _get_children_of_type(hlr_id, 'LLR', graph, artifacts)
        
        if valid_parents and llr_children:
            fully_implemented.append({
                'id': hlr_id,
                'text': hlr['text'],
                'parent_count': len(valid_parents),
                'llr_count': len(llr_children)
            })
        elif valid_parents or llr_children:
            reason_parts = []
            has = []
            missing = []
            
            if not valid_parents:
                reason_parts.append('No parent link (orphaned from system requirements)')
                missing.append('parent_link')
            else:
                has.append('parent_link')
            
            if not llr_children:
                reason_parts.append('No LLR children (not decomposed to low-level)')
                missing.append('LLR_children')
            else:
                has.append('LLR_children')
            
            partially_implemented.append({
                'id': hlr_id,
                'text': hlr['text'],
                'reason': '; '.join(reason_parts),
                'has': has,
                'missing': missing,
                'parent_count': len(valid_parents),
                'llr_count': len(llr_children)
            })
        else:
            orphaned.append({
                'id': hlr_id,
                'text': hlr['text'],
                'reason': 'Completely isolated - no parent and no children'
            })
    
    total = len(hlrs)
    return {
        'total': total,
        'fully_implemented': {
            'count': len(fully_implemented),
            'percentage': (len(fully_implemented) / total * 100) if total > 0 else 0,
            'requirements': fully_implemented
        },
        'partially_implemented': {
            'count': len(partially_implemented),
            'percentage': (len(partially_implemented) / total * 100) if total > 0 else 0,
            'requirements': partially_implemented
        },
        'orphaned': {
            'count': len(orphaned),
            'percentage': (len(orphaned) / total * 100) if total > 0 else 0,
            'requirements': orphaned
        }
    }


def _analyze_low_level_requirements(
    artifacts: Dict[str, Any],
    graph: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze LLR traceability status.
    
    Classification (simple):
    - TRACED: Has HLR parent (mapped to higher level)
    - ORPHANED: No HLR parent (not mapped)
    
    Note: LLRs are the leaf nodes, so we only check if they're mapped to HLRs.
    """
    
    llrs = [a for a in artifacts.values() if a['type'] == 'LLR']
    
    traced = []
    orphaned = []
    
    for llr in llrs:
        llr_id = llr['id']
        
        # Check for HLR parent
        parents = graph['edges_up'].get(llr_id, [])
        hlr_parents = [p for p in parents if artifacts[p]['type'] == 'HLR']
        
        if hlr_parents:
            traced.append({
                'id': llr_id,
                'text': llr['text'],
                'hlr_count': len(hlr_parents),
                'parent_hlrs': hlr_parents
            })
        else:
            orphaned.append({
                'id': llr_id,
                'text': llr['text'],
                'reason': 'Not mapped to any HLR'
            })
    
    total = len(llrs)
    return {
        'total': total,
        'traced': {
            'count': len(traced),
            'percentage': (len(traced) / total * 100) if total > 0 else 0,
            'requirements': traced
        },
        'orphaned': {
            'count': len(orphaned),
            'percentage': (len(orphaned) / total * 100) if total > 0 else 0,
            'requirements': orphaned
        }
    }


def _build_all_trace_paths(
    artifacts: Dict[str, Any],
    graph: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build complete trace paths for all requirements.
    
    Returns paths for:
    - System requirements (forward trace: SYS → DECOMP → HLR → LLR)
    - High-level requirements (backward: HLR → DECOMP → SYS; forward: HLR → LLR)
    - Low-level requirements (backward trace: LLR → HLR → DECOMP → SYS)
    """
    
    sys_paths = {}
    hlr_paths = {}
    llr_paths = {}
    
    # System requirement paths (forward)
    sys_reqs = [a for a in artifacts.values() if a['type'] == 'SYSTEM_REQ']
    for sys_req in sys_reqs:
        paths = _trace_forward(sys_req['id'], graph, artifacts)
        sys_paths[sys_req['id']] = {
            'id': sys_req['id'],
            'text': sys_req['text'],
            'forward_paths': paths,
            'path_count': len(paths)
        }
    
    # HLR paths (both directions)
    hlrs = [a for a in artifacts.values() if a['type'] == 'HLR']
    for hlr in hlrs:
        forward = _trace_forward(hlr['id'], graph, artifacts)
        backward = _trace_backward(hlr['id'], graph, artifacts)
        hlr_paths[hlr['id']] = {
            'id': hlr['id'],
            'text': hlr['text'],
            'backward_paths': backward,
            'forward_paths': forward
        }
    
    # LLR paths (backward)
    llrs = [a for a in artifacts.values() if a['type'] == 'LLR']
    for llr in llrs:
        backward = _trace_backward(llr['id'], graph, artifacts)
        llr_paths[llr['id']] = {
            'id': llr['id'],
            'text': llr['text'],
            'backward_paths': backward
        }
    
    return {
        'system_requirements': sys_paths,
        'high_level_requirements': hlr_paths,
        'low_level_requirements': llr_paths
    }


def _trace_forward(
    start_id: str,
    graph: Dict[str, Any],
    artifacts: Dict[str, Any],
    visited: set = None
) -> List[List[str]]:
    """Trace forward from a node to find all downstream paths."""
    
    if visited is None:
        visited = set()
    
    if start_id in visited:
        return []
    
    visited.add(start_id)
    children = graph['edges_down'].get(start_id, [])
    
    if not children:
        return [[start_id]]
    
    all_paths = []
    for child in children:
        child_paths = _trace_forward(child, graph, artifacts, visited.copy())
        for path in child_paths:
            all_paths.append([start_id] + path)
    
    return all_paths


def _trace_backward(
    start_id: str,
    graph: Dict[str, Any],
    artifacts: Dict[str, Any],
    visited: set = None
) -> List[List[str]]:
    """Trace backward from a node to find all upstream paths."""
    
    if visited is None:
        visited = set()
    
    if start_id in visited:
        return []
    
    visited.add(start_id)
    parents = graph['edges_up'].get(start_id, [])
    
    if not parents:
        return [[start_id]]
    
    all_paths = []
    for parent in parents:
        parent_paths = _trace_backward(parent, graph, artifacts, visited.copy())
        for path in parent_paths:
            all_paths.append(path + [start_id])
    
    return all_paths


def _calculate_quality_metrics(
    sys_analysis: Dict[str, Any],
    hlr_analysis: Dict[str, Any],
    llr_analysis: Dict[str, Any],
    trace_paths: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate overall quality metrics."""
    
    total_sys = sys_analysis['total']
    total_hlr = hlr_analysis['total']
    total_llr = llr_analysis['total']
    
    # Overall implementation rate
    implemented_sys = sys_analysis['fully_implemented']['count']
    implemented_hlr = hlr_analysis['fully_implemented']['count']
    traced_llr = llr_analysis['traced']['count']
    
    total_requirements = total_sys + total_hlr + total_llr
    total_implemented = implemented_sys + implemented_hlr + traced_llr
    
    overall_rate = (total_implemented / total_requirements * 100) if total_requirements > 0 else 0
    
    return {
        'overall_implementation_rate': overall_rate,
        'system_requirements_rate': sys_analysis['fully_implemented']['percentage'],
        'hlr_implementation_rate': hlr_analysis['fully_implemented']['percentage'],
        'llr_traceability_rate': llr_analysis['traced']['percentage'],
        'total_requirements': total_requirements,
        'total_implemented': total_implemented,
        'orphaned_hlrs': hlr_analysis['orphaned']['count'],
        'orphaned_llrs': llr_analysis['orphaned']['count'],
        'total_orphaned': hlr_analysis['orphaned']['count'] + llr_analysis['orphaned']['count']
    }


def _get_children_of_type(
    parent_id: str,
    child_type: str,
    graph: Dict[str, Any],
    artifacts: Dict[str, Any]
) -> List[str]:
    """Get all children of a specific type for a parent node."""
    
    children = graph['edges_down'].get(parent_id, [])
    return [c for c in children if artifacts[c]['type'] == child_type]
