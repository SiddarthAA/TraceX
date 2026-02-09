"""Enhanced traceability matrix generator with detailed status and paths."""

from typing import Dict, List, Any, Set
from src.utils.file_io import save_csv


def generate_enhanced_traceability_matrix(
    artifacts: Dict[str, Any],
    links: List[Dict[str, Any]],
    analysis: Dict[str, Any],
    output_dir: str
) -> List[List[str]]:
    """
    Generate enhanced traceability matrix with:
    - Full/Partial/Orphan status
    - Complete trace paths
    - Reasons for partial tracing
    
    Returns: Matrix rows for CSV export
    """
    
    # Build graph for path tracing
    graph = _build_graph(artifacts, links)
    
    # Get system requirements
    sys_reqs = [a for a in artifacts.values() if a['type'] == 'SYSTEM_REQ']
    
    # Matrix header
    rows = [[
        'System Req',
        'SYS Text',
        'Status',
        'Decomposed Parts',
        'HLRs',
        'LLRs',
        'Variables',
        'Complete Path',
        'Issue/Gap Reason'
    ]]
    
    # Process each system requirement
    for sys_req in sorted(sys_reqs, key=lambda x: x['id']):
        sys_id = sys_req['id']
        sys_text = sys_req['text'][:80] + '...' if len(sys_req['text']) > 80 else sys_req['text']
        
        # Find all paths from this system req
        paths = _find_all_paths(sys_id, graph, artifacts)
        
        if not paths:
            # No decomposition at all
            rows.append([
                sys_id,
                sys_text,
                '❌ NO DECOMPOSITION',
                '0',
                '-',
                '-',
                '-',
                '-',
                'System requirement not decomposed'
            ])
            continue
        
        # Analyze each path
        for path_idx, path in enumerate(paths):
            status, reason = _classify_path(path, artifacts)
            
            # Extract IDs at each level
            decomposed_ids = _extract_ids_by_type(path, 'SYSTEM_REQ_DECOMPOSED')
            hlr_ids = _extract_ids_by_type(path, 'HLR')
            llr_ids = _extract_ids_by_type(path, 'LLR')
            var_ids = _extract_ids_by_type(path, 'CODE_VAR')
            
            # Build complete path string
            path_str = ' → '.join(path)
            
            # System req only on first row for this req
            sys_col = sys_id if path_idx == 0 else ''
            text_col = sys_text if path_idx == 0 else ''
            
            rows.append([
                sys_col,
                text_col,
                status,
                ', '.join(decomposed_ids) if decomposed_ids else '-',
                ', '.join(hlr_ids) if hlr_ids else '-',
                ', '.join(llr_ids) if llr_ids else '-',
                ', '.join(var_ids) if var_ids else '-',
                path_str,
                reason
            ])
    
    # Add HLR orphans section
    if 'high_level_requirements' in analysis:
        hlr_orphans = analysis['high_level_requirements'].get('orphaned', {}).get('requirements', [])
        if hlr_orphans:
            rows.append(['', '', '', '', '', '', '', '', ''])  # Blank row
            rows.append(['=== ORPHANED HIGH-LEVEL REQUIREMENTS ===', '', '', '', '', '', '', '', ''])
            
            for orphan in hlr_orphans:
                orphan_text = orphan['text'][:80] + '...' if len(orphan['text']) > 80 else orphan['text']
                rows.append([
                    '',
                    '',
                    '❌ ORPHANED',
                    '',
                    orphan['id'],
                    '',
                    '',
                    orphan['id'] + ' (isolated)',
                    orphan.get('issue', 'No parent or children links')
                ])
    
    # Add LLR orphans section
    if 'low_level_requirements' in analysis:
        llr_orphans = analysis['low_level_requirements'].get('orphaned', {}).get('requirements', [])
        if llr_orphans:
            rows.append(['', '', '', '', '', '', '', '', ''])  # Blank row
            rows.append(['=== ORPHANED LOW-LEVEL REQUIREMENTS ===', '', '', '', '', '', '', '', ''])
            
            for orphan in llr_orphans:
                orphan_text = orphan['text'][:80] + '...' if len(orphan['text']) > 80 else orphan['text']
                rows.append([
                    '',
                    '',
                    '❌ ORPHANED',
                    '',
                    '',
                    orphan['id'],
                    '',
                    orphan['id'] + ' (isolated)',
                    orphan.get('issue', 'No parent or children links')
                ])
    
    # Save to file
    matrix_file = f"{output_dir}/traceability_matrix_enhanced.csv"
    save_csv(rows, matrix_file)
    print(f"   ✓ Enhanced matrix: {matrix_file}")
    
    return rows


