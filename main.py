#!/usr/bin/env python3
"""
Aerospace Requirements Traceability Engine

Main entry point for running traceability analysis.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

from config import Config
from src.pipeline.orchestrator import TraceabilityPipeline


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Aerospace Requirements Traceability Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline with default paths
  python main.py --full
  
  # Run with custom requirement paths
  python main.py --full --sys-reqs path/to/System-Level-Requirements.csv --hlr path/to/High-Level-Requirements.csv --llr path/to/Low-Level-Requirements.csv --vars path/to/Variables.csv
  
  # Run with custom input directory (looks for CSV files inside)
  python main.py --full --input-dir path/to/requirements/
  
  # Run specific stage
  python main.py --stage decompose
  
  # Show trace chain for artifact
  python main.py --trace SYS-001
        """
    )
    
    # Input files
    parser.add_argument(
        "--input-dir", type=str,
        help="Input directory containing CSV files (auto-detects System-Level-Requirements.csv, High-Level-Requirements.csv, Low-Level-Requirements.csv, Variables.csv)"
    )
    parser.add_argument(
        "--sys-reqs", type=str,
        help="System requirements CSV file (default: <input-dir>/System-Level-Requirements.csv)"
    )
    parser.add_argument(
        "--hlr", type=str,
        help="High-level requirements CSV file (default: <input-dir>/High-Level-Reqs.csv)"
    )
    parser.add_argument(
        "--llr", type=str,
        help="Low-level requirements CSV file (default: <input-dir>/Low-Level-Reqs.csv)"
    )
    parser.add_argument(
        "--vars", type=str,
        help="Variables CSV file (default: <input-dir>/Variables.csv)"
    )
    
    # Output control
    parser.add_argument(
        "--data-dir", type=str, default="./data",
        help="Base data directory (default: ./data). Run outputs go to data/run_<timestamp>/"
    )
    parser.add_argument(
        "--output-name", type=str,
        help="Custom output folder name (default: run_<timestamp>)"
    )
    
    # Pipeline control
    parser.add_argument(
        "--full", action="store_true",
        help="Run full pipeline (load, decompose, index, link, analyze)"
    )
    parser.add_argument(
        "--stage", type=str,
        choices=["load", "decompose", "index", "link", "analyze"],
        help="Run specific pipeline stage"
    )
    parser.add_argument(
        "--no-llm", action="store_true",
        help="Skip LLM-based reasoning (faster, less detailed)"
    )
    parser.add_argument(
        "--hierarchical", action="store_true", default=True,
        help="Use hierarchical layer-by-layer linking with LLM reasoning (default: True)"
    )
    parser.add_argument(
        "--legacy-linking", action="store_true",
        help="Use legacy all-at-once linking (disables hierarchical mode)"
    )
    
    # Output options
    parser.add_argument(
        "--export-matrix", action="store_true",
        help="Export trace matrix to CSV"
    )
    
    # Query options
    parser.add_argument(
        "--trace", type=str,
        help="Show trace chain for specific artifact ID"
    )
    parser.add_argument(
        "--gaps", action="store_true",
        help="Show all gaps with reasoning"
    )
    parser.add_argument(
        "--coverage", action="store_true",
        help="Show coverage metrics"
    )
    
    args = parser.parse_args()
    
    # Determine input directory
    if args.input_dir:
        input_dir = Path(args.input_dir)
        if not input_dir.exists():
            print(f"❌ Input directory does not exist: {input_dir}")
            sys.exit(1)
    else:
        input_dir = Path("reqs/With_Gaps")
    
    # Resolve file paths (use explicit args or auto-detect in input_dir)
    sys_reqs_file = args.sys_reqs or str(input_dir / "System-Level-Requirements.csv")
    hlr_file = args.hlr or str(input_dir / "High-Level-Requirements.csv")
    llr_file = args.llr or str(input_dir / "Low-Level-Requirements.csv")
    vars_file = args.vars or str(input_dir / "Variables.csv")
    
    # Verify required input files exist
    required_files = [
        (sys_reqs_file, "System-Level-Requirements"),
        (hlr_file, "High-Level-Requirements"),
        (llr_file, "Low-Level-Requirements")
    ]
    
    for filepath, name in required_files:
        if not Path(filepath).exists():
            print(f"❌ {name} file not found: {filepath}")
            sys.exit(1)
    
    # Check if variables file exists (optional)
    has_variables = Path(vars_file).exists()
    
    # Create timestamped output directory
    base_data_dir = Path(args.data_dir)
    if args.output_name:
        run_dir = base_data_dir / args.output_name
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = base_data_dir / f"run_{timestamp}"
    
    run_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Input directory: {input_dir}")
    print(f"📁 Output directory: {run_dir}")
    print(f"\n📄 Input files:")
    print(f"   System Reqs: {sys_reqs_file}")
    print(f"   HLR:         {hlr_file}")
    print(f"   LLR:         {llr_file}")
    if has_variables:
        print(f"   Variables:   {vars_file}")
    else:
        print(f"   Variables:   (not provided)")

    
    # Load configuration
    try:
        config = Config.from_env()
        config.data_dir = str(run_dir)
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        print("\nPlease set GROQ_API_KEY environment variable:")
        print("  export GROQ_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    # Initialize pipeline
    pipeline = TraceabilityPipeline(config)
    
    # Determine linking mode
    use_hierarchical = not args.legacy_linking
    
    # Run pipeline based on arguments
    try:
        if args.full:
            # Run full pipeline
            pipeline.run_full_pipeline(
                sys_reqs_file,
                hlr_file,
                llr_file,
                vars_file if has_variables else None,
                use_llm_reasoning=not args.no_llm,
                use_hierarchical=use_hierarchical
            )
            
            # Export matrix if requested
            if args.export_matrix:
                pipeline.export_trace_matrix()
        
        elif args.stage:
            # Run specific stage
            if args.stage == "load":
                pipeline.load_data(sys_reqs_file, hlr_file, llr_file, vars_file)
            elif args.stage == "decompose":
                pipeline.run_decomposition()
            elif args.stage == "index":
                pipeline.build_index()
            elif args.stage == "link":
                pipeline.establish_links()
            elif args.stage == "analyze":
                pipeline.analyze(use_llm_reasoning=not args.no_llm)
        
        # Handle query operations
        elif args.trace:
            chain_info = pipeline.get_trace_chain(args.trace)
            print(f"\n🔍 Trace chains for {args.trace}:")
            for i, chain in enumerate(chain_info['chains'], 1):
                print(f"\n  Chain {i}: {' -> '.join(chain)}")
        
        elif args.gaps:
            gaps = pipeline.get_gaps()
            print(f"\n⚠️  Found {len(gaps)} gaps:\n")
            for gap in gaps:
                print(f"[{gap['gap_id']}] {gap['severity'].upper()}: {gap['description']}")
                if gap.get('reasoning'):
                    print(f"  Reasoning: {gap['reasoning'][:200]}...")
                print()
        
        elif args.coverage:
            coverage = pipeline.get_coverage()
            print("\n📊 Coverage Metrics:\n")
            for level, metrics in coverage.items():
                print(f"{level}:")
                for key, value in metrics.items():
                    print(f"  {key}: {value}")
                print()
        
        elif args.export_matrix:
            pipeline.export_trace_matrix()
        
        else:
            parser.print_help()
            print("\n💡 Tip: Use --full to run complete analysis")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

