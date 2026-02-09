"""CSV requirements and variables parser."""

import csv
from pathlib import Path
from typing import List, Dict, Any
from src.utils.text_utils import extract_keywords, extract_quantities, extract_variable_names


def parse_csv_requirements(filepath: str, artifact_type: str) -> List[Dict[str, Any]]:
    """
    Parse CSV file containing requirements.
    
    Expected format: ID,Text (2 columns, no header)
    """
    artifacts = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2:
                continue
            
            req_id = row[0].strip()
            text = row[1].strip()
            
            # Extract metadata
            keywords = extract_keywords(text)
            quantities = extract_quantities(text)
            variable_refs = extract_variable_names(text)
            
            artifact = {
                'id': req_id,
                'type': artifact_type,
                'text': text,
                'metadata': {
                    'category': infer_category(text),
                    'source_file': Path(filepath).name
                },
                'extracted': {
                    'keywords': keywords,
                    'quantities': quantities,
                    'referenced_ids': list(variable_refs)
                },
                'decomposed': False,
                'children': []
            }
            
            artifacts.append(artifact)
    
    return artifacts


def parse_csv_variables(filepath: str) -> List[Dict[str, Any]]:
    """
    Parse CSV file containing code variables.
    
    Expected format: Variable Name,Type,Range (with header)
    """
    artifacts = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header
        
        for idx, row in enumerate(reader):
            if len(row) < 3:
                continue
            
            var_name = row[0].strip()
            data_type = row[1].strip()
            range_str = row[2].strip()
            
            # Generate variable ID
            var_id = f"VAR-{idx+1:03d}"
            
            # Parse range
            range_min, range_max = parse_range(range_str)
            
            # Create description text
            text = f"{var_name} ({data_type}, {range_str})"
            
            artifact = {
                'id': var_id,
                'type': 'CODE_VAR',
                'name': var_name,
                'text': text,
                'metadata': {
                    'data_type': data_type,
                    'range': range_str,
                    'range_min': range_min,
                    'range_max': range_max,
                    'source_file': Path(filepath).name
                },
                'extracted': {
                    'keywords': extract_keywords(var_name + ' ' + data_type),
                    'quantities': [],
                    'referenced_ids': []
                }
            }
            
            artifacts.append(artifact)
    
    return artifacts


def parse_range(range_str: str) -> tuple:
    """Parse range string to min/max values."""
    if range_str == 'N/A':
        return None, None
    
    # Pattern: 0.0–100.0 or 0–5000
    import re
    match = re.search(r'([-+]?\d+\.?\d*)\s*[–-]\s*([-+]?\d+\.?\d*)', range_str)
    if match:
        try:
            return float(match.group(1)), float(match.group(2))
        except ValueError:
            return None, None
    
    return None, None


def infer_category(text: str) -> str:
    """Infer category from requirement text."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['brake', 'pressure', 'wheel', 'slip']):
        return 'Brake Control'
    elif any(word in text_lower for word in ['sensor', 'speed', 'interface']):
        return 'Sensing & I/O'
    elif any(word in text_lower for word in ['voltage', 'temperature', 'supply']):
        return 'Environmental'
    elif any(word in text_lower for word in ['fault', 'error', 'degraded', 'detect']):
        return 'Fault Management'
    elif any(word in text_lower for word in ['mode', 'state', 'transition']):
        return 'Mode Management'
    else:
        return 'General'


def load_all_artifacts(
    system_reqs_file: str,
    hlr_file: str,
    llr_file: str,
    variables_file: str = None
) -> Dict[str, Any]:
    """
    Load all artifacts from CSV files.
    
    Args:
        system_reqs_file: Path to System-Level-Requirements.csv (required)
        hlr_file: Path to High-Level-Requirements.csv (required)
        llr_file: Path to Low-Level-Requirements.csv (required)
        variables_file: Path to Variables.csv (optional)
    
    Returns:
        Dictionary with 'artifacts' key containing all parsed artifacts
    """
    
    artifacts = {}
    
    # Load system requirements (required)
    print(f"  Loading system requirements from {Path(system_reqs_file).name}...")
    sys_reqs = parse_csv_requirements(system_reqs_file, 'SYSTEM_REQ')
    for artifact in sys_reqs:
        artifacts[artifact['id']] = artifact
    print(f"    ✓ Loaded {len(sys_reqs)} system requirements")
    
    # Load HLRs (required)
    print(f"  Loading HLRs from {Path(hlr_file).name}...")
    hlrs = parse_csv_requirements(hlr_file, 'HLR')
    for artifact in hlrs:
        artifacts[artifact['id']] = artifact
    print(f"    ✓ Loaded {len(hlrs)} high-level requirements")
    
    # Load LLRs (required)
    print(f"  Loading LLRs from {Path(llr_file).name}...")
    llrs = parse_csv_requirements(llr_file, 'LLR')
    for artifact in llrs:
        artifacts[artifact['id']] = artifact
    print(f"    ✓ Loaded {len(llrs)} low-level requirements")
    
    # Load variables (optional)
    if variables_file and Path(variables_file).exists():
        print(f"  Loading variables from {Path(variables_file).name}...")
        variables = parse_csv_variables(variables_file)
        for artifact in variables:
            artifacts[artifact['id']] = artifact
        print(f"    ✓ Loaded {len(variables)} variables")
    else:
        print(f"  ⚠ Variables.csv not found - continuing without variables")
    
    return {'artifacts': artifacts}
