"""
Link Reasoning Engine - evaluates candidates and makes traceability decisions.
"""
from typing import List, Dict, Tuple
from src.models import (
    HLR, LLR, CandidateLink, TraceabilityLink, 
    LinkType, CoverageType, ReasoningTrace
)
from src.model_provider import ModelProvider


class LinkReasoningEngine:
    """Evaluate candidate links and make traceability decisions."""
    
    def __init__(self, reasoning_model: ModelProvider):
        self.reasoning_model = reasoning_model
    
    def evaluate_candidates(
        self, 
        candidates_map: Dict[str, List[CandidateLink]], 
        hlrs: List[HLR], 
        llrs: List[LLR]
    ) -> List[TraceabilityLink]:
        """Evaluate all candidate links and create traceability links."""
        
        # Create lookup dictionaries
        hlr_dict = {hlr.id: hlr for hlr in hlrs}
        llr_dict = {llr.id: llr for llr in llrs}
        
        all_links = []
        
        for hlr_id, candidates in candidates_map.items():
            hlr = hlr_dict[hlr_id]
            
            for candidate in candidates:
                llr = llr_dict[candidate.llr_id]
                
                # Evaluate the candidate
                link = self._evaluate_single_candidate(hlr, llr, candidate)
                
                # Only keep links with reasonable confidence
                if link.confidence >= 0.3:  # Threshold
                    all_links.append(link)
        
        return all_links
    
    def _evaluate_single_candidate(
        self, 
        hlr: HLR, 
        llr: LLR, 
        candidate: CandidateLink
    ) -> TraceabilityLink:
        """Evaluate a single candidate link using multi-dimensional reasoning."""
        
        # 1. Type compatibility check
        type_compatible = self._check_type_compatibility(hlr, llr)
        
        # 2. Safety level check
        safety_compatible = self._check_safety_compatibility(hlr, llr)
        
        # 3. Generate detailed reasoning using LLM
        reasoning_trace, explanation = self._generate_reasoning(hlr, llr, candidate)
        
        # 4. Make final decision
        decision = self._make_decision(
            type_compatible, 
            safety_compatible, 
            candidate.combined_score,
            reasoning_trace.decision
        )
        
        # 5. Determine link type and coverage
        link_type, coverage = self._determine_link_type_and_coverage(decision, reasoning_trace)
        
        # 6. Calculate confidence
        confidence = self._calculate_confidence(
            candidate.combined_score,
            type_compatible,
            safety_compatible,
            decision
        )
        
        return TraceabilityLink(
            hlr_id=hlr.id,
            llr_id=llr.id,
            link_type=link_type,
            coverage=coverage,
            confidence=confidence,
            explanation=explanation,
            reasoning_trace=reasoning_trace,
            accepted=(decision == "ACCEPT")
        )
    
    def _check_type_compatibility(self, hlr: HLR, llr: LLR) -> bool:
        """Check if requirement types are compatible."""
        # Incompatible combinations
        incompatible = [
            (("functional", "safety"), ("diagnostic",)),
            (("safety",), ("diagnostic",)),
        ]
        
        hlr_type = hlr.type.lower()
        llr_type = llr.type.lower()
        
        for hlr_types, llr_types in incompatible:
            if hlr_type in hlr_types and llr_type in llr_types:
                return False
        
        return True
    
    def _check_safety_compatibility(self, hlr: HLR, llr: LLR) -> bool:
        """Check if safety levels are compatible."""
        # Safety level hierarchy (higher number = more critical)
        safety_hierarchy = {
            "dal-a": 4, "asil-d": 4,
            "dal-b": 3, "asil-c": 3,
            "dal-c": 2, "asil-b": 2,
            "dal-d": 1, "asil-a": 1,
            "qm": 0, "not_specified": 0
        }
        
        hlr_level = safety_hierarchy.get(hlr.safety_level.lower(), 0)
        llr_level = safety_hierarchy.get(llr.safety_level.lower(), 0)
        
        # LLR should be at same or higher safety level than HLR
        return llr_level >= hlr_level
    
    def _generate_reasoning(
        self, 
        hlr: HLR, 
        llr: LLR, 
        candidate: CandidateLink
    ) -> Tuple[ReasoningTrace, str]:
        """Generate detailed aerospace-specific reasoning using LLM."""
        
        prompt = f"""You are an aerospace systems engineer evaluating requirements traceability for DO-178C compliance.

Evaluate whether this Low-Level Requirement (LLR) implements or contributes to this High-Level Requirement (HLR).

═══════════════════════════════════════════════════════════════
HIGH-LEVEL REQUIREMENT (HLR-{hlr.id})
═══════════════════════════════════════════════════════════════
Title: {hlr.title}
Description: {hlr.description}
Type: {hlr.type}
Safety Level: {hlr.safety_level} (DO-178C)

Semantic Understanding:
- Primary Intent: {hlr.structured.intent_verb if hlr.structured else 'N/A'}
- System/Subsystem: {hlr.structured.subject if hlr.structured else 'N/A'}
- Controlled Object: {hlr.structured.object if hlr.structured else 'N/A'}
- Abstraction Level: {hlr.structured.abstraction_level if hlr.structured else 'N/A'}
- Key Aerospace Concepts: {', '.join(hlr.structured.key_concepts) if hlr.structured else 'N/A'}

═══════════════════════════════════════════════════════════════
LOW-LEVEL REQUIREMENT (LLR-{llr.id})
═══════════════════════════════════════════════════════════════
Title: {llr.title}
Description: {llr.description}
Type: {llr.type}
Component: {llr.component or 'N/A'}
Safety Level: {llr.safety_level} (DO-178C)

Semantic Understanding:
- Primary Intent: {llr.structured.intent_verb if llr.structured else 'N/A'}
- Component/Module: {llr.structured.subject if llr.structured else 'N/A'}
- Target Object: {llr.structured.object if llr.structured else 'N/A'}
- Constraint/Spec: {llr.structured.constraint if llr.structured else 'N/A'}
- Abstraction Level: {llr.structured.abstraction_level if llr.structured else 'N/A'}
- Key Concepts: {', '.join(llr.structured.key_concepts) if llr.structured else 'N/A'}

═══════════════════════════════════════════════════════════════
SIMILARITY METRICS
═══════════════════════════════════════════════════════════════
- Semantic Embedding Similarity: {candidate.embedding_score:.3f} (0-1 scale)
- Lexical BM25 Score: {candidate.bm25_score:.3f}
- Overlapping Technical Terms: {', '.join(candidate.ontology_overlap) if candidate.ontology_overlap else 'None'}

═══════════════════════════════════════════════════════════════
EVALUATION CRITERIA (Aerospace Traceability)
═══════════════════════════════════════════════════════════════

Evaluate the following 5 dimensions for aerospace system traceability:

1. **Intent Alignment (Functional Decomposition)**
   Does the LLR's specific function directly enable or support the HLR's system-level goal?
   Consider: control loops (sense → compute → actuate), data flow, timing chains
   Example: "Fast actuator response (LLR) enables stable pitch control (HLR)"
   Provide 2-3 sentences explaining the functional relationship.

2. **Conceptual Chain (Causal Dependencies)**
   Is there a clear causal or dependency path between HLR and LLR?
   Consider: physics-based dependencies, control theory, sensor-actuator chains
   Example: "Stability requires control loop → control requires fast computation"
   Identify if this is direct causation, enabling relationship, or part of larger chain.
   Provide 2-3 sentences.

3. **Type Compatibility (Requirement Classification)**
   Are the requirement types logically compatible for traceability?
   Valid patterns: functional→performance, functional→functional, safety→safety
   Invalid patterns: functional→diagnostic, safety→diagnostic
   Provide 1-2 sentences on compatibility.

4. **Safety Consistency (DO-178C DAL Compliance)**
   Are the DO-178C Design Assurance Levels compatible?
   Rule: LLR must be at same or higher criticality than HLR
   DAL-A (most critical) > DAL-B > DAL-C > DAL-D (least critical)
   Example: DAL-A HLR can only be implemented by DAL-A LLRs
   Provide 1-2 sentences on safety level compatibility.

5. **Coverage Logic (Implementation Completeness)**
   Is this LLR sufficient alone to implement the HLR, or is it one of multiple needed?
   Consider: Does HLR need sensor + processing + actuation? Or just one component?
   Classify as: FULL (sufficient alone), PARTIAL (one of many needed), or NONE
   Provide 2-3 sentences explaining completeness.

═══════════════════════════════════════════════════════════════
FINAL DECISION
═══════════════════════════════════════════════════════════════

Based on the 5 dimensions above, make a traceability decision:
- ACCEPT: Strong link, clear implementation relationship
- PARTIAL: Valid but incomplete link, part of larger implementation set
- REJECT: No meaningful link, incompatible types, or insufficient relationship

Return your analysis as a JSON object with the exact structure below:"""
        
        schema = {
            "intent_alignment": "string (2-3 sentences)",
            "conceptual_chain": "string (2-3 sentences)",
            "type_compatibility": "string (1-2 sentences)",
            "safety_consistency": "string (1-2 sentences)",
            "coverage_logic": "string (1-2 sentences)",
            "decision": "string (ACCEPT|REJECT|PARTIAL)"
        }
        
        try:
            result = self.reasoning_model.generate_structured(prompt, schema)
            
            reasoning_trace = ReasoningTrace(
                intent_alignment=result.get("intent_alignment", ""),
                conceptual_chain=result.get("conceptual_chain", ""),
                type_compatibility=result.get("type_compatibility", ""),
                safety_consistency=result.get("safety_consistency", ""),
                coverage_logic=result.get("coverage_logic", ""),
                decision=result.get("decision", "REJECT")
            )
            
            # Generate human-readable explanation
            explanation = self._format_explanation(hlr, llr, reasoning_trace)
            
            return reasoning_trace, explanation
            
        except Exception as e:
            print(f"Error generating reasoning for {hlr.id} -> {llr.id}: {e}")
            # Return default reasoning
            reasoning_trace = ReasoningTrace(
                intent_alignment="Unable to evaluate",
                conceptual_chain="Unable to evaluate",
                type_compatibility="Unable to evaluate",
                safety_consistency="Unable to evaluate",
                coverage_logic="Unable to evaluate",
                decision="REJECT"
            )
            explanation = f"Error during reasoning: {str(e)}"
            return reasoning_trace, explanation
    
    def _format_explanation(self, hlr: HLR, llr: LLR, trace: ReasoningTrace) -> str:
        """Format a human-readable explanation."""
        if trace.decision == "ACCEPT" or trace.decision == "PARTIAL":
            return f"""{hlr.id} is linked to {llr.id} because:

Intent Alignment: {trace.intent_alignment}

Conceptual Chain: {trace.conceptual_chain}

Type Compatibility: {trace.type_compatibility}

Safety Consistency: {trace.safety_consistency}

Coverage: {trace.coverage_logic}"""
        else:
            return f"""{hlr.id} is NOT linked to {llr.id} because:

Intent Alignment: {trace.intent_alignment}

Conceptual Chain: {trace.conceptual_chain}

This LLR does not contribute to fulfilling the HLR."""
    
    def _make_decision(
        self, 
        type_compatible: bool, 
        safety_compatible: bool, 
        combined_score: float,
        llm_decision: str
    ) -> str:
        """Make final decision based on all factors."""
        # Hard constraints
        if not type_compatible or not safety_compatible:
            return "REJECT"
        
        # Low similarity threshold
        if combined_score < 0.3:
            return "REJECT"
        
        # Use LLM decision
        return llm_decision
    
    def _determine_link_type_and_coverage(
        self, 
        decision: str, 
        trace: ReasoningTrace
    ) -> Tuple[LinkType, CoverageType]:
        """Determine link type and coverage based on decision."""
        if decision == "REJECT":
            return LinkType.NOT_LINKED, CoverageType.NONE
        elif decision == "PARTIAL":
            return LinkType.CONTRIBUTES, CoverageType.PARTIAL
        else:  # ACCEPT
            # Check if it's full or partial coverage based on reasoning
            if "partial" in trace.coverage_logic.lower():
                return LinkType.SUPPORTS, CoverageType.PARTIAL
            else:
                return LinkType.IMPLEMENTS, CoverageType.FULL
    
    def _calculate_confidence(
        self, 
        combined_score: float, 
        type_compatible: bool, 
        safety_compatible: bool,
        decision: str
    ) -> float:
        """Calculate confidence score."""
        base_confidence = combined_score
        
        if not type_compatible:
            base_confidence *= 0.5
        if not safety_compatible:
            base_confidence *= 0.5
        
        if decision == "REJECT":
            base_confidence *= 0.3
        elif decision == "PARTIAL":
            base_confidence *= 0.7
        
        return min(max(base_confidence, 0.0), 1.0)
