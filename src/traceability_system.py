"""
Main Traceability System Pipeline
"""
from typing import List, Dict, Optional
from src.models import HLR, LLR, TraceabilityMatrix, TraceabilityLink
from src.requirements_loader import RequirementsLoader
from src.understanding_layer import RequirementUnderstandingLayer
from src.candidate_generator import CandidateLinkGenerator
from src.reasoning_engine import LinkReasoningEngine
from src.matrix_generator import TraceabilityMatrixGenerator
from src.model_provider import ModelProvider


class TraceabilitySystem:
    """Main system orchestrator."""
    
    def __init__(
        self, 
        structured_model: ModelProvider,
        reasoning_model: ModelProvider,
        top_k_candidates: int = 10
    ):
        self.structured_model = structured_model
        self.reasoning_model = reasoning_model
        
        self.understanding_layer = RequirementUnderstandingLayer(structured_model)
        self.candidate_generator = CandidateLinkGenerator(top_k=top_k_candidates)
        self.reasoning_engine = LinkReasoningEngine(reasoning_model)
        self.matrix_generator = TraceabilityMatrixGenerator()
        
        self.hlrs: List[HLR] = []
        self.llrs: List[LLR] = []
        self.traceability_matrix: Optional[TraceabilityMatrix] = None
    
    def load_requirements(
        self, 
        hlr_source: str, 
        llr_source: str, 
        source_type: str = "csv"
    ):
        """Load requirements from files."""
        if source_type == "csv":
            self.hlrs, self.llrs = RequirementsLoader.load_from_csv(hlr_source, llr_source)
        elif source_type == "excel":
            self.hlrs, self.llrs = RequirementsLoader.load_from_excel(hlr_source)
        elif source_type == "sample":
            self.hlrs, self.llrs = RequirementsLoader.create_sample_requirements()
        else:
            raise ValueError(f"Unknown source type: {source_type}")
        
        return len(self.hlrs), len(self.llrs)
    
    def understand_requirements(self):
        """Extract structured understanding from requirements."""
        print("Understanding HLRs...")
        self.hlrs = self.understanding_layer.understand_requirements(self.hlrs)
        
        print("Understanding LLRs...")
        self.llrs = self.understanding_layer.understand_requirements(self.llrs)
    
    def generate_traceability(self) -> TraceabilityMatrix:
        """Run complete traceability pipeline."""
        
        # Step 1: Generate candidate links
        print("\n=== Step 1: Generating Candidate Links ===")
        candidates_map = self.candidate_generator.generate_candidates(self.hlrs, self.llrs)
        total_candidates = sum(len(c) for c in candidates_map.values())
        print(f"Generated {total_candidates} candidate links")
        
        # Step 2: Evaluate candidates with reasoning
        print("\n=== Step 2: Evaluating Candidates with Reasoning ===")
        all_links = self.reasoning_engine.evaluate_candidates(
            candidates_map, self.hlrs, self.llrs
        )
        print(f"Evaluated {len(all_links)} links")
        
        # Step 3: Generate traceability matrix
        print("\n=== Step 3: Generating Traceability Matrix ===")
        self.traceability_matrix = self.matrix_generator.generate_matrix(
            self.hlrs, self.llrs, all_links
        )
        
        print(f"Final matrix: {self.traceability_matrix.link_count} accepted links")
        print(f"Coverage: {self.traceability_matrix.gap_report.coverage_percentage:.1f}%")
        
        return self.traceability_matrix
    
    def export_results(self, output_path: str):
        """Export traceability matrix to file."""
        if not self.traceability_matrix:
            raise ValueError("No traceability matrix generated yet")
        
        self.matrix_generator.export_to_csv(
            self.traceability_matrix, 
            self.hlrs, 
            self.llrs, 
            output_path
        )
    
    def get_hlr_links(self, hlr_id: str) -> List[TraceabilityLink]:
        """Get all links for a specific HLR."""
        if not self.traceability_matrix:
            return []
        
        return [link for link in self.traceability_matrix.links if link.hlr_id == hlr_id]
    
    def get_llr_links(self, llr_id: str) -> List[TraceabilityLink]:
        """Get all links for a specific LLR."""
        if not self.traceability_matrix:
            return []
        
        return [link for link in self.traceability_matrix.links if link.llr_id == llr_id]
