"""LLM-based gap reasoning with rate limiting."""

import json
from typing import Dict, Any, List
from groq import Groq
from src.decompose.prompts import GAP_REASONING_SYSTEM_PROMPT, GAP_REASONING_USER_PROMPT
from src.utils.api_utils import rate_limiter, api_tracker


def gather_gap_context(
    gap: Dict[str, Any],
    artifacts: Dict[str, Any],
    graph: Dict[str, Any],
    indexer
) -> Dict[str, Any]:
    """Gather relevant context for gap reasoning."""
    
    context = {}
    
    artifact_id = gap.get('artifact_id') or (gap.get('chain', [None])[-1])
    
    if artifact_id:
        artifact = artifacts.get(artifact_id, {})
        context['artifact'] = artifact
        context['artifact_id'] = artifact_id
        context['artifact_text'] = artifact.get('text', '')
        context['artifact_type'] = artifact.get('type', '')
        
        # Get parents and children
        context['parents'] = graph.get('edges_up', {}).get(artifact_id, [])
        context['children'] = graph.get('edges_down', {}).get(artifact_id, [])
        
        # Find near-miss candidates
        context['near_misses'] = find_near_misses(
            artifact_id,
            artifacts,
            indexer,
            threshold=0.35,
            top_k=3
        )
    
    return context


def find_near_misses(
    artifact_id: str,
    artifacts: Dict[str, Any],
    indexer,
    threshold: float = 0.35,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """Find artifacts that almost matched but weren't linked."""
    
    # Get embedding
    embedding = indexer.get_embedding(artifact_id)
    if embedding is None:
        return []
    
    # Search for similar
    candidates = indexer.search_similar(
        query_embedding=embedding,
        top_k=top_k * 2,
        threshold=threshold
    )
    
    near_misses = []
    for candidate_id, score in candidates:
        if candidate_id != artifact_id:
            candidate = artifacts.get(candidate_id)
            if candidate:
                near_misses.append({
                    'candidate_id': candidate_id,
                    'similarity': score,
                    'candidate_type': candidate['type'],
                    'candidate_text': candidate['text'][:200]
                })
    
    return near_misses[:top_k]


def explain_gap(
    gap: Dict[str, Any],
    artifacts: Dict[str, Any],
    graph: Dict[str, Any],
    indexer,
    groq_client: Groq
) -> Dict[str, Any]:
    """Generate detailed explanation for a gap using LLM."""
    
    # Gather context
    context = gather_gap_context(gap, artifacts, graph, indexer)
    
    # Build prompt
    near_miss_text = ""
    for nm in context.get('near_misses', []):
        near_miss_text += f"\n- {nm['candidate_id']} ({nm['candidate_type']}, similarity: {nm['similarity']:.2f}): {nm['candidate_text']}"
    
    if not near_miss_text:
        near_miss_text = "\nNone found"
    
    user_prompt = GAP_REASONING_USER_PROMPT.format(
        gap_type=gap.get('type', 'unknown'),
        severity=gap.get('severity', 'unknown'),
        artifact_id=context.get('artifact_id', 'N/A'),
        artifact_type=context.get('artifact_type', 'N/A'),
        artifact_text=context.get('artifact_text', 'N/A'),
        parent_ids=', '.join(context.get('parents', [])) if context.get('parents') else 'None',
        parent_count=len(context.get('parents', [])),
        children_ids=', '.join(context.get('children', [])) if context.get('children') else 'None',
        children_count=len(context.get('children', [])),
        expected_parent_type=gap.get('expected_parent_type', 'N/A'),
        expected_child_type=gap.get('expected_child_type', 'N/A'),
        chain_path=' -> '.join(gap.get('chain', [])) if gap.get('chain') else 'N/A',
        break_point=gap.get('break_point', 'N/A'),
        near_miss_list=near_miss_text
    )
    
    try:
        # Call Groq API with rate limiting
        def make_api_call():
            return groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": GAP_REASONING_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
        
        response = rate_limiter.call_with_retry(make_api_call)
        
        # Track API call
        api_tracker.log_call(
            model="llama-3.3-70b-versatile",
            purpose="gap_reasoning",
            tokens_input=response.usage.prompt_tokens,
            tokens_output=response.usage.completion_tokens
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Enhance gap with reasoning
        gap['reasoning'] = result.get('reasoning', 'No reasoning provided')
        gap['root_cause'] = result.get('root_cause', 'unknown')
        gap['root_cause_explanation'] = result.get('root_cause_explanation', '')
        gap['impact'] = result.get('impact', {})
        gap['suggestions'] = result.get('suggestions', [])
        gap['potential_links'] = result.get('potential_links', [])
        
    except Exception as e:
        print(f"  Error generating reasoning for {gap['gap_id']}: {e}")
        gap['reasoning'] = f"Error generating reasoning: {str(e)}"
        gap['root_cause'] = 'error'
    
    return gap


def explain_all_gaps(
    gaps: List[Dict[str, Any]],
    artifacts: Dict[str, Any],
    graph: Dict[str, Any],
    indexer,
    groq_client: Groq
) -> List[Dict[str, Any]]:
    """Generate explanations for all gaps."""
    
    if not gaps:
        return gaps
    
    print(f"Generating LLM reasoning for {len(gaps)} gaps...")
    
    enhanced_gaps = []
    for i, gap in enumerate(gaps, 1):
        print(f"  Processing gap {i}/{len(gaps)}: {gap['gap_id']}")
        enhanced_gap = explain_gap(gap, artifacts, graph, indexer, groq_client)
        enhanced_gaps.append(enhanced_gap)
    
    return enhanced_gaps
