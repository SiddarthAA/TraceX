"""Text processing utilities."""

import re
from typing import List, Dict, Set


# Domain keywords for aerospace
DOMAIN_KEYWORDS = {
    "components": [
        "brake", "control", "unit", "wheel", "sensor", "hydraulic", "actuator",
        "valve", "pressure", "speed", "system", "interface", "bus", "data"
    ],
    "parameters": [
        "slip", "voltage", "temperature", "current", "rate", "mode", "state",
        "fault", "status", "input", "output", "command", "ground", "aircraft"
    ],
    "actions": [
        "compute", "calculate", "monitor", "detect", "transmit", "receive",
        "control", "limit", "sample", "validate", "check", "transition",
        "prevent", "modulate", "reduce", "restore", "format"
    ],
    "constraints": [
        "maximum", "minimum", "within", "exceeds", "below", "above", "range",
        "threshold", "limit", "safe", "valid", "normal", "degraded"
    ]
}

# Stopwords for keyword extraction
STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'from', 'by', 'shall', 'will', 'should', 'must', 'may',
    'can', 'could', 'would', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'this', 'that',
    'these', 'those', 'it', 'its', 'when', 'where', 'which', 'who', 'how'
}


def tokenize(text: str) -> List[str]:
    """Tokenize text into words."""
    # Convert to lowercase and split
    tokens = re.findall(r'\b\w+\b', text.lower())
    return tokens


def extract_keywords(text: str) -> List[str]:
    """Extract domain keywords from text."""
    tokens = tokenize(text)
    keywords = []
    
    # Remove stopwords
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    
    # Match against domain dictionary
    all_domain_words = set()
    for category in DOMAIN_KEYWORDS.values():
        all_domain_words.update(category)
    
    for token in tokens:
        if token in all_domain_words:
            keywords.append(token)
    
    # Extract variable-like names (camelCase, snake_case, UPPER_CASE)
    var_pattern = r'\b([A-Z][a-z]+[A-Z][a-zA-Z]*|[a-z]+_[a-z_]+|[A-Z][A-Z_]+)\b'
    var_matches = re.findall(var_pattern, text)
    keywords.extend([v.lower() for v in var_matches])
    
    # Extract noun phrases (simple pattern)
    words = text.split()
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i+1]}".lower()
        if bigram in [kw for cat in DOMAIN_KEYWORDS.values() for kw in cat]:
            keywords.append(bigram)
    
    return list(set(keywords))


def extract_quantities(text: str) -> List[Dict[str, any]]:
    """Extract numerical quantities with units."""
    quantities = []
    
    # Pattern for numbers with units
    patterns = [
        r'([±]?\d+\.?\d*)\s*(feet|ft|meters|m|seconds|s|ms|Hz|degrees|deg|percent|%|VDC|°C|rpm|mA)',
        r'(within|maximum|minimum|at least|no more than|exceeds|below|above)\s+([±]?\d+\.?\d*)',
        r'(\d+\.?\d*)\s*(?:to|–|-)\s*(\d+\.?\d*)\s*(feet|ft|meters|m|seconds|s|ms|Hz|degrees|deg|percent|%|VDC|°C|rpm|mA)?',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            groups = match.groups()
            if len(groups) >= 2:
                try:
                    value = float(groups[0]) if groups[0].replace('.', '').replace('-', '').replace('+', '').isdigit() else groups[0]
                    unit = groups[1] if len(groups) > 1 else ""
                    quantities.append({
                        'value': value,
                        'unit': unit,
                        'constraint': 'range' if 'to' in match.group() or '–' in match.group() else 'single'
                    })
                except (ValueError, IndexError):
                    continue
    
    return quantities


def extract_variable_names(text: str) -> Set[str]:
    """Extract variable names from text."""
    # Pattern for variable names: snake_case, camelCase, PascalCase
    patterns = [
        r'\b([a-z][a-z0-9]*(?:_[a-z0-9]+)+)\b',  # snake_case
        r'\b([a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*)\b',  # camelCase
        r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b',  # PascalCase
        r'\b([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*)\b',  # UPPER_CASE
    ]
    
    variables = set()
    for pattern in patterns:
        matches = re.findall(pattern, text)
        variables.update(matches)
    
    return variables


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text."""
    return ' '.join(text.split())
