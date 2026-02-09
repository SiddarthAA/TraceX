"""LLM-based requirement decomposition with rate limiting."""

import json
from typing import Dict, Any, List
from groq import Groq
from src.decompose.prompts import DECOMPOSITION_SYSTEM_PROMPT, DECOMPOSITION_USER_PROMPT
from src.utils.text_utils import extract_keywords, extract_quantities
from src.utils.api_utils import rate_limiter, api_tracker


def detect_complex_requirement(requirement: Dict[str, Any]) -> bool:
    """
    Detect if a requirement is complex and needs decomposition.
    
    Heuristics:
    - Contains conjunctions (and, or)
    - Contains multiple quantities
    - Contains multiple conditions (when, upon, if)
    - Text length > 150 characters
    """
    text = requirement['text'].lower()
    
    # Check for conjunctions
    if ' and ' in text or ' or ' in text:
        return True
    
    # Check for multiple quantities
    quantities = requirement['extracted'].get('quantities', [])
    if len(quantities) > 1:
        return True
    
    # Check for multiple conditions
    condition_words = ['when', 'upon', 'if', 'under', 'during', 'while']
    condition_count = sum(1 for word in condition_words if word in text)
    if condition_count > 1:
        return True
    
    # Check text length
    if len(text) > 150:
        return True
    
    return False


def decompose_requirement(
    requirement: Dict[str, Any],
    groq_client: Groq
) -> List[Dict[str, Any]]:
    """
    Decompose a single system requirement using Groq LLM.
    
    Returns list of decomposed sub-requirement artifacts.
    """
    # Check if already decomposed
    if requirement.get('decomposed', False) or requirement.get('children', []):
        return []
    
    # Check if complex enough to decompose
    if not detect_complex_requirement(requirement):
        # Already atomic - create single decomposed version
        child_id = f"{requirement['id']}-A"
        child = {
            'id': child_id,
            'type': 'SYSTEM_REQ_DECOMPOSED',
            'parent_id': requirement['id'],
            'text': requirement['text'],
            'metadata': {
                **requirement.get('metadata', {}),
                'aspect': 'complete',
                'decomposition_reason': 'Already atomic'
            },
            'extracted': requirement.get('extracted', {}),
            'decomposed': True,
            'children': []
        }
        return [child]
    
    # Build prompt
    user_prompt = DECOMPOSITION_USER_PROMPT.format(
        requirement_id=requirement['id'],
        requirement_text=requirement['text'],
        category=requirement.get('metadata', {}).get('category', 'General')
    )
    
    # Call Groq API with rate limiting
    try:
        def make_api_call():
            return groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": DECOMPOSITION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
        
        response = rate_limiter.call_with_retry(make_api_call)
        
        # Track API call
        api_tracker.log_call(
            model="llama-3.3-70b-versatile",
            purpose="decompose_req",
            tokens_input=response.usage.prompt_tokens,
            tokens_output=response.usage.completion_tokens
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Create child artifacts
        children = []
        for sub_req in result.get('sub_requirements', []):
            child_id = f"{requirement['id']}-{sub_req['suffix']}"
            
            child = {
                'id': child_id,
                'type': 'SYSTEM_REQ_DECOMPOSED',
                'parent_id': requirement['id'],
                'text': sub_req['text'],
                'metadata': {
                    **requirement.get('metadata', {}),
                    'aspect': sub_req.get('aspect', 'general'),
                    'testable': sub_req.get('testable', True),
                    'test_approach': sub_req.get('test_approach', ''),
                    'decomposition_rationale': result.get('decomposition_rationale', '')
                },
                'extracted': {
                    'keywords': sub_req.get('keywords', []),
                    'quantities': sub_req.get('quantities', []),
                    'referenced_ids': list(extract_keywords(sub_req['text']))
                },
                'decomposed': True,
                'children': []
            }
            
            children.append(child)
        
        return children
        
    except Exception as e:
        print(f"Error decomposing {requirement['id']}: {e}")
        # Fallback: create single atomic version
        child_id = f"{requirement['id']}-A"
        child = {
            'id': child_id,
            'type': 'SYSTEM_REQ_DECOMPOSED',
            'parent_id': requirement['id'],
            'text': requirement['text'],
            'metadata': {
                **requirement.get('metadata', {}),
                'aspect': 'complete',
                'decomposition_error': str(e)
            },
            'extracted': requirement.get('extracted', {}),
            'decomposed': True,
            'children': []
        }
        return [child]


def decompose_all_system_requirements(
    artifacts: Dict[str, Any],
    groq_client: Groq
) -> Dict[str, Any]:
    """
    Decompose all SYSTEM_REQ type artifacts.
    
    Returns updated artifacts dictionary with decomposed children added.
    """
    updated_artifacts = artifacts.copy()
    
    # Find all system requirements
    sys_reqs = [art for art in artifacts.values() if art['type'] == 'SYSTEM_REQ']
    
    print(f"Decomposing {len(sys_reqs)} system requirements...")
    
    for sys_req in sys_reqs:
        print(f"  Decomposing {sys_req['id']}...")
        
        # Decompose
        children = decompose_requirement(sys_req, groq_client)
        
        # Add children to artifacts
        for child in children:
            updated_artifacts[child['id']] = child
        
        # Update parent's children list
        child_ids = [child['id'] for child in children]
        updated_artifacts[sys_req['id']]['children'] = child_ids
        updated_artifacts[sys_req['id']]['decomposed'] = True
        
        print(f"    Created {len(children)} sub-requirements")
    
    return updated_artifacts
