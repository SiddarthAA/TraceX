"""ID parsing and hierarchy utilities."""

import re
from typing import Optional, Tuple, List


def parse_id(artifact_id: str) -> Tuple[str, List[str]]:
    """
    Parse artifact ID into base and suffixes.
    
    Examples:
        SYS-001 -> ('SYS-001', [])
        HLR-001-A -> ('HLR-001', ['A'])
        LLR-001-A-1 -> ('LLR-001', ['A', '1'])
    """
    parts = artifact_id.split('-')
    if len(parts) <= 2:
        return (artifact_id, [])
    
    base = '-'.join(parts[:2])
    suffixes = parts[2:]
    return (base, suffixes)


def get_expected_parent_id(artifact_id: str, artifact_type: str) -> Optional[str]:
    """
    Infer expected parent ID from artifact ID.
    
    Examples:
        HLR-001-A -> SYS-001 or SYS-001-A (decomposed)
        LLR-001-A-1 -> HLR-001-A
    """
    base, suffixes = parse_id(artifact_id)
    
    if not suffixes:
        return None  # Root level
    
    if artifact_type == 'HLR':
        # HLR-001-A could come from SYS-001-A (decomposed)
        sys_base = base.replace('HLR', 'SYS')
        return f"{sys_base}-{suffixes[0]}" if suffixes else sys_base
    
    elif artifact_type == 'LLR':
        # LLR-001-A-1 -> HLR-001-A
        if len(suffixes) >= 2:
            hlr_base = base.replace('LLR', 'HLR')
            return f"{hlr_base}-{suffixes[0]}"
        elif len(suffixes) == 1:
            hlr_base = base.replace('LLR', 'HLR')
            return hlr_base
    
    return None


def get_expected_parent_type(artifact_type: str) -> Optional[str]:
    """Get expected parent type for an artifact type."""
    hierarchy = {
        'SYSTEM_REQ_DECOMPOSED': 'SYSTEM_REQ',
        'HLR': 'SYSTEM_REQ_DECOMPOSED',
        'LLR': 'HLR',
        'CODE_VAR': 'LLR'
    }
    return hierarchy.get(artifact_type)


def get_expected_child_type(artifact_type: str) -> Optional[str]:
    """Get expected child type for an artifact type."""
    hierarchy = {
        'SYSTEM_REQ': 'SYSTEM_REQ_DECOMPOSED',
        'SYSTEM_REQ_DECOMPOSED': 'HLR',
        'HLR': 'LLR',
        'LLR': 'CODE_VAR'
    }
    return hierarchy.get(artifact_type)


def generate_child_id(parent_id: str, suffix: str) -> str:
    """Generate child ID from parent ID and suffix."""
    return f"{parent_id}-{suffix}"


def is_valid_id(artifact_id: str) -> bool:
    """Check if artifact ID follows valid pattern."""
    pattern = r'^[A-Z]{3}-\d{3}(-[A-Z0-9]+)*$'
    return bool(re.match(pattern, artifact_id))
