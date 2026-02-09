"""Enhanced analysis for hierarchical traceability with orphan and completeness tracking."""

from typing import Dict, List, Any, Set, Tuple


def analyze_hierarchical_traceability(
    artifacts: Dict[str, Any],
    links: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Comprehensive hierarchical traceability analysis.
    
    Returns detailed analysis including:
    - Complete vs partial implementation status
    - Orphaned requirements at each level
    - Coverage metrics
    - Chain analysis
    """
    
    print("\n=== Analyzing Hierarchical Traceability ===")
    
    # Build graph structure
    graph = _build_graph(artifacts, links)
    
    # Analyze each layer
    analysis = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'system_requirements': _analyze_system_requirements(artifacts, graph),
        'high_level_requirements': _analyze_hlr_layer(artifacts, graph),
        'low_level_requirements': _analyze_llr_layer(artifacts, graph),
        'variables': _analyze_variable_layer(artifacts, graph),
        'chains': _analyze_chains(artifacts, graph),
        'coverage_summary': _compute_coverage_summary(artifacts, graph),
        'quality_metrics': _compute_quality_metrics(links)
    }
    
    # Print summary
    _print_analysis_summary(analysis)
    
    return analysis


def _build_graph(artifacts: Dict[str, Any], links: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build bidirectional graph from links."""
    
    graph = {
        'nodes': artifacts,
        'edges_down': {},  # parent -> [children]
        'edges_up': {},    # child -> [parents]
        'links_by_source': {},  # source_id -> [link objects]
        'links_by_target': {}   # target_id -> [link objects]
    }
    
    for link in links:
        source_id = link['source_id']
        target_id = link['target_id']
        
        # Forward edges
        if source_id not in graph['edges_down']:
            graph['edges_down'][source_id] = []
        graph['edges_down'][source_id].append(target_id)
        
        # Backward edges
        if target_id not in graph['edges_up']:
            graph['edges_up'][target_id] = []
        graph['edges_up'][target_id].append(source_id)
        
        # Link objects
        if source_id not in graph['links_by_source']:
            graph['links_by_source'][source_id] = []
        graph['links_by_source'][source_id].append(link)
        
        if target_id not in graph['links_by_target']:
            graph['links_by_target'][target_id] = []
        graph['links_by_target'][target_id].append(link)
    
    return graph


def _analyze_system_requirements(
    artifacts: Dict[str, Any],
    graph: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze system requirements completeness."""
    
    sys_reqs = [a for a in artifacts.values() if a['type'] == 'SYSTEM_REQ']
    
    complete = []
    partial = []
    no_decomposition = []
    
    for req in sys_reqs:
        req_id = req['id']
        
        # Check if decomposed
        children = graph['edges_down'].get(req_id, [])
        if not children:
            no_decomposition.append({
                'id': req_id,
                'text': req['text'],
                'issue': 'Not decomposed'
            })
            continue
        
        # Check if decomposed parts link to HLRs
        decomposed_children = [
            c for c in children 
            if artifacts[c]['type'] == 'SYSTEM_REQ_DECOMPOSED'
        ]
        
        hlr_linked = []
        for decomp_id in decomposed_children:
            decomp_children = graph['edges_down'].get(decomp_id, [])
            hlr_children = [
                c for c in decomp_children 
                if artifacts[c]['type'] == 'HLR'
            ]
            if hlr_children:
                hlr_linked.append(decomp_id)
        
        # Classify completeness
        if len(hlr_linked) == len(decomposed_children):
            # All decomposed parts link to HLRs - check chain depth
            has_complete_chain = False
            for decomp_id in decomposed_children:
                chain_depth = _get_max_chain_depth(decomp_id, graph, artifacts)
                if chain_depth >= 3:  # Reaches at least LLR
                    has_complete_chain = True
                    break
            
            if has_complete_chain:
                complete.append({
                    'id': req_id,
                    'text': req['text'],
                    'decomposed_parts': len(decomposed_children),
                    'max_chain_depth': max(_get_max_chain_depth(d, graph, artifacts) 
                                          for d in decomposed_children)
                })
            else:
                partial.append({
                    'id': req_id,
                    'text': req['text'],
                    'decomposed_parts': len(decomposed_children),
                    'linked_parts': len(hlr_linked),
                    'issue': 'Chain does not reach LLR level'
                })
        elif len(hlr_linked) > 0:
            partial.append({
                'id': req_id,
                'text': req['text'],
                'decomposed_parts': len(decomposed_children),
                'linked_parts': len(hlr_linked),
                'issue': f'{len(decomposed_children) - len(hlr_linked)} decomposed parts not linked to HLR'
            })
        else:
            partial.append({
                'id': req_id,
                'text': req['text'],
                'decomposed_parts': len(decomposed_children),
                'linked_parts': 0,
                'issue': 'No decomposed parts linked to HLR'
            })
    
    total = len(sys_reqs)
    return {
        'total': total,
        'complete': {
            'count': len(complete),
            'percentage': (len(complete) / total * 100) if total > 0 else 0,
            'requirements': complete
        },
        'partial': {
            'count': len(partial),
            'percentage': (len(partial) / total * 100) if total > 0 else 0,
            'requirements': partial
        },
        'no_decomposition': {
            'count': len(no_decomposition),
            'percentage': (len(no_decomposition) / total * 100) if total > 0 else 0,
            'requirements': no_decomposition
        }
    }


def _analyze_hlr_layer(
    artifacts: Dict[str, Any],
    graph: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze HLR layer completeness and orphans."""
    
    hlrs = [a for a in artifacts.values() if a['type'] == 'HLR']
    
    complete = []  # Has parent and children
    partial = []   # Has parent OR children but not both
    orphaned = []  # No parent and no children
    
    for hlr in hlrs:
        hlr_id = hlr['id']
        parents = graph['edges_up'].get(hlr_id, [])
        children = graph['edges_down'].get(hlr_id, [])
        
        llr_children = [c for c in children if artifacts[c]['type'] == 'LLR']
        
        if parents and llr_children:
            complete.append({
                'id': hlr_id,
                'text': hlr['text'],
                'parent_count': len(parents),
                'llr_count': len(llr_children)
            })
        elif parents or llr_children:
            issue = []
            if not parents:
                issue.append('No parent link (orphaned from SYS requirements)')
            if not llr_children:
                issue.append('No LLR children (not further decomposed)')
            
            partial.append({
                'id': hlr_id,
                'text': hlr['text'],
                'parent_count': len(parents),
                'llr_count': len(llr_children),
                'issue': '; '.join(issue)
            })
        else:
            orphaned.append({
                'id': hlr_id,
                'text': hlr['text'],
                'issue': 'Completely isolated - no parent or children'
            })
    
    total = len(hlrs)
    return {
        'total': total,
        'complete': {
            'count': len(complete),
            'percentage': (len(complete) / total * 100) if total > 0 else 0,
            'requirements': complete
        },
        'partial': {
            'count': len(partial),
            'percentage': (len(partial) / total * 100) if total > 0 else 0,
            'requirements': partial
        },
        'orphaned': {
            'count': len(orphaned),
            'percentage': (len(orphaned) / total * 100) if total > 0 else 0,
            'requirements': orphaned
        }
    }


def _analyze_llr_layer(
    artifacts: Dict[str, Any],
    graph: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze LLR layer completeness and orphans.
    
    Classification logic depends on variable availability:
    - If variables exist: LLRs classified as complete/partial/orphaned (like HLRs)
    - If no variables: LLRs classified as implemented/orphaned (simpler)
    """
    
    llrs = [a for a in artifacts.values() if a['type'] == 'LLR']
    has_variables = any(a['type'] == 'CODE_VAR' for a in artifacts.values())
    
    if not has_variables:
        # Simple classification: implemented (has HLR parent) or orphaned
        implemented = []
        orphaned = []
        
        for llr in llrs:
            llr_id = llr['id']
            parents = graph['edges_up'].get(llr_id, [])
            hlr_parents = [p for p in parents if artifacts[p]['type'] == 'HLR']
            
            if hlr_parents:
                implemented.append({
                    'id': llr_id,
                    'text': llr['text'],
                    'hlr_count': len(hlr_parents)
                })
            else:
                orphaned.append({
                    'id': llr_id,
                    'text': llr['text'],
                    'issue': 'No HLR parent'
                })
        
        total = len(llrs)
        return {
            'total': total,
            'implemented': {
                'count': len(implemented),
                'percentage': (len(implemented) / total * 100) if total > 0 else 0,
                'requirements': implemented
            },
            'orphaned': {
                'count': len(orphaned),
                'percentage': (len(orphaned) / total * 100) if total > 0 else 0,
                'requirements': orphaned
            }
        }
    
    # Detailed classification when variables exist: complete/partial/orphaned
    complete = []
    partial = []
    orphaned = []
    
    for llr in llrs:
        llr_id = llr['id']
        parents = graph['edges_up'].get(llr_id, [])
        children = graph['edges_down'].get(llr_id, [])
        
        hlr_parents = [p for p in parents if artifacts[p]['type'] == 'HLR']
        var_children = [c for c in children if artifacts[c]['type'] == 'CODE_VAR']
        
        if hlr_parents and var_children:
            complete.append({
                'id': llr_id,
                'text': llr['text'],
                'hlr_count': len(hlr_parents),
                'variable_count': len(var_children)
            })
        elif hlr_parents or var_children:
            issue = []
            if not hlr_parents:
                issue.append('No HLR parent (orphaned)')
            if not var_children:
                issue.append('No variables referenced')
            
            partial.append({
                'id': llr_id,
                'text': llr['text'],
                'hlr_count': len(hlr_parents),
                'variable_count': len(var_children),
                'issue': '; '.join(issue)
            })
        else:
            orphaned.append({
                'id': llr_id,
                'text': llr['text'],
                'issue': 'Completely isolated'
            })
    
    total = len(llrs)
    return {
        'total': total,
        'complete': {
            'count': len(complete),
            'percentage': (len(complete) / total * 100) if total > 0 else 0,
            'requirements': complete
        },
        'partial': {
            'count': len(partial),
            'percentage': (len(partial) / total * 100) if total > 0 else 0,
            'requirements': partial
        },
        'orphaned': {
            'count': len(orphaned),
            'percentage': (len(orphaned) / total * 100) if total > 0 else 0,
            'requirements': orphaned
        }
    }


def _analyze_variable_layer(
    artifacts: Dict[str, Any],
    graph: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze variable traceability."""
    
    variables = [a for a in artifacts.values() if a['type'] == 'CODE_VAR']
    
    traced = []
    orphaned = []
    
    for var in variables:
        var_id = var['id']
        parents = graph['edges_up'].get(var_id, [])
        
        llr_parents = [p for p in parents if artifacts[p]['type'] == 'LLR']
        
        if llr_parents:
            traced.append({
                'id': var_id,
                'name': var.get('name', var_id),
                'llr_count': len(llr_parents),
                'llr_parents': llr_parents[:5]  # Limit for display
            })
        else:
            orphaned.append({
                'id': var_id,
                'name': var.get('name', var_id),
                'issue': 'No LLR parent - not traced to requirements'
            })
    
    total = len(variables)
    return {
        'total': total,
        'traced': {
            'count': len(traced),
            'percentage': (len(traced) / total * 100) if total > 0 else 0,
            'variables': traced
        },
        'orphaned': {
            'count': len(orphaned),
            'percentage': (len(orphaned) / total * 100) if total > 0 else 0,
            'variables': orphaned
        }
    }


def _analyze_chains(
    artifacts: Dict[str, Any],
    graph: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze end-to-end trace chains."""
    
    sys_reqs = [a for a in artifacts.values() if a['type'] == 'SYSTEM_REQ']
    
    chains_analysis = {
        'complete_chains': [],
        'partial_chains': [],
        'broken_chains': []
    }
    
    for sys_req in sys_reqs:
        chains = _find_all_chains(sys_req['id'], graph, artifacts)
        
        for chain in chains:
            chain_types = [artifacts[node_id]['type'] for node_id in chain]
            chain_depth = len(chain)
            terminal_type = chain_types[-1] if chain_types else None
            
            chain_info = {
                'system_req': sys_req['id'],
                'chain': chain,
                'depth': chain_depth,
                'types': chain_types
            }
            
            # Complete: reaches CODE_VAR
            if terminal_type == 'CODE_VAR' and chain_depth >= 4:
                chains_analysis['complete_chains'].append(chain_info)
            # Partial: has depth but doesn't reach CODE_VAR
            elif chain_depth >= 2:
                chains_analysis['partial_chains'].append(chain_info)
            # Broken: too short
            else:
                chains_analysis['broken_chains'].append(chain_info)
    
    total_chains = sum(len(v) for v in chains_analysis.values())
    
    return {
        'total_chains': total_chains,
        'complete': {
            'count': len(chains_analysis['complete_chains']),
            'percentage': (len(chains_analysis['complete_chains']) / total_chains * 100) if total_chains > 0 else 0,
            'chains': chains_analysis['complete_chains'][:10]  # Limit for display
        },
        'partial': {
            'count': len(chains_analysis['partial_chains']),
            'percentage': (len(chains_analysis['partial_chains']) / total_chains * 100) if total_chains > 0 else 0,
            'chains': chains_analysis['partial_chains'][:10]
        },
        'broken': {
            'count': len(chains_analysis['broken_chains']),
            'percentage': (len(chains_analysis['broken_chains']) / total_chains * 100) if total_chains > 0 else 0,
            'chains': chains_analysis['broken_chains'][:10]
        }
    }


def _find_all_chains(
    start_id: str,
    graph: Dict[str, Any],
    artifacts: Dict[str, Any]
) -> List[List[str]]:
    """Find all trace chains from a starting node using DFS."""
    
    chains = []
    
    def dfs(node_id: str, path: List[str], visited: Set[str]):
        if node_id in visited:
            return
        
        current_path = path + [node_id]
        visited_copy = visited | {node_id}
        
        children = graph['edges_down'].get(node_id, [])
        
        if not children:
            chains.append(current_path)
        else:
            for child_id in children:
                dfs(child_id, current_path, visited_copy)
    
    dfs(start_id, [], set())
    return chains


def _get_max_chain_depth(
    start_id: str,
    graph: Dict[str, Any],
    artifacts: Dict[str, Any]
) -> int:
    """Get maximum chain depth from a node."""
    
    chains = _find_all_chains(start_id, graph, artifacts)
    return max(len(chain) for chain in chains) if chains else 0


def _compute_coverage_summary(
    artifacts: Dict[str, Any],
    graph: Dict[str, Any]
) -> Dict[str, Any]:
    """Compute overall coverage summary."""
    
    # Count by type
    by_type = {}
    for artifact in artifacts.values():
        art_type = artifact['type']
        by_type[art_type] = by_type.get(art_type, 0) + 1
    
    # Count linked
    linked_count = {}
    for art_type in by_type:
        linked = sum(
            1 for a in artifacts.values()
            if a['type'] == art_type and (
                graph['edges_up'].get(a['id'], []) or
                graph['edges_down'].get(a['id'], [])
            )
        )
        linked_count[art_type] = linked
    
    # Coverage percentages
    coverage = {}
    for art_type, total in by_type.items():
        linked = linked_count.get(art_type, 0)
        coverage[art_type] = {
            'total': total,
            'linked': linked,
            'percentage': (linked / total * 100) if total > 0 else 0
        }
    
    return coverage


def _compute_quality_metrics(links: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute link quality metrics."""
    
    if not links:
        return {
            'total_links': 0,
            'avg_confidence': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0
        }
    
    confidences = [link['confidence'] for link in links]
    avg_confidence = sum(confidences) / len(confidences)
    
    high = sum(1 for c in confidences if c >= 0.7)
    medium = sum(1 for c in confidences if 0.5 <= c < 0.7)
    low = sum(1 for c in confidences if c < 0.5)
    
    return {
        'total_links': len(links),
        'avg_confidence': avg_confidence,
        'high_confidence': {'count': high, 'percentage': high / len(links) * 100},
        'medium_confidence': {'count': medium, 'percentage': medium / len(links) * 100},
        'low_confidence': {'count': low, 'percentage': low / len(links) * 100}
    }


def _print_analysis_summary(analysis: Dict[str, Any]) -> None:
    """Print human-readable summary of analysis."""
    
    print("\n" + "="*60)
    print("HIERARCHICAL TRACEABILITY ANALYSIS SUMMARY")
    print("="*60)
    
    # System Requirements
    sys = analysis['system_requirements']
    print(f"\nSYSTEM REQUIREMENTS ({sys['total']} total):")
    print(f"  ✓ Complete: {sys['complete']['count']} ({sys['complete']['percentage']:.1f}%)")
    print(f"  ⚠ Partial: {sys['partial']['count']} ({sys['partial']['percentage']:.1f}%)")
    print(f"  ✗ No decomposition: {sys['no_decomposition']['count']} ({sys['no_decomposition']['percentage']:.1f}%)")
    
    # HLRs
    hlr = analysis['high_level_requirements']
    print(f"\nHIGH-LEVEL REQUIREMENTS ({hlr['total']} total):")
    print(f"  ✓ Complete: {hlr['complete']['count']} ({hlr['complete']['percentage']:.1f}%)")
    print(f"  ⚠ Partial: {hlr['partial']['count']} ({hlr['partial']['percentage']:.1f}%)")
    print(f"  ✗ Orphaned: {hlr['orphaned']['count']} ({hlr['orphaned']['percentage']:.1f}%)")
    
    # LLRs
    llr = analysis['low_level_requirements']
    print(f"\nLOW-LEVEL REQUIREMENTS ({llr['total']} total):")
    if 'complete' in llr:
        # Detailed format (with variables)
        print(f"  ✓ Complete: {llr['complete']['count']} ({llr['complete']['percentage']:.1f}%)")
        print(f"  ⚠ Partial: {llr['partial']['count']} ({llr['partial']['percentage']:.1f}%)")
        print(f"  ✗ Orphaned: {llr['orphaned']['count']} ({llr['orphaned']['percentage']:.1f}%)")
    else:
        # Simple format (no variables)
        print(f"  ✓ Implemented: {llr['implemented']['count']} ({llr['implemented']['percentage']:.1f}%)")
        print(f"  ✗ Orphaned: {llr['orphaned']['count']} ({llr['orphaned']['percentage']:.1f}%)")
    
    # Variables
    var = analysis['variables']
    print(f"\nVARIABLES ({var['total']} total):")
    print(f"  ✓ Traced: {var['traced']['count']} ({var['traced']['percentage']:.1f}%)")
    print(f"  ✗ Orphaned: {var['orphaned']['count']} ({var['orphaned']['percentage']:.1f}%)")
    
    # Chains
    chains = analysis['chains']
    print(f"\nTRACE CHAINS ({chains['total_chains']} total):")
    print(f"  ✓ Complete: {chains['complete']['count']} ({chains['complete']['percentage']:.1f}%)")
    print(f"  ⚠ Partial: {chains['partial']['count']} ({chains['partial']['percentage']:.1f}%)")
    print(f"  ✗ Broken: {chains['broken']['count']} ({chains['broken']['percentage']:.1f}%)")
    
    # Quality
    quality = analysis['quality_metrics']
    print(f"\nLINK QUALITY:")
    print(f"  Total links: {quality['total_links']}")
    print(f"  Average confidence: {quality['avg_confidence']:.2f}")
    print(f"  High confidence (≥0.7): {quality['high_confidence']['count']} ({quality['high_confidence']['percentage']:.1f}%)")
    print(f"  Medium confidence (0.5-0.7): {quality['medium_confidence']['count']} ({quality['medium_confidence']['percentage']:.1f}%)")
    
    print("\n" + "="*60)


# Missing import at top
from datetime import datetime
