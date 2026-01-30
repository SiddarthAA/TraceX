"""
Requirement Understanding Layer - extracts structured meaning from requirements.
"""
from typing import List
from src.models import Requirement, HLR, LLR, StructuredRequirement, RequirementType
from src.model_provider import ModelProvider


class RequirementUnderstandingLayer:
    """Extract structured semantic understanding from requirements."""
    
    def __init__(self, model_provider: ModelProvider):
        self.model_provider = model_provider
    
    def understand_requirements(self, requirements: List[Requirement]) -> List[Requirement]:
        """Process all requirements to extract structured meaning."""
        for req in requirements:
            req.structured = self._extract_structure(req)
        return requirements
    
    def _extract_structure(self, requirement: Requirement) -> StructuredRequirement:
        """Extract structured information from a single aerospace requirement."""
        
        prompt = f"""Analyze this aerospace system requirement and extract structured information for DO-178C traceability analysis.

Requirement ID: {requirement.id}
Title: {requirement.title}
Description: {requirement.description}
Type: {requirement.type}
Safety Level: {requirement.safety_level}

Extract the following with aerospace context in mind:

1. **intent_verb**: The primary action verb describing what the system must do
   Examples: maintain, control, detect, compute, respond, limit, monitor, prevent, provide, execute
   
2. **subject**: The aerospace system, subsystem, or component performing the action
   Examples: flight control system, actuator, sensor, algorithm, avionics, computer, monitor
   
3. **object**: What is being acted upon or controlled
   Examples: pitch attitude, control surface, sensor data, flight envelope, aircraft state
   
4. **constraint**: Specific timing, accuracy, range, or performance bounds (extract exact values if present)
   Examples: "within 30ms", "±2 degrees", "100 Hz minimum", "< 10% error", "DAL-A compliance"
   Leave empty if no specific constraint mentioned.
   
5. **requirement_type**: Classify as one of:
   - functional: Core system functionality or behavior
   - performance: Timing, accuracy, throughput, latency requirements
   - safety: Fault detection, failure handling, envelope protection, DAL compliance
   - interface: Data exchange, communication protocols
   - diagnostic: Logging, monitoring, health management
   - other: If none of the above apply
   
6. **abstraction_level**: Determine hierarchical level:
   - system: Whole aircraft or flight control system level
   - subsystem: Major functional group (e.g., pitch control, navigation)
   - component: Individual hardware/software module (e.g., actuator, IMU, algorithm)
   
7. **key_concepts**: Extract 3-5 domain-specific technical terms that are critical for understanding relationships
   Focus on: aerospace systems, control theory, avionics, sensors, actuators, algorithms, safety standards
   Examples: ["pitch control", "actuator", "latency", "DAL-B"], ["envelope protection", "angle of attack", "limit"]

IMPORTANT FOR AEROSPACE TRACEABILITY:
- Identify causal relationships (e.g., "fast response enables stability")
- Recognize control loop components (sensors → processing → actuation)
- Understand DO-178C safety levels (DAL-A = most critical, DAL-D = least critical)
- Note timing constraints critical for real-time control systems
- Identify aircraft flight dynamics terms (pitch, roll, yaw, attitude, envelope)

Respond with ONLY a valid JSON object matching this structure (no markdown, no extra text):"""
        
        schema = {
            "intent_verb": "string",
            "subject": "string",
            "object": "string",
            "constraint": "string or null",
            "requirement_type": "string (functional|performance|safety|interface|diagnostic|other)",
            "abstraction_level": "string (system|subsystem|component)",
            "key_concepts": ["string"]
        }
        
        try:
            result = self.model_provider.generate_structured(prompt, schema)
            
            # Map requirement_type string to enum
            req_type_map = {
                "functional": RequirementType.FUNCTIONAL,
                "performance": RequirementType.PERFORMANCE,
                "safety": RequirementType.SAFETY,
                "interface": RequirementType.INTERFACE,
                "diagnostic": RequirementType.DIAGNOSTIC,
                "other": RequirementType.OTHER
            }
            
            return StructuredRequirement(
                intent_verb=result.get("intent_verb", ""),
                subject=result.get("subject", ""),
                object=result.get("object", ""),
                constraint=result.get("constraint"),
                requirement_type=req_type_map.get(result.get("requirement_type", "other").lower(), RequirementType.OTHER),
                abstraction_level=result.get("abstraction_level", "system"),
                key_concepts=result.get("key_concepts", [])
            )
        except Exception as e:
            print(f"Error extracting structure for {requirement.id}: {e}")
            # Return default structure
            return StructuredRequirement(
                intent_verb="unknown",
                subject=requirement.title,
                object=requirement.description[:50],
                requirement_type=RequirementType.OTHER,
                abstraction_level="system",
                key_concepts=[]
            )