def _build_graph(artifacts: Dict[str, Any], links: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build directed graph from links."""
    graph = {
        'edges_down': {},
        'edges_up': {}
    }
    
    for link in links:
        src, tgt = link['source_id'], link['target_id']
        
        if src not in graph['edges_down']:
            graph['edges_down'][src] = []
        graph['edges_down'][src].append(tgt)
        
        if tgt not in graph['edges_up']:
            graph['edges_up'][tgt] = []
        graph['edges_up'][tgt].append(src)
    
    return graph


def _find_all_paths(
    start_id: str,
    graph: Dict[str, Any],
    artifacts: Dict[str, Any],
    max_depth: int = 10
) -> List[List[str]]:
    """Find all paths from start node using DFS."""
    paths = []
    
    def dfs(node_id: str, path: List[str], visited: Set[str]):
        if len(path) > max_depth or node_id in visited:
            return
        
        current_path = path + [node_id]
        visited_copy = visited | {node_id}
        
        children = graph['edges_down'].get(node_id, [])
        
        if not children:
            # Leaf node - complete path
            paths.append(current_path)
        else:
            for child_id in children:
                dfs(child_id, current_path, visited_copy)
    
    dfs(start_id, [], set())
    return paths


def _classify_path(path: List[str], artifacts: Dict[str, Any]) -> tuple[str, str]:
    """
    Classify a trace path as complete/partial/broken.
    
    Returns: (status_emoji, reason)
    """
    if not path:
        return ('❌ BROKEN', 'Empty path')
    
    # Get types in path
    types_in_path = [artifacts[node_id]['type'] for node_id in path if node_id in artifacts]
    
    # Ideal path: SYSTEM_REQ → SYSTEM_REQ_DECOMPOSED → HLR → LLR → CODE_VAR
    has_decomposed = 'SYSTEM_REQ_DECOMPOSED' in types_in_path
    has_hlr = 'HLR' in types_in_path
    has_llr = 'LLR' in types_in_path
    has_var = 'CODE_VAR' in types_in_path
    
    # Complete: reaches CODE_VAR
    if has_var:
        return ('✅ COMPLETE', 'Fully traced to code variable')
    
    # Partial: has some depth but doesn't reach variable
    if has_llr:
        return ('⚠️ PARTIAL', 'Reaches LLR but no variable link')
    elif has_hlr:
        return ('⚠️ PARTIAL', 'Reaches HLR but no LLR link')
    elif has_decomposed:
        return ('⚠️ PARTIAL', 'Decomposed but no HLR link')
    else:
        return ('❌ BROKEN', 'No decomposition')


def _extract_ids_by_type(path: List[str], target_type: str) -> List[str]:
    """Extract all IDs of a specific type from path."""
    # Assuming artifacts are accessible globally or passed
    # For now, filter by ID pattern
    
    type_prefixes = {
        'SYSTEM_REQ': 'SYS-',
        'SYSTEM_REQ_DECOMPOSED': 'SYS-',
        'HLR': 'HLR-',
        'LLR': 'LLR-',
        'CODE_VAR': 'VAR-'
    }
    
    prefix = type_prefixes.get(target_type, '')
    if not prefix:
        return []
    
    # For SYSTEM_REQ_DECOMPOSED, look for SYS-XXX-X pattern
    if target_type == 'SYSTEM_REQ_DECOMPOSED':
        return [id for id in path if id.startswith('SYS-') and '-' in id[4:]]
    else:
        return [id for id in path if id.startswith(prefix)]
