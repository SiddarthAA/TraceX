"""Link scoring and creation with hierarchical linking support."""

from typing import Dict, List, Tuple, Any, Set
from datetime import datetime
import uuid
import re


def extract_id_hierarchy(artifact_id: str) -> Dict[str, Any]:
    """
    Extract hierarchical information from artifact ID.
    
    Examples:
        HLR-001-A -> {base: 'HLR-001', suffix: 'A', parent_ref: 'SYS-001'}
        LLR-001-A-1 -> {base: 'LLR-001-A', suffix: '1', parent_ref: 'HLR-001-A'}
    """
    # Pattern: PREFIX-NUMBER[-LETTER][-NUMBER]
    pattern = r'^([A-Z]+)-(\d+)(?:-([A-Z]+))?(?:-(\d+))?$'
    match = re.match(pattern, artifact_id)
    
    if not match:
        return {'base': artifact_id, 'suffix': None, 'parent_ref': None}
    
    prefix, num, letter, subnum = match.groups()
    
    info = {
        'base': f"{prefix}-{num}",
        'suffix': letter or subnum,
        'parent_ref': None,
        'prefix': prefix
    }
    
    # Infer parent reference based on structure
    if prefix == 'HLR' and letter:
        # HLR-001-A likely implements SYS-001
        info['parent_ref'] = f"SYS-{num}"
    elif prefix == 'LLR' and letter:
        if subnum:
            # LLR-001-A-1 implements HLR-001-A
            info['parent_ref'] = f"HLR-{num}-{letter}"
        else:
            # LLR-001-A implements HLR-001-A
            info['parent_ref'] = f"HLR-{num}-{letter}"
    
    return info


def compute_id_relationship_boost(source_id: str, target_id: str) -> float:
    """
    Boost score if IDs show hierarchical relationship.
    
    Returns: Boost factor (0.0 to 0.3)
    """
    source_info = extract_id_hierarchy(source_id)
    target_info = extract_id_hierarchy(target_id)
    
    # Direct parent reference match
    if source_info['parent_ref'] == target_id or target_info['parent_ref'] == source_id:
        return 0.3
    
    # Same base number (e.g., HLR-001-A -> LLR-001-A-1)
    if source_info['base'].split('-')[-1] == target_info['base'].split('-')[-1]:
        return 0.2
    
    # Check if target ID appears in source text would be checked elsewhere
    return 0.0


