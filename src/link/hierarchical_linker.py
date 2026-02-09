"""Hierarchical layer-by-layer linking with LLM reasoning."""

from typing import Dict, List, Tuple, Any, Set
from datetime import datetime
import uuid
from groq import Groq

from src.link.linker import (
    compute_keyword_score,
    compute_quantity_match,
    compute_variable_name_match,
    compute_id_relationship_boost,
    compute_combined_score,
    generate_link_rationale,
    create_link
)
from src.utils.api_utils import rate_limit_decorator, api_tracker_decorator
from config import Config


LLM_SELECTION_SYSTEM_PROMPT = """You are an expert aerospace requirements traceability analyst.

Your task is to analyze candidate links between requirements at different abstraction levels and determine which candidates ACTUALLY implement the source requirement.

A good implementation match means:
- The target requirement directly addresses the source requirement
- Key technical concepts align (keywords, quantities, constraints)
- The target provides sufficient detail to satisfy the source
- There is clear semantic relationship beyond surface similarity

You will be given:
1. A source requirement at a higher abstraction level
2. Multiple candidate requirements at the next level down
3. Match scores and details for each candidate

Respond with VALID JSON only (no comments, no text outside JSON):
{
  "selected_targets": [
    {
      "target_id": "HLR-001-A",
      "reasoning": "Brief explanation of why this implements the source",
      "confidence": 0.85
    }
  ],
  "rejected_targets": [
    {
      "target_id": "HLR-002-B", 
      "reason": "Why this was rejected"
    }
  ]
}

CRITICAL RULES:
- confidence MUST be a decimal number between 0.0 and 1.0 (e.g., 0.85, 0.72, 0.91)
- DO NOT write confidence as words (e.g., "0.nine" is INVALID, use "0.9")
- DO NOT include comments in the JSON
- Be selective: Only select targets that TRULY implement the source
- Multiple targets can implement one source (common for decomposition)
- Confidence should reflect implementation strength (0.7+ for good match)
- Reject candidates that are merely semantically similar but don't implement
"""


