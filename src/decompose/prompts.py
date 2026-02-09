"""LLM prompt templates - optimized for token efficiency."""

DECOMPOSITION_SYSTEM_PROMPT = """Aerospace engineer decomposing requirements for DO-178C compliance.

Rules:
1. ONE testable condition per sub-requirement
2. Use "shall" for requirements
3. Decompose on: "and"/"or", multiple values/conditions/actors/modes
4. If atomic, return single sub-req"""

DECOMPOSITION_USER_PROMPT = """ID: {requirement_id}
Text: "{requirement_text}"
Category: {category}

JSON only:
{{
  "original_id": "{requirement_id}",
  "decomposition_rationale": "Brief why/how split",
  "sub_requirements": [
    {{
      "suffix": "A",
      "text": "component shall statement",
      "aspect": "functionality|performance|timing|interface|safety|constraint",
      "keywords": ["key1", "key2"],
      "quantities": [{{"value": 50, "unit": "feet", "constraint": "tolerance"}}],
      "testable": true,
      "test_approach": "verification method"
    }}
  ]
}}"""

GAP_REASONING_SYSTEM_PROMPT = """DO-178C traceability gap analyst. Explain gaps, assess impact, suggest fixes."""

GAP_REASONING_USER_PROMPT = """GAP: {gap_type} | SEVERITY: {severity}

ARTIFACT: {artifact_id} ({artifact_type})
Text: "{artifact_text}"

STATUS:
Parents: {parent_ids} ({parent_count}) - Expected: {expected_parent_type}
Children: {children_ids} ({children_count}) - Expected: {expected_child_type}
Chain: {chain_path} | Break: {break_point}

NEAR-MISS:
{near_miss_list}

JSON response:
{{
  "reasoning": "Why gap exists",
  "root_cause": "primary|derived|process|data_quality|other",
  "root_cause_explanation": "Specific cause",
  "impact": {{
    "certification_impact": "critical|high|medium|low",
    "impact_explanation": "Cert impact",
    "affected_objectives": ["DO-178C items"]
  }},
  "suggestions": [
    {{"action": "Fix action", "priority": "immediate|short_term|long_term", "effort": "low|medium|high"}}
  ],
  "potential_links": [
    {{"candidate_id": "ID", "why_not_linked": "Reason", "recommendation": "Should link?"}}
  ]
}}"""

LINK_VALIDATION_PROMPT = """You are validating a requirements trace link for aerospace certification (DO-178C).

SOURCE ARTIFACT:
ID: {source_id}
Type: {source_type}
Text: "{source_text}"

TARGET ARTIFACT:
ID: {target_id}
Type: {target_type}
Text: "{target_text}"

PROPOSED LINK TYPE: {link_type}

MATCHING EVIDENCE:
- Embedding similarity: {embedding_score}
- Keyword overlap: {keywords}
- Quantity match: {quantities}

TASK:
Determine if this is a valid trace link. Consider:
1. Does the target actually implement/decompose the source?
2. Is the relationship direct or indirect?
3. Are there any aspects of the source NOT covered by the target?
4. Would an auditor accept this link?

Respond in JSON:
{{
  "valid": true|false,
  "confidence": 0.0-1.0,
  "rationale": "Explanation of your assessment...",
  "coverage": "full|partial|minimal",
  "uncovered_aspects": ["List of source aspects not addressed by target"],
  "concerns": ["Any certification concerns with this link"]
}}"""