def compute_keyword_score(source: Dict[str, Any], target: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Compute keyword overlap score using Jaccard similarity.
    Enhanced to handle partial word matches.
    
    Returns: (score, matching_keywords)
    """
    source_keywords = set(source.get('extracted', {}).get('keywords', []))
    target_keywords = set(target.get('extracted', {}).get('keywords', []))
    
    if not source_keywords or not target_keywords:
        # Fallback to text-based keyword extraction
        source_text = source.get('text', '').lower()
        target_text = target.get('text', '').lower()
        
        # Extract important words (length > 4, not common stopwords)
        stopwords = {'shall', 'will', 'must', 'should', 'when', 'where', 'that', 'this', 'with', 'from'}
        source_words = set(w for w in re.findall(r'\b\w{5,}\b', source_text) if w not in stopwords)
        target_words = set(w for w in re.findall(r'\b\w{5,}\b', target_text) if w not in stopwords)
        
        if source_words and target_words:
            intersection = source_words & target_words
            union = source_words | target_words
            score = len(intersection) / len(union) if union else 0.0
            return score, list(intersection)[:5]
        
        return 0.0, []
    
    intersection = source_keywords & target_keywords
    union = source_keywords | target_keywords
    
    score = len(intersection) / len(union) if union else 0.0
    matching = list(intersection)
    
    return score, matching


def compute_quantity_match(source: Dict[str, Any], target: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if quantities match between artifacts.
    
    Returns: (match_bool, matched_quantities)
    """
    source_quants = source.get('extracted', {}).get('quantities', [])
    target_quants = target.get('extracted', {}).get('quantities', [])
    
    if not source_quants or not target_quants:
        return False, []
    
    matched = []
    for sq in source_quants:
        for tq in target_quants:
            if quantities_equal(sq, tq):
                matched.append(f"{sq.get('value')} {sq.get('unit', '')}")
    
    return len(matched) > 0, matched


def quantities_equal(q1: Dict, q2: Dict) -> bool:
    """Check if two quantities are equal."""
    # Compare values
    v1 = q1.get('value')
    v2 = q2.get('value')
    
    if isinstance(v1, str) or isinstance(v2, str):
        return False
    
    if abs(v1 - v2) > 0.001:
        return False
    
    # Compare units (normalize common variations)
    u1 = normalize_unit(q1.get('unit', ''))
    u2 = normalize_unit(q2.get('unit', ''))
    
    return u1 == u2


def normalize_unit(unit: str) -> str:
    """Normalize unit strings."""
    unit = unit.lower().strip()
    
    # Common normalizations
    mappings = {
        'ft': 'feet',
        'm': 'meters',
        's': 'seconds',
        'deg': 'degrees',
        '°c': 'celsius',
        'vdc': 'volts'
    }
    
    return mappings.get(unit, unit)


def compute_variable_name_match(
    llr: Dict[str, Any],
    variable: Dict[str, Any]
) -> Tuple[float, List[str]]:
    """
    Check if variable name appears in LLR text.
    
    Returns: (score, match_reasons)
    """
    var_name = variable.get('name', '')
    llr_text = llr.get('text', '')
    llr_refs = llr.get('extracted', {}).get('referenced_ids', [])
    
    reasons = []
    score = 0.0
    
    # Exact name match in text
    if var_name in llr_text:
        score = 1.0
        reasons.append(f"Exact match: '{var_name}' in LLR text")
    
    # Match in referenced IDs
    elif var_name.lower() in [ref.lower() for ref in llr_refs]:
        score = 0.9
        reasons.append(f"Variable '{var_name}' extracted from LLR text")
    
    # Partial match (underscore-separated parts)
    else:
        var_parts = var_name.lower().split('_')
        matches = sum(1 for part in var_parts if part in llr_text.lower())
        if matches > 0:
            score = 0.5 + (0.3 * matches / len(var_parts))
            reasons.append(f"Partial match: {matches}/{len(var_parts)} parts of '{var_name}'")
    
    return score, reasons


def compute_combined_score(
    embedding_sim: float,
    keyword_score: float,
    quantity_match: bool,
    name_match_score: float = 0.0,
    id_boost: float = 0.0,
    weights: Dict[str, float] = None
) -> float:
    """
    Compute final combined link score with ID hierarchy boost.
    
    Args:
        id_boost: Additional boost for hierarchical ID relationships (0-0.3)
    
    Default weights:
    - embedding: 0.45
    - keyword: 0.25
    - quantity: 0.15
    - name: 0.15
    """
    if weights is None:
        weights = {
            'embedding': 0.45,
            'keyword': 0.25,
            'quantity': 0.15,
            'name': 0.15
        }
    
    # Base weighted score
    score = (
        weights['embedding'] * embedding_sim +
        weights['keyword'] * keyword_score +
        weights['quantity'] * (1.0 if quantity_match else 0.0) +
        weights['name'] * name_match_score
    )
    
    # Add ID boost (additive, capped at 1.0)
    score = min(1.0, score + id_boost)
    
    return score


def generate_link_rationale(
    source: Dict[str, Any],
    target: Dict[str, Any],
    match_details: Dict[str, Any]
) -> str:
    """Generate human-readable rationale for a link."""
    
    parts = [
        f"{target['id']} implements {source['id']}."
    ]
    
    # Keyword matches
    keywords = match_details.get('keyword_overlap', [])
    if keywords:
        parts.append(f"Matched on keywords: {', '.join(keywords[:5])}.")
    
    # Embedding similarity
    emb_sim = match_details.get('embedding_similarity', 0.0)
    parts.append(f"Embedding similarity: {emb_sim:.2f}.")
    
    # Quantity matches
    quantities = match_details.get('quantities_matched', [])
    if quantities:
        parts.append(f"Matched quantities: {', '.join(quantities)}.")
    
    # Variable name match
    name_reasons = match_details.get('name_match_reasons', [])
    if name_reasons:
        parts.append(name_reasons[0])
    
    return ' '.join(parts)


def create_link(
    source_id: str,
    target_id: str,
    link_type: str,
    confidence: float,
    match_details: Dict[str, Any],
    source: Dict[str, Any],
    target: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a trace link."""
    
    link_id = f"LINK-{uuid.uuid4().hex[:8]}"
    
    return {
        'id': link_id,
        'source_id': source_id,
        'target_id': target_id,
        'link_type': link_type,
        'direction': 'down',
        'confidence': confidence,
        'status': 'confirmed' if confidence >= 0.7 else 'candidate',
        'match_details': match_details,
        'rationale': generate_link_rationale(source, target, match_details),
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'created_by': 'auto'
    }


class LinkManager:
    """Manages trace links."""
    
    def __init__(self, artifacts: Dict[str, Any], indexer, config):
        """Initialize link manager."""
        self.artifacts = artifacts
        self.indexer = indexer
        self.config = config
        self.links = []
    
    def find_candidates(
        self,
        source_id: str,
        target_type: str,
        top_k: int = 10
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Find candidate links for source artifact.
        
        Returns: List of (target_id, embedding_score, match_details)
        """
        source = self.artifacts[source_id]
        
        # Get source embedding
        source_emb = self.indexer.get_embedding(source_id)
        if source_emb is None:
            return []
        
        # Search for similar artifacts
        candidates = self.indexer.search_similar(
            query_embedding=source_emb,
            top_k=top_k * 3,  # Get extra for filtering
            threshold=self.config.linking.embedding_threshold
        )
        
        # Filter by type and compute scores
        results = []
        for candidate_id, emb_score in candidates:
            # Skip self
            if candidate_id == source_id:
                continue
            
            candidate = self.artifacts.get(candidate_id)
            if not candidate or candidate['type'] != target_type:
                continue
            
            # Compute keyword score
            keyword_score, keyword_matches = compute_keyword_score(source, candidate)
            
            # Compute quantity match
            quantity_match, quantity_matches = compute_quantity_match(source, candidate)
            
            # Compute variable name match (for LLR->VAR links)
            name_score = 0.0
            name_reasons = []
            if target_type == 'CODE_VAR':
                name_score, name_reasons = compute_variable_name_match(source, candidate)
            
            # Compute ID hierarchy boost
            id_boost = compute_id_relationship_boost(source_id, candidate_id)
            
            # Compute combined score
            combined_score = compute_combined_score(
                emb_score,
                keyword_score,
                quantity_match,
                name_score,
                id_boost,
                self.config.linking.weights
            )
            
            match_details = {
                'embedding_similarity': emb_score,
                'keyword_score': keyword_score,
                'keyword_overlap': keyword_matches,
                'quantity_match': quantity_match,
                'quantities_matched': quantity_matches,
                'name_match_score': name_score,
                'name_match_reasons': name_reasons,
                'id_boost': id_boost,
                'combined_score': combined_score
            }
            
            # Apply quality filters
            if self._passes_quality_filters(match_details, source, candidate):
                results.append((candidate_id, combined_score, match_details))
        
        # Sort by combined score
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Apply max links per source limit
        max_links = self.config.linking.quality_filters.get('max_links_per_source', 8)
        return results[:min(top_k, max_links)]
    
    def _passes_quality_filters(
        self,
        match_details: Dict[str, Any],
        source: Dict[str, Any],
        target: Dict[str, Any]
    ) -> bool:
        """
        Apply quality filters to reject poor-quality links.
        More lenient to improve coverage while still preventing random matches.
        
        Returns: True if link meets quality standards
        """
        filters = self.config.linking.quality_filters
        
        # Filter 1: Minimum text overlap (very low baseline)
        min_overlap = filters.get('min_text_overlap', 0.05)
        emb_score = match_details['embedding_similarity']
        if emb_score < min_overlap:
            return False
        
        # Adaptive Quality Check: Strong signals OR multiple moderate signals
        # More lenient thresholds to improve coverage
        
        # Check for STRONG signals (any one is sufficient)
        has_strong_keywords = match_details['keyword_score'] > 0.20  # Lowered from 0.25
        has_strong_embedding = match_details['embedding_similarity'] > 0.30  # Lowered from 0.35
        has_strong_combo = (
            match_details['embedding_similarity'] > 0.20 and  # Lowered from 0.25
            match_details['keyword_score'] > 0.12             # Lowered from 0.15
        )
        
        # If ANY strong signal exists, accept (more lenient)
        if has_strong_keywords or has_strong_embedding or has_strong_combo:
            return True
        
        # Otherwise, require multiple moderate signals (2 out of many)
        active_signals = 0
        
        # Lower thresholds to catch more genuine links
        if match_details['embedding_similarity'] > 0.12:  # Lowered from 0.15
            active_signals += 1
        if match_details['keyword_score'] > 0.05:  # Lowered from 0.08
            active_signals += 1
        if match_details['quantity_match']:
            active_signals += 1
        if match_details['name_match_score'] > 0.10:  # Lowered from 0.15
            active_signals += 1
        if match_details.get('id_boost', 0) > 0.05:  # Lowered from 0.08
            active_signals += 1
        
        # Need at least 2 moderate signals
        min_signals = filters.get('min_combined_signals', 2)
        if active_signals >= min_signals:
            return True
        
        # Special case: If we have ID boost + one other signal, accept
        if match_details.get('id_boost', 0) > 0.10 and active_signals >= 1:
            return True
        
        return False
    
    def establish_links(self) -> List[Dict[str, Any]]:
        """Establish all trace links."""
        
        print("Establishing trace links...")
        links = []
        
        # 1. Decomposition links (SYSTEM_REQ -> SYSTEM_REQ_DECOMPOSED)
        print("  Creating decomposition links...")
        for art_id, artifact in self.artifacts.items():
            if artifact['type'] == 'SYSTEM_REQ' and artifact.get('children'):
                for child_id in artifact['children']:
                    link = create_link(
                        art_id,
                        child_id,
                        'decomposes',
                        1.0,
                        {'decomposition': True},
                        artifact,
                        self.artifacts[child_id]
                    )
                    links.append(link)
        
        # 2. SYSTEM_REQ_DECOMPOSED -> HLR links
        print("  Linking decomposed requirements to HLRs...")
        decomposed = [a for a in self.artifacts.values() if a['type'] == 'SYSTEM_REQ_DECOMPOSED']
        layer_threshold = self.config.linking.layer_thresholds.get('SYSTEM_REQ_DECOMPOSED->HLR', 
                                                                     self.config.linking.confidence_threshold)
        print(f"    Using threshold: {layer_threshold:.2f}")
        link_count = 0
        for source in decomposed:
            candidates = self.find_candidates(source['id'], 'HLR', top_k=10)
            for target_id, score, details in candidates:
                if score >= layer_threshold:
                    link = create_link(
                        source['id'],
                        target_id,
                        'implements',
                        score,
                        details,
                        source,
                        self.artifacts[target_id]
                    )
                    links.append(link)
                    link_count += 1
        print(f"    Created {link_count} links")
        
        # 3. HLR -> LLR links
        print("  Linking HLRs to LLRs...")
        hlrs = [a for a in self.artifacts.values() if a['type'] == 'HLR']
        layer_threshold = self.config.linking.layer_thresholds.get('HLR->LLR',
                                                                     self.config.linking.confidence_threshold)
        print(f"    Using threshold: {layer_threshold:.2f}")
        link_count = 0
        for source in hlrs:
            candidates = self.find_candidates(source['id'], 'LLR', top_k=10)
            for target_id, score, details in candidates:
                if score >= layer_threshold:
                    link = create_link(
                        source['id'],
                        target_id,
                        'implements',
                        score,
                        details,
                        source,
                        self.artifacts[target_id]
                    )
                    links.append(link)
                    link_count += 1
        print(f"    Created {link_count} links")
        
        # 4. LLR -> CODE_VAR links
        print("  Linking LLRs to variables...")
        llrs = [a for a in self.artifacts.values() if a['type'] == 'LLR']
        layer_threshold = self.config.linking.layer_thresholds.get('LLR->CODE_VAR',
                                                                     self.config.linking.confidence_threshold)
        print(f"    Using threshold: {layer_threshold:.2f}")
        link_count = 0
        for source in llrs:
            candidates = self.find_candidates(source['id'], 'CODE_VAR', top_k=10)
            for target_id, score, details in candidates:
                if score >= layer_threshold:
                    link = create_link(
                        source['id'],
                        target_id,
                        'references',
                        score,
                        details,
                        source,
                        self.artifacts[target_id]
                    )
                    links.append(link)
                    link_count += 1
        print(f"    Created {link_count} links")
        
        self.links = links
        
        # Calculate and report link quality statistics
        self._report_link_quality(links)
        
        print(f"  Total links created: {len(links)}")
        
        return links
    
    def _report_link_quality(self, links: List[Dict[str, Any]]) -> None:
        """Report quality statistics for created links."""
        if not links:
            return
        
        confidence_bands = self.config.linking.confidence_bands
        
        high_conf = sum(1 for l in links if l['confidence'] >= confidence_bands['high'])
        med_conf = sum(1 for l in links if confidence_bands['medium'] <= l['confidence'] < confidence_bands['high'])
        low_conf = sum(1 for l in links if confidence_bands['low'] <= l['confidence'] < confidence_bands['medium'])
        
        print(f"\n  Link Quality Distribution:")
        print(f"    High confidence (≥{confidence_bands['high']:.2f}): {high_conf} links ({high_conf/len(links)*100:.0f}%)")
        print(f"    Medium confidence (≥{confidence_bands['medium']:.2f}): {med_conf} links ({med_conf/len(links)*100:.0f}%)")
        print(f"    Low confidence (≥{confidence_bands['low']:.2f}): {low_conf} links ({low_conf/len(links)*100:.0f}%)")
        
        avg_conf = sum(l['confidence'] for l in links) / len(links)
        print(f"    Average confidence: {avg_conf:.2f}")