class HierarchicalLinker:
    """
    Layer-by-layer hierarchical linker with LLM reasoning.
    
    Links are established one layer at a time:
    1. SYSTEM_REQ -> SYSTEM_REQ_DECOMPOSED (deterministic)
    2. SYSTEM_REQ_DECOMPOSED -> HLR (multi-signal + LLM)
    3. HLR -> LLR (multi-signal + LLM)
    4. LLR -> CODE_VAR (multi-signal + LLM)
    
    After all layers are linked, chains are formed by traversing connections.
    """
    
    def __init__(
        self,
        artifacts: Dict[str, Any],
        indexer: Any,
        config: Config,
        groq_client: Groq = None
    ):
        self.artifacts = artifacts
        self.indexer = indexer
        self.config = config
        self.groq_client = groq_client
        self.links = []
        
        # Statistics
        self.stats = {
            'decomposition': 0,
            'sys_to_hlr': {'candidates': 0, 'llm_calls': 0, 'selected': 0},
            'hlr_to_llr': {'candidates': 0, 'llm_calls': 0, 'selected': 0},
            'llr_to_var': {'candidates': 0, 'llm_calls': 0, 'selected': 0}
        }
    
    def establish_all_links(self) -> List[Dict[str, Any]]:
        """
        Establish all links layer-by-layer.
        
        Returns: List of all created links
        """
        print("\n=== Layer-by-Layer Hierarchical Linking ===")
        
        # Layer 1: Decomposition (deterministic)
        self._link_decomposition()
        
        # Layer 2: Decomposed -> HLR (multi-signal + LLM)
        self._link_layer(
            source_type='SYSTEM_REQ_DECOMPOSED',
            target_type='HLR',
            layer_name='sys_to_hlr',
            use_llm=True
        )
        
        # Layer 3: HLR -> LLR (multi-signal + LLM)
        self._link_layer(
            source_type='HLR',
            target_type='LLR',
            layer_name='hlr_to_llr',
            use_llm=True
        )
        
        # Layer 4: LLR -> Variables (multi-signal + LLM)
        self._link_layer(
            source_type='LLR',
            target_type='CODE_VAR',
            layer_name='llr_to_var',
            use_llm=True
        )
        
        # Report statistics
        self._report_statistics()
        
        return self.links
    
    def _link_decomposition(self) -> None:
        """Link SYSTEM_REQ to their decomposed children (deterministic)."""
        print("\n[Layer 1] Linking SYSTEM_REQ -> SYSTEM_REQ_DECOMPOSED...")
        
        for art_id, artifact in self.artifacts.items():
            if artifact['type'] == 'SYSTEM_REQ' and artifact.get('children'):
                for child_id in artifact['children']:
                    link = create_link(
                        art_id,
                        child_id,
                        'decomposes',
                        1.0,
                        {'decomposition': True, 'method': 'deterministic'},
                        artifact,
                        self.artifacts[child_id]
                    )
                    self.links.append(link)
                    self.stats['decomposition'] += 1
        
        print(f"  Created {self.stats['decomposition']} decomposition links")
    
    def _link_layer(
        self,
        source_type: str,
        target_type: str,
        layer_name: str,
        use_llm: bool = True
    ) -> None:
        """
        Link one layer to the next using multi-signal matching + optional LLM reasoning.
        
        Args:
            source_type: Type of source artifacts (e.g., 'HLR')
            target_type: Type of target artifacts (e.g., 'LLR')
            layer_name: Name for statistics tracking
            use_llm: Whether to use LLM for final selection
        """
        print(f"\n[Layer] Linking {source_type} -> {target_type}...")
        
        # Get threshold for this layer
        layer_key = f"{source_type}->{target_type}"
        threshold = self.config.linking.layer_thresholds.get(
            layer_key,
            self.config.linking.confidence_threshold
        )
        print(f"  Confidence threshold: {threshold:.2f}")
        print(f"  LLM reasoning: {'enabled' if use_llm and self.groq_client else 'disabled'}")
        
        # Get all source artifacts
        sources = [a for a in self.artifacts.values() if a['type'] == source_type]
        print(f"  Processing {len(sources)} {source_type} artifacts...")
        
        for source in sources:
            # Find candidates using multi-signal matching
            candidates = self._find_candidates(
                source,
                target_type,
                threshold=threshold * 0.7  # Lower threshold for candidate generation
            )
            
            self.stats[layer_name]['candidates'] += len(candidates)
            
            if not candidates:
                continue
            
            # Use LLM to select best matches if enabled
            if use_llm and self.groq_client and len(candidates) > 1:
                selected = self._llm_select_targets(source, candidates, layer_name)
                self.stats[layer_name]['llm_calls'] += 1
            else:
                # No LLM: accept all candidates above threshold
                selected = [
                    {
                        'target_id': c['target_id'],
                        'confidence': c['score'],
                        'reasoning': c['match_details'].get('rationale', 'Multi-signal match'),
                        'match_details': c['match_details']
                    }
                    for c in candidates
                ]
            
            # Create links for selected targets
            for sel in selected:
                target = self.artifacts[sel['target_id']]
                
                # Update match details with LLM reasoning
                match_details = sel.get('match_details', {})
                match_details['llm_reasoning'] = sel.get('reasoning', '')
                match_details['llm_confidence'] = sel.get('confidence')
                match_details['method'] = 'multi-signal + llm' if use_llm else 'multi-signal'
                
                link = create_link(
                    source['id'],
                    sel['target_id'],
                    'implements',
                    sel['confidence'],
                    match_details,
                    source,
                    target
                )
                self.links.append(link)
                self.stats[layer_name]['selected'] += 1
        
        print(f"  Created {self.stats[layer_name]['selected']} links")
    
    def _find_candidates(
        self,
        source: Dict[str, Any],
        target_type: str,
        threshold: float = 0.2,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find candidate targets using multi-signal matching.
        
        Returns: List of candidate dicts with scores and details
        """
        source_id = source['id']
        
        # Get embedding similarity candidates
        embedding = self.indexer.get_embedding(source_id)
        if embedding is None:
            return []
        
        similar = self.indexer.search_similar(
            query_embedding=embedding,
            top_k=top_k * 2,
            threshold=self.config.linking.embedding_threshold
        )
        
        candidates = []
        for target_id, emb_sim in similar:
            target = self.artifacts.get(target_id)
            if not target or target['type'] != target_type:
                continue
            
            # Compute all match signals
            keyword_score, keywords = compute_keyword_score(source, target)
            quantity_match, quantities = compute_quantity_match(source, target)
            
            # Variable name matching (only for LLR -> VAR)
            name_score = 0.0
            if source['type'] == 'LLR' and target['type'] == 'CODE_VAR':
                name_score, _ = compute_variable_name_match(source, target)
            
            # ID hierarchy boost
            id_boost = compute_id_relationship_boost(source_id, target_id)
            
            # Compute combined score
            combined_score = compute_combined_score(
                embedding_sim=emb_sim,
                keyword_score=keyword_score,
                quantity_match=quantity_match,
                name_match_score=name_score,
                id_boost=id_boost
            )
            
            # Apply quality filters
            if not self._passes_quality_filters(combined_score, emb_sim, keyword_score, 
                                                  quantity_match, name_score, id_boost):
                continue
            
            if combined_score >= threshold:
                candidates.append({
                    'target_id': target_id,
                    'score': combined_score,
                    'match_details': {
                        'embedding_similarity': emb_sim,
                        'keyword_score': keyword_score,
                        'keyword_overlap': keywords,
                        'quantity_match': quantity_match,
                        'quantities_matched': quantities,
                        'name_match_score': name_score,
                        'id_boost': id_boost,
                        'combined_score': combined_score
                    }
                })
        
        # Sort by score and limit
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[:top_k]
    
    def _passes_quality_filters(
        self,
        combined_score: float,
        emb_sim: float,
        keyword_score: float,
        quantity_match: bool,
        name_score: float,
        id_boost: float
    ) -> bool:
        """
        Apply quality filters to prevent false positives.
        
        Returns: True if candidate passes quality checks
        """
        filters = self.config.linking.quality_filters
        
        # Minimum overall score
        if combined_score < filters.get('min_text_overlap', 0.05):
            return False
        
        # Strong signal check
        has_strong_signal = (
            keyword_score > 0.20 or
            emb_sim > 0.30 or
            (emb_sim > 0.20 and keyword_score > 0.12)
        )
        
        if has_strong_signal:
            return True
        
        # Multiple moderate signals (need at least 2)
        signal_count = 0
        if emb_sim > 0.12:
            signal_count += 1
        if keyword_score > 0.05:
            signal_count += 1
        if quantity_match:
            signal_count += 1
        if name_score > 0.10:
            signal_count += 1
        if id_boost > 0.05:
            signal_count += 1
        
        return signal_count >= filters.get('min_combined_signals', 2)
    
    @rate_limit_decorator(max_calls_per_minute=30)
    @api_tracker_decorator()
    def _llm_select_targets(
        self,
        source: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        layer_name: str
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to select which candidates actually implement the source.
        
        Returns: List of selected targets with reasoning
        """
        # Limit candidates to top 10 to avoid token limits
        candidates = candidates[:10]
        
        # Build prompt
        user_prompt = self._build_selection_prompt(source, candidates)
        
        try:
            response = self.groq_client.chat.completions.create(
                model=self.config.groq.model,
                messages=[
                    {"role": "system", "content": LLM_SELECTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            
            # Clean up common JSON formatting issues
            import json
            import re
            
            # Fix common issues like "0.nine" -> "0.9"
            result = re.sub(r'"confidence":\s*0\.\s*nine', '"confidence": 0.9', result, flags=re.IGNORECASE)
            result = re.sub(r'"confidence":\s*0\.\s*eight', '"confidence": 0.8', result, flags=re.IGNORECASE)
            result = re.sub(r'"confidence":\s*0\.\s*seven', '"confidence": 0.7', result, flags=re.IGNORECASE)
            result = re.sub(r'"confidence":\s*0\.\s*six', '"confidence": 0.6', result, flags=re.IGNORECASE)
            result = re.sub(r'"confidence":\s*(\d+)\.\s*(\w+)', r'"confidence": \1.\2', result)  # Fix space after decimal
            
            # Remove any comments (# ...) from JSON
            result = re.sub(r'#[^\n]*', '', result)
            
            try:
                parsed = json.loads(result)
            except json.JSONDecodeError as je:
                print(f"  JSON parse error: {je}")
                print(f"  Problematic JSON: {result[:500]}")
                # Fallback to top 3 candidates
                return [
                    {
                        'target_id': c['target_id'],
                        'confidence': c['score'],
                        'reasoning': 'JSON parse failed, using multi-signal match',
                        'match_details': c['match_details']
                    }
                    for c in candidates[:3]
                ]
            
            # Extract selected targets
            selected = parsed.get('selected_targets', [])
            
            # Validate and filter by confidence
            valid_selected = []
            for sel in selected:
                # Handle confidence as string or number
                try:
                    confidence = float(sel['confidence'])
                except (ValueError, TypeError):
                    print(f"  Warning: Invalid confidence value for {sel.get('target_id')}: {sel.get('confidence')}")
                    continue
                
                if confidence >= 0.6:  # Minimum LLM confidence
                    # Find original candidate to get match details
                    for cand in candidates:
                        if cand['target_id'] == sel['target_id']:
                            valid_selected.append({
                                'target_id': sel['target_id'],
                                'confidence': confidence,
                                'reasoning': sel['reasoning'],
                                'match_details': cand['match_details']
                            })
                            break
            
            return valid_selected
            
        except Exception as e:
            print(f"  LLM selection failed: {e}")
            # Fallback: return top 3 candidates
            return [
                {
                    'target_id': c['target_id'],
                    'confidence': c['score'],
                    'reasoning': 'LLM unavailable, using multi-signal match',
                    'match_details': c['match_details']
                }
                for c in candidates[:3]
            ]
    
    def _build_selection_prompt(
        self,
        source: Dict[str, Any],
        candidates: List[Dict[str, Any]]
    ) -> str:
        """Build LLM prompt for target selection."""
        
        prompt = f"""SOURCE REQUIREMENT:
ID: {source['id']}
Type: {source['type']}
Text: {source['text']}

CANDIDATE TARGETS (scored by multi-signal matching):

"""
        
        for i, cand in enumerate(candidates, 1):
            target = self.artifacts[cand['target_id']]
            details = cand['match_details']
            
            prompt += f"""{i}. {cand['target_id']} (Score: {cand['score']:.2f})
   Text: {target['text'][:200]}...
   Match Details:
   - Embedding similarity: {details['embedding_similarity']:.2f}
   - Keyword score: {details['keyword_score']:.2f}
   - Keywords: {', '.join(details['keyword_overlap'][:5])}
   - Quantities matched: {', '.join(details['quantities_matched'])}
   - ID relationship boost: {details['id_boost']:.2f}

"""
        
        prompt += """
Analyze these candidates and select which ones ACTUALLY implement the source requirement.
Respond in JSON format as specified in the system prompt.
"""
        
        return prompt
    
    def _report_statistics(self) -> None:
        """Report linking statistics."""
        print("\n=== Linking Statistics ===")
        print(f"Decomposition links: {self.stats['decomposition']}")
        
        for layer in ['sys_to_hlr', 'hlr_to_llr', 'llr_to_var']:
            stats = self.stats[layer]
            if stats['candidates'] > 0:
                layer_name = layer.replace('_', ' ').upper()
                print(f"\n{layer_name}:")
                print(f"  Candidates evaluated: {stats['candidates']}")
                print(f"  LLM calls made: {stats['llm_calls']}")
                print(f"  Links created: {stats['selected']}")
                if stats['candidates'] > 0:
                    selectivity = (stats['selected'] / stats['candidates']) * 100
                    print(f"  Selectivity: {selectivity:.1f}%")
        
        print(f"\nTotal links created: {len(self.links)}")
