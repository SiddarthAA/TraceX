"""Pipeline orchestrator with visualization and API tracking."""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from groq import Groq

from config import Config
from src.ingest.parser import load_all_artifacts
from src.decompose.decomposer import decompose_all_system_requirements
from src.index.indexer import EmbeddingIndexer
from src.link.linker import LinkManager
from src.link.hierarchical_linker import HierarchicalLinker
from src.analyze.analyzer import analyze_traceability, build_trace_graph, trace_chain_forward
from src.analyze.hierarchical_analyzer import analyze_hierarchical_traceability
from src.analyze.unified_analyzer import analyze_unified_traceability
from src.analyze.reasoner import explain_all_gaps
from src.utils.file_io import save_json, load_json, save_csv
from src.utils.api_utils import api_tracker
from src.utils.visualization import generate_trace_graph_html, generate_trace_table_html
from src.utils.graph_enhanced import generate_enhanced_trace_graph
from src.utils.report_generator import generate_traceability_matrix, generate_final_report
from src.utils.matrix_enhanced import generate_enhanced_traceability_matrix
from src.utils.output_generator import generate_all_outputs


class TraceabilityPipeline:
    """Orchestrates the complete traceability analysis pipeline."""
    
    def __init__(self, config: Config):
        """Initialize pipeline with configuration."""
        self.config = config
        self.artifacts = {}
        self.links = []
        self.analysis = {}
        self.indexer = None
        self.groq_client = None
        self.graph = None
        
        # Set up Groq client
        if config.groq:
            self.groq_client = Groq(api_key=config.groq.api_key)
        
        # Create data directories
        self.data_dir = Path(config.data_dir)
        self.intermediate_dir = self.data_dir / "intermediate"
        self.output_dir = self.data_dir / "output"
        
        self.intermediate_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_data(
        self,
        system_reqs_file: str,
        hlr_file: str,
        llr_file: str,
        variables_file: str
    ) -> None:
        """Load artifacts from CSV files."""
        print("\n=== STAGE 1: Loading Data ===")
        
        data = load_all_artifacts(
            system_reqs_file,
            hlr_file,
            llr_file,
            variables_file
        )
        
        self.artifacts = data['artifacts']
        print(f"Loaded {len(self.artifacts)} artifacts")
        
        # Save intermediate result
        save_json(data, str(self.intermediate_dir / "raw_artifacts.json"))
    
    def run_decomposition(self) -> None:
        """Decompose all system requirements."""
        print("\n=== STAGE 2: Decomposing System Requirements ===")
        
        if not self.groq_client:
            print("WARNING: No Groq API key configured. Skipping decomposition.")
            return
        
        self.artifacts = decompose_all_system_requirements(
            self.artifacts,
            self.groq_client
        )
        
        # Save intermediate result
        save_json(
            {'artifacts': self.artifacts},
            str(self.intermediate_dir / "decomposed_artifacts.json")
        )
    
    def build_index(self) -> None:
        """Generate embeddings and build FAISS index."""
        print("\n=== STAGE 3: Building Embedding Index ===")
        
        self.indexer = EmbeddingIndexer(self.config.embedding.model_name)
        
        # Generate embeddings
        self.indexer.generate_all_embeddings(self.artifacts)
        
        # Build FAISS index
        self.indexer.build_faiss_index()
        
        # Save index
        index_path = str(self.intermediate_dir / "embeddings")
        self.indexer.save_index(index_path)
    
    def establish_links(self, use_hierarchical: bool = True) -> None:
        """Run linking algorithm with hierarchical layer-by-layer approach."""
        print("\n=== STAGE 4: Establishing Trace Links ===")
        
        if not self.indexer:
            print("Loading index from disk...")
            self.indexer = EmbeddingIndexer(self.config.embedding.model_name)
            index_path = str(self.intermediate_dir / "embeddings")
            self.indexer.load_index(index_path)
            
            # Load embeddings
            artifacts_data = load_json(str(self.intermediate_dir / "decomposed_artifacts.json"))
            self.artifacts = artifacts_data['artifacts']
            self.indexer.generate_all_embeddings(self.artifacts)
        
        if use_hierarchical:
            # Use new hierarchical linker with LLM reasoning
            print("Using hierarchical layer-by-layer linking...")
            hierarchical_linker = HierarchicalLinker(
                self.artifacts,
                self.indexer,
                self.config,
                self.groq_client
            )
            self.links = hierarchical_linker.establish_all_links()
        else:
            # Fallback to original linker
            print("Using original linking approach...")
            link_manager = LinkManager(self.artifacts, self.indexer, self.config)
            self.links = link_manager.establish_links()
        
        # Save links
        save_json(
            {'links': self.links},
            str(self.intermediate_dir / "links.json")
        )
    
    def analyze(self, use_llm_reasoning: bool = True, use_hierarchical: bool = True) -> None:
        """Run coverage and gap analysis."""
        print("\n=== STAGE 5: Analyzing Traceability ===")
        
        # Load data if needed
        if not self.artifacts:
            artifacts_data = load_json(str(self.intermediate_dir / "decomposed_artifacts.json"))
            self.artifacts = artifacts_data['artifacts']
        
        if not self.links:
            links_data = load_json(str(self.intermediate_dir / "links.json"))
            self.links = links_data['links']
        
        if use_hierarchical:
            # Use new hierarchical analyzer with orphan detection
            print("Using hierarchical analysis...")
            self.analysis = analyze_hierarchical_traceability(self.artifacts, self.links)
        else:
            # Fallback to original analyzer
            print("Using original analysis...")
            self.analysis = analyze_traceability(self.artifacts, self.links)
        
        # Build graph for reasoning
        self.graph = build_trace_graph(self.artifacts, self.links)
    
    def analyze_unified(self) -> None:
        """
        Perform unified analysis and generate all 5 outputs consistently.
        """
        from src.analyze.unified_analyzer import analyze_unified_traceability
        from src.utils.unified_output_generator import generate_all_outputs
        
        print("\n" + "="*80)
        print("STAGE 5: UNIFIED ANALYSIS & OUTPUT GENERATION")
        print("="*80)
        
        # Load data if needed
        if not self.artifacts:
            artifacts_data = load_json(str(self.intermediate_dir / "decomposed_artifacts.json"))
            self.artifacts = artifacts_data['artifacts']
        
        if not self.links:
            links_data = load_json(str(self.intermediate_dir / "links.json"))
            self.links = links_data['links']
        
        # Run unified analysis
        print("🔍 Analyzing traceability with unified logic...")
        self.analysis = analyze_unified_traceability(self.artifacts, self.links)
        
        # Generate all outputs
        print("\n📝 Generating unified outputs...")
        generate_all_outputs(
            self.analysis,
            self.artifacts,
            self.links,
            str(self.output_dir)
        )
        
        # Build graph for compatibility with legacy functions
        self.graph = build_trace_graph(self.artifacts, self.links)
    
    def run_full_pipeline(
        self,
        system_reqs_file: str,
        hlr_file: str,
        llr_file: str,
        variables_file: str,
        use_llm_reasoning: bool = True,
        use_hierarchical: bool = True
    ) -> Dict[str, Any]:
        """Run complete pipeline end-to-end."""
        
        print("="*80)
        print("AEROSPACE TRACEABILITY ENGINE")
        print("="*80)
        
        if use_hierarchical:
            print("🔗 Mode: Hierarchical layer-by-layer linking with LLM reasoning")
        else:
            print("🔗 Mode: Legacy all-at-once linking")
        
        # Stage 1: Load data
        self.load_data(system_reqs_file, hlr_file, llr_file, variables_file)
        
        # Stage 2: Decompose system requirements
        self.run_decomposition()
        
        # Stage 3: Build index
        self.build_index()
        
        # Stage 4: Establish links
        self.establish_links(use_hierarchical=use_hierarchical)
        
        # Stage 5: Unified Analysis & Output Generation
        if use_hierarchical:
            print("\n=== Using Unified Analysis Mode ===")
            self.analyze_unified()
            
            # Generate visualization (graph) - 5th output
            print("\n📊 Generating interactive trace graph...")
            try:
                graph_file = str(self.output_dir / "trace_graph.html")
                generate_enhanced_trace_graph(self.artifacts, self.links, graph_file)
                print(f"   5. {graph_file}")
            except Exception as e:
                print(f"   ⚠️  Graph generation error: {e}")
        else:
            # Legacy mode - original analyzer
            self.analyze(use_llm_reasoning=use_llm_reasoning, use_hierarchical=False)
        
        # Generate summary
        summary = self.get_summary()
        
        # Legacy outputs (only if not using unified mode)
        if not use_hierarchical:
            # Generate traceability matrix
            print("\n📊 Generating traceability matrices...")
            try:
                # Standard matrix
                matrix_rows = generate_traceability_matrix(
                    self.artifacts,
                    self.links,
                    self.analysis,
                    str(self.output_dir)
                )
            except Exception as e:
                print(f"   ⚠️  Matrix generation error: {e}")
                matrix_rows = []
            
            # Generate visualizations
            print("\n📊 Generating visualizations...")
            try:
                # Generate enhanced interactive graph
                graph_file = str(self.output_dir / "trace_graph.html")
                generate_enhanced_trace_graph(self.artifacts, self.links, graph_file)
                
                # Generate trace table
                table_file = str(self.output_dir / "trace_table.html")
                generate_trace_table_html(self.artifacts, self.links, self.analysis, table_file)
                
                print(f"   ✓ Interactive graph: {graph_file}")
                print(f"   ✓ Table view: {table_file}")
            except Exception as e:
                print(f"   ⚠️  Visualization error: {e}")
            
            # Generate final report
            print("\n� Generating final traceability report...")
            try:
                generate_final_report(
                    self.artifacts,
                    self.links,
                    self.analysis,
                    matrix_rows,
                    str(self.output_dir),
                    {}
                )
            except Exception as e:
                print(f"   ⚠️  Report error: {e}")
        
        # Save and print API tracking
        print("\n� Saving API call tracking...")
        try:
            tracker_file = str(self.output_dir / "api_calls.json")
            api_tracker.save(tracker_file)
            api_stats = api_tracker.get_summary()
        except Exception as e:
            print(f"   ⚠️  Tracking error: {e}")
            api_stats = {}
        
            print(f"   ⚠️  Report generation error: {e}")
        
        # Print API summary
        api_tracker.print_summary()
        
        print("\n" + "="*80)
        print("PIPELINE COMPLETE")
        print("="*80)
        self.print_summary(summary)
        
        print("\n📋 Generated Reports:")
        print(f"   • Traceability Matrix: {self.output_dir}/traceability_matrix.csv")
        print(f"   • Final Report: {self.output_dir}/TRACEABILITY_REPORT.md")
        print(f"   • Interactive Graph: {self.output_dir}/trace_graph.html")
        print(f"   • Searchable Table: {self.output_dir}/trace_table.html")
        
        return summary
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics from unified, hierarchical or legacy analysis."""
        if not self.analysis:
            return {}
        
        # Check if unified analysis format (has fully_implemented/partially_implemented)
        if 'system_requirements' in self.analysis and 'fully_implemented' in self.analysis.get('system_requirements', {}):
            # Unified format
            sys_reqs = self.analysis.get('system_requirements', {})
            hlr = self.analysis.get('high_level_requirements', {})
            llr = self.analysis.get('low_level_requirements', {})
            metrics = self.analysis.get('quality_metrics', {})
            
            return {
                'artifacts': {
                    'system_req': sys_reqs.get('total', 0),
                    'system_req_decomposed': len([a for a in self.artifacts.values() if a['type'] == 'SYSTEM_REQ_DECOMPOSED']),
                    'hlr': hlr.get('total', 0),
                    'llr': llr.get('total', 0),
                    'code_var': len([a for a in self.artifacts.values() if a['type'] == 'CODE_VAR']),
                    'total': len(self.artifacts)
                },
                'links': {
                    'total': len(self.links)
                },
                'coverage': {
                    'system_reqs_fully_implemented': sys_reqs.get('fully_implemented', {}).get('count', 0),
                    'system_reqs_partially_implemented': sys_reqs.get('partially_implemented', {}).get('count', 0),
                    'system_reqs_not_implemented': sys_reqs.get('not_implemented', {}).get('count', 0),
                    'hlr_fully_implemented': hlr.get('fully_implemented', {}).get('count', 0),
                    'hlr_partially_implemented': hlr.get('partially_implemented', {}).get('count', 0),
                    'hlr_orphaned': hlr.get('orphaned', {}).get('count', 0),
                    'llr_traced': llr.get('traced', {}).get('count', 0),
                    'llr_orphaned': llr.get('orphaned', {}).get('count', 0),
                    'overall_rate': metrics.get('overall_implementation_rate', 0)
                },
                'gaps': {
                    'hlr_orphaned': hlr.get('orphaned', {}).get('count', 0),
                    'llr_orphaned': llr.get('orphaned', {}).get('count', 0),
                    'partially_implemented_sys': sys_reqs.get('partially_implemented', {}).get('count', 0),
                    'not_implemented_sys': sys_reqs.get('not_implemented', {}).get('count', 0),
                    'total': metrics.get('total_orphaned', 0) + sys_reqs.get('not_implemented', {}).get('count', 0)
                }
            }
        # Check if hierarchical analysis format
        elif 'system_requirements' in self.analysis and 'high_level_requirements' in self.analysis:
            # Hierarchical format
            sys_reqs = self.analysis.get('system_requirements', {})
            hlr = self.analysis.get('high_level_requirements', {})
            llr = self.analysis.get('low_level_requirements', {})
            vars_data = self.analysis.get('variables', {})
            chains = self.analysis.get('chains', {})
            quality = self.analysis.get('quality_metrics', {})
            
            return {
                'artifacts': {
                    'system_req': sys_reqs.get('total', 0),
                    'system_req_decomposed': len([a for a in self.artifacts.values() if a['type'] == 'SYSTEM_REQ_DECOMPOSED']),
                    'hlr': hlr.get('total', 0),
                    'llr': llr.get('total', 0),
                    'code_var': vars_data.get('total', 0),
                    'total': len(self.artifacts)
                },
                'links': {
                    'total': quality.get('total_links', len(self.links)),
                    'high_confidence': quality.get('high_confidence', {}).get('count', 0),
                    'medium_confidence': quality.get('medium_confidence', {}).get('count', 0),
                    'low_confidence': quality.get('low_confidence', {}).get('count', 0)
                },
                'coverage': {
                    'system_reqs_complete': sys_reqs.get('complete', {}).get('count', 0),
                    'system_reqs_partial': sys_reqs.get('partial', {}).get('count', 0),
                    'hlr_complete': hlr.get('complete', {}).get('count', 0),
                    'hlr_orphaned': hlr.get('orphaned', {}).get('count', 0),
                    # LLR can have two formats: complete/orphaned OR implemented/orphaned
                    'llr_complete': llr.get('complete', {}).get('count', 0) if 'complete' in llr else 0,
                    'llr_implemented': llr.get('implemented', {}).get('count', 0) if 'implemented' in llr else 0,
                    'llr_orphaned': llr.get('orphaned', {}).get('count', 0),
                    'llr_has_variables': 'complete' in llr,  # Flag to indicate which format
                    'complete_chains': chains.get('complete', {}).get('count', 0),
                    'partial_chains': chains.get('partial', {}).get('count', 0),
                    'broken_chains': chains.get('broken', {}).get('count', 0),
                    'total_chains': chains.get('total_chains', 0),
                    'complete_percentage': chains.get('complete', {}).get('percentage', 0)
                },
                'gaps': {
                    'hlr_orphaned': hlr.get('orphaned', {}).get('count', 0),
                    'llr_orphaned': llr.get('orphaned', {}).get('count', 0),
                    'partial_system_reqs': sys_reqs.get('partial', {}).get('count', 0),
                    'total': (hlr.get('orphaned', {}).get('count', 0) + 
                             llr.get('orphaned', {}).get('count', 0) +
                             sys_reqs.get('partial', {}).get('count', 0))
                }
            }
        else:
            # Legacy format
            return {
                'artifacts': self.analysis.get('artifact_counts', {}),
                'links': self.analysis.get('link_counts', {}),
                'coverage': self.analysis.get('coverage_metrics', {}).get('end_to_end', {}),
                'gaps': self.analysis.get('gap_summary', {})
            }
    
    def print_summary(self, summary: Dict[str, Any]) -> None:
        """Print summary to console."""
        print("\n📊 SUMMARY")
        print("-" * 80)
        
        artifacts = summary.get('artifacts', {})
        print(f"\n📦 Artifacts:")
        print(f"  System Requirements:      {artifacts.get('system_req', 0)}")
        print(f"  Decomposed Requirements:  {artifacts.get('system_req_decomposed', 0)}")
        print(f"  High-Level Requirements:  {artifacts.get('hlr', 0)}")
        print(f"  Low-Level Requirements:   {artifacts.get('llr', 0)}")
        print(f"  Code Variables:           {artifacts.get('code_var', 0)}")
        print(f"  TOTAL:                    {artifacts.get('total', 0)}")
        
        links = summary.get('links', {})
        print(f"\n🔗 Links:")
        print(f"  Total trace links:        {links.get('total', 0)}")
        if links.get('high_confidence'):
            print(f"  High confidence (≥0.6):   {links.get('high_confidence', 0)}")
            print(f"  Medium confidence:        {links.get('medium_confidence', 0)}")
            print(f"  Low confidence:           {links.get('low_confidence', 0)}")
        
        coverage = summary.get('coverage', {})
        
        # Check if unified format
        if 'system_reqs_fully_implemented' in coverage:
            print(f"\n✅ System Requirements ({artifacts.get('system_req', 0)} total):")
            print(f"  Fully Implemented:        {coverage.get('system_reqs_fully_implemented', 0)} ({coverage.get('system_reqs_fully_implemented', 0)/artifacts.get('system_req', 1)*100:.1f}%)")
            print(f"  Partially Implemented:    {coverage.get('system_reqs_partially_implemented', 0)}")
            print(f"  Not Implemented:          {coverage.get('system_reqs_not_implemented', 0)}")
            
            print(f"\n✅ High-Level Requirements ({artifacts.get('hlr', 0)} total):")
            print(f"  Fully Implemented:        {coverage.get('hlr_fully_implemented', 0)}")
            print(f"  Partially Implemented:    {coverage.get('hlr_partially_implemented', 0)}")
            print(f"  Orphaned:                 {coverage.get('hlr_orphaned', 0)}")
            
            print(f"\n✅ Low-Level Requirements ({artifacts.get('llr', 0)} total):")
            print(f"  Traced (mapped to HLR):   {coverage.get('llr_traced', 0)}")
            print(f"  Orphaned:                 {coverage.get('llr_orphaned', 0)}")
            
            print(f"\n📊 Overall Implementation Rate: {coverage.get('overall_rate', 0):.1f}%")
        # Check if hierarchical format
        elif 'complete_chains' in coverage:
            print(f"\n✅ System Requirements:")
            print(f"  Complete (traced to LLR): {coverage.get('system_reqs_complete', 0)}/{artifacts.get('system_req', 0)}")
            print(f"  Partial implementations:  {coverage.get('system_reqs_partial', 0)}")
            
            print(f"\n✅ High-Level Requirements:")
            print(f"  Complete (has parent+children): {coverage.get('hlr_complete', 0)}/{artifacts.get('hlr', 0)}")
            print(f"  Orphaned (isolated):      {coverage.get('hlr_orphaned', 0)}")
            
            print(f"\n✅ Low-Level Requirements:")
            if coverage.get('llr_has_variables'):
                # Detailed format (with variables)
                print(f"  Complete (has parent+children): {coverage.get('llr_complete', 0)}/{artifacts.get('llr', 0)}")
                print(f"  Orphaned (isolated):      {coverage.get('llr_orphaned', 0)}")
            else:
                # Simple format (no variables)
                print(f"  Implemented (has HLR parent): {coverage.get('llr_implemented', 0)}/{artifacts.get('llr', 0)}")
                print(f"  Orphaned (no parent):     {coverage.get('llr_orphaned', 0)}")
            
            print(f"\n✅ Trace Chains:")
            print(f"  Complete (SYS→VAR):       {coverage.get('complete_chains', 0)}/{coverage.get('total_chains', 0)}")
            print(f"  Partial (gaps):           {coverage.get('partial_chains', 0)}")
            print(f"  Broken (too short):       {coverage.get('broken_chains', 0)}")
            print(f"  Coverage percentage:      {coverage.get('complete_percentage', 0):.1f}%")
        else:
            # Legacy format
            print(f"\n✅ Coverage:")
            print(f"  Complete chains:          {coverage.get('complete', 0)}/{coverage.get('total_chains', 0)}")
            print(f"  Coverage percentage:      {coverage.get('complete_percentage', 0):.1f}%")
        
        gaps = summary.get('gaps', {})
        print(f"\n⚠️  Issues Found:")
        print(f"  Orphaned HLRs:            {gaps.get('hlr_orphaned', 0)}")
        print(f"  Orphaned LLRs:            {gaps.get('llr_orphaned', 0)}")
        print(f"  Partial System Reqs:      {gaps.get('partial_system_reqs', 0)}")
        print(f"  TOTAL ISSUES:             {gaps.get('total', 0)}")
        
        print(f"\n📁 Output files:")
        print(f"  Analysis:                 {self.output_dir}/analysis.json")
        print(f"  Traceability Matrix:      {self.output_dir}/traceability_matrix.csv")
        print(f"  Interactive Graph:        {self.output_dir}/trace_graph.html")
    
    def export_trace_matrix(self, filepath: str = None) -> None:
        """Export trace matrix to CSV."""
        if filepath is None:
            filepath = str(self.output_dir / "trace_matrix.csv")
        
        print(f"\n📄 Exporting trace matrix to {filepath}")
        
        if not self.graph:
            self.graph = build_trace_graph(self.artifacts, self.links)
        
        rows = [['System Req', 'Decomposed', 'HLR', 'LLR', 'Variable', 'Status', 'Gap Reason']]
        
        # Find all system requirements
        sys_reqs = [a for a in self.artifacts.values() if a['type'] == 'SYSTEM_REQ']
        
        for sys_req in sys_reqs:
            chains = trace_chain_forward(self.graph, sys_req['id'])
            
            if not chains:
                rows.append([sys_req['id'], '', '', '', '', 'INCOMPLETE', 'No decomposition'])
                continue
            
            for chain in chains:
                row = ['', '', '', '', '', 'COMPLETE', '']
                row[0] = sys_req['id']
                
                for node_id in chain[1:]:  # Skip sys_req itself
                    node = self.artifacts[node_id]
                    node_type = node['type']
                    
                    if node_type == 'SYSTEM_REQ_DECOMPOSED':
                        row[1] = node_id
                    elif node_type == 'HLR':
                        row[2] = node_id
                    elif node_type == 'LLR':
                        row[3] = node_id
                    elif node_type == 'CODE_VAR':
                        row[4] = node_id
                
                # Check if complete
                if not row[4]:  # No variable
                    row[5] = 'PARTIAL'
                    if not row[3]:
                        row[6] = 'No LLR found'
                    else:
                        row[6] = 'No variable link'
                
                rows.append(row)
        
        save_csv(rows, filepath)
        print(f"  Exported {len(rows)-1} rows")
    
    def get_trace_chain(self, artifact_id: str) -> Dict[str, Any]:
        """Get complete trace chain for an artifact."""
        if not self.graph:
            self.graph = build_trace_graph(self.artifacts, self.links)
        
        chains = trace_chain_forward(self.graph, artifact_id)
        
        return {
            'artifact_id': artifact_id,
            'chains': chains,
            'chain_count': len(chains)
        }
    
    def get_gaps(self) -> List[Dict[str, Any]]:
        """Get all gaps with explanations."""
        return self.analysis.get('gaps', [])
    
    def get_coverage(self) -> Dict[str, Any]:
        """Get coverage metrics."""
        return self.analysis.get('coverage_metrics', {})
