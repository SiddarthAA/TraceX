"""
Traceability Matrix Generator - creates final matrix and reports.
"""
from typing import List, Dict
import pandas as pd
from src.models import (
    HLR, LLR, TraceabilityLink, TraceabilityMatrix, 
    GapReport, CoverageType
)


class TraceabilityMatrixGenerator:
    """Generate traceability matrix and gap analysis."""
    
    def generate_matrix(
        self, 
        hlrs: List[HLR], 
        llrs: List[LLR], 
        links: List[TraceabilityLink]
    ) -> TraceabilityMatrix:
        """Generate complete traceability matrix."""
        
        # Filter to accepted links only
        accepted_links = [link for link in links if link.accepted]
        
        # Generate gap report
        gap_report = self._generate_gap_report(hlrs, llrs, accepted_links)
        
        return TraceabilityMatrix(
            links=accepted_links,
            gap_report=gap_report,
            hlr_count=len(hlrs),
            llr_count=len(llrs),
            link_count=len(accepted_links),
            metadata={
                "total_candidates_evaluated": len(links),
                "acceptance_rate": len(accepted_links) / len(links) if links else 0
            }
        )
    
    def _generate_gap_report(
        self, 
        hlrs: List[HLR], 
        llrs: List[LLR], 
        links: List[TraceabilityLink]
    ) -> GapReport:
        """Generate gap analysis report."""
        
        # Track which requirements are linked
        hlrs_with_links = set()
        llrs_with_links = set()
        hlrs_with_partial = set()
        
        for link in links:
            hlrs_with_links.add(link.hlr_id)
            llrs_with_links.add(link.llr_id)
            
            if link.coverage == CoverageType.PARTIAL:
                hlrs_with_partial.add(link.hlr_id)
        
        # Find orphans
        orphan_hlrs = [hlr.id for hlr in hlrs if hlr.id not in hlrs_with_links]
        orphan_llrs = [llr.id for llr in llrs if llr.id not in llrs_with_links]
        
        # Calculate coverage
        coverage_percentage = (len(hlrs_with_links) / len(hlrs) * 100) if hlrs else 0
        
        return GapReport(
            orphan_hlrs=orphan_hlrs,
            orphan_llrs=orphan_llrs,
            partial_coverage_hlrs=list(hlrs_with_partial),
            coverage_percentage=coverage_percentage
        )
    
    def export_to_csv(
        self, 
        matrix: TraceabilityMatrix, 
        hlrs: List[HLR], 
        llrs: List[LLR],
        output_path: str
    ):
        """Export traceability matrix to CSV."""
        
        # Create links dataframe
        links_data = []
        for link in matrix.links:
            links_data.append({
                "HLR_ID": link.hlr_id,
                "LLR_ID": link.llr_id,
                "Link_Type": link.link_type.value,
                "Coverage": link.coverage.value,
                "Confidence": f"{link.confidence:.2f}",
                "Explanation": link.explanation
            })
        
        links_df = pd.DataFrame(links_data)
        
        # Create gap report
        gap_data = {
            "Metric": [
                "Total HLRs",
                "Total LLRs",
                "Total Links",
                "Coverage %",
                "Orphan HLRs",
                "Orphan LLRs",
                "Partial Coverage HLRs"
            ],
            "Value": [
                matrix.hlr_count,
                matrix.llr_count,
                matrix.link_count,
                f"{matrix.gap_report.coverage_percentage:.1f}%",
                len(matrix.gap_report.orphan_hlrs),
                len(matrix.gap_report.orphan_llrs),
                len(matrix.gap_report.partial_coverage_hlrs)
            ]
        }
        gap_df = pd.DataFrame(gap_data)
        
        # Export to Excel with multiple sheets
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            links_df.to_excel(writer, sheet_name='Traceability Links', index=False)
            gap_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Orphans details
            if matrix.gap_report.orphan_hlrs:
                orphan_hlrs_df = pd.DataFrame({
                    "Orphan_HLR_ID": matrix.gap_report.orphan_hlrs
                })
                orphan_hlrs_df.to_excel(writer, sheet_name='Orphan HLRs', index=False)
            
            if matrix.gap_report.orphan_llrs:
                orphan_llrs_df = pd.DataFrame({
                    "Orphan_LLR_ID": matrix.gap_report.orphan_llrs
                })
                orphan_llrs_df.to_excel(writer, sheet_name='Orphan LLRs', index=False)
    
    def create_pivot_matrix(
        self, 
        matrix: TraceabilityMatrix, 
        hlrs: List[HLR], 
        llrs: List[LLR]
    ) -> pd.DataFrame:
        """Create traditional pivot table matrix."""
        
        # Create empty matrix
        hlr_ids = [hlr.id for hlr in hlrs]
        llr_ids = [llr.id for llr in llrs]
        
        data = {llr_id: ["" for _ in hlr_ids] for llr_id in llr_ids}
        pivot_df = pd.DataFrame(data, index=hlr_ids)
        
        # Fill in links
        for link in matrix.links:
            if link.hlr_id in hlr_ids and link.llr_id in llr_ids:
                symbol = "✓"
                if link.coverage == CoverageType.PARTIAL:
                    symbol = "◐"
                elif link.coverage == CoverageType.FULL:
                    symbol = "✓✓"
                
                pivot_df.loc[link.hlr_id, link.llr_id] = symbol
        
        return pivot_df
