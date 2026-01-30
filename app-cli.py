#!/usr/bin/env python3
"""
TraceX Command Line Interface
Main entry point for running traceability analysis.
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.model_provider import create_model_provider, MODEL_CONFIGS
from src.traceability_system import TraceabilitySystem
from src.requirements_loader import RequirementsLoader


def print_banner():
    """Print TraceX banner."""
    print("=" * 70)
    print("🔗 TraceX - HLR-LLR Requirements Traceability System")
    print("   AI-Powered Requirements Mapping with Explainable Reasoning")
    print("=" * 70)
    print()


def load_requirements(args):
    """Load requirements based on input source."""
    print("📥 Loading requirements...")
    
    if args.sample:
        print("   Using built-in sample data")
        hlrs, llrs = RequirementsLoader.create_sample_requirements()
    elif args.excel:
        print(f"   Loading from Excel: {args.excel}")
        hlrs, llrs = RequirementsLoader.load_from_excel(
            args.excel,
            args.hlr_sheet,
            args.llr_sheet
        )
    elif args.hlr_csv and args.llr_csv:
        print(f"   Loading HLRs from: {args.hlr_csv}")
        print(f"   Loading LLRs from: {args.llr_csv}")
        hlrs, llrs = RequirementsLoader.load_from_csv(args.hlr_csv, args.llr_csv)
    else:
        print("❌ Error: No input source specified")
        print("   Use --sample, --excel, or --hlr-csv/--llr-csv")
        sys.exit(1)
    
    print(f"✅ Loaded {len(hlrs)} HLRs and {len(llrs)} LLRs\n")
    return hlrs, llrs


def create_models(args):
    """Create model providers."""
    print("🤖 Initializing AI models...")
    print(f"   Structured Model: {args.struct_provider}/{args.struct_model}")
    print(f"   Reasoning Model: {args.reason_provider}/{args.reason_model}")
    
    try:
        structured_model = create_model_provider(
            args.struct_provider,
            args.struct_model
        )
        reasoning_model = create_model_provider(
            args.reason_provider,
            args.reason_model
        )
        print("✅ Models initialized\n")
        return structured_model, reasoning_model
    except Exception as e:
        print(f"❌ Error initializing models: {e}")
        print("\nTroubleshooting:")
        print("  - Check your API keys in .env file")
        print("  - For Ollama, ensure it's running: ollama serve")
        print("  - Verify model names are correct")
        sys.exit(1)


def run_traceability(args):
    """Run complete traceability analysis."""
    print_banner()
    
    # Load requirements
    hlrs, llrs = load_requirements(args)
    
    # Create models
    structured_model, reasoning_model = create_models(args)
    
    # Initialize system
    print("🔧 Initializing traceability system...")
    system = TraceabilitySystem(
        structured_model=structured_model,
        reasoning_model=reasoning_model,
        top_k_candidates=args.top_k
    )
    system.hlrs = hlrs
    system.llrs = llrs
    print("✅ System ready\n")
    
    # Step 1: Understand requirements
    print("=" * 70)
    print("Step 1/3: Understanding Requirements")
    print("=" * 70)
    system.understand_requirements()
    print("✅ Semantic understanding complete\n")
    
    # Step 2: Generate traceability
    print("=" * 70)
    print("Step 2/3: Generating Traceability Links")
    print("=" * 70)
    matrix = system.generate_traceability()
    
    # Step 3: Save results
    print("\n" + "=" * 70)
    print("Step 3/3: Saving Results")
    print("=" * 70)
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"traceability_matrix_{timestamp}.xlsx"
    
    print(f"💾 Saving to: {output_file}")
    system.export_results(str(output_file))
    print("✅ Export complete\n")
    
    # Print summary
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total HLRs:           {matrix.hlr_count}")
    print(f"Total LLRs:           {matrix.llr_count}")
    print(f"Traceability Links:   {matrix.link_count}")
    print(f"Coverage:             {matrix.gap_report.coverage_percentage:.1f}%")
    print(f"Orphan HLRs:          {len(matrix.gap_report.orphan_hlrs)}")
    print(f"Orphan LLRs:          {len(matrix.gap_report.orphan_llrs)}")
    print(f"Partial Coverage:     {len(matrix.gap_report.partial_coverage_hlrs)}")
    print()
    
    if matrix.gap_report.orphan_hlrs:
        print("⚠️  WARNING: Orphan HLRs detected (not implemented):")
        for hlr_id in matrix.gap_report.orphan_hlrs:
            print(f"   - {hlr_id}")
        print()
    
    print(f"✅ Results saved to: {output_file}")
    print("=" * 70)
    print()
    
    return 0


def list_models(args):
    """List available models for each provider."""
    print_banner()
    print("Available Models:\n")
    
    for provider, config in MODEL_CONFIGS.items():
        print(f"📦 {provider.upper()}")
        print(f"   Best for Structured: {config['best_for_structured']}")
        print(f"   Best for Reasoning:  {config['best_for_reasoning']}")
        print(f"   Available models:")
        for model in config['models']:
            print(f"      - {model}")
        print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TraceX - HLR-LLR Requirements Traceability System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use sample data with Gemini
  tracex run --sample --struct-provider gemini --reason-provider gemini
  
  # Load from Excel with Claude for reasoning
  tracex run --excel data/input/requirements.xlsx \\
             --struct-provider gemini --struct-model gemini-2.0-flash-exp \\
             --reason-provider claude --reason-model claude-3-5-sonnet-20241022
  
  # Load from CSV files with local Ollama
  tracex run --hlr-csv data/input/hlrs.csv --llr-csv data/input/llrs.csv \\
             --struct-provider ollama --reason-provider ollama
  
  # List available models
  tracex list-models
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run traceability analysis')
    
    # Input sources (mutually exclusive group)
    input_group = run_parser.add_argument_group('input sources (choose one)')
    input_group.add_argument('--sample', action='store_true',
                            help='Use built-in sample data')
    input_group.add_argument('--excel', type=str,
                            help='Load from Excel file')
    input_group.add_argument('--hlr-csv', type=str,
                            help='HLR CSV file')
    input_group.add_argument('--llr-csv', type=str,
                            help='LLR CSV file (use with --hlr-csv)')
    
    # Excel options
    excel_group = run_parser.add_argument_group('excel options')
    excel_group.add_argument('--hlr-sheet', type=str, default='HLRs',
                            help='HLR sheet name (default: HLRs)')
    excel_group.add_argument('--llr-sheet', type=str, default='LLRs',
                            help='LLR sheet name (default: LLRs)')
    
    # Model configuration
    model_group = run_parser.add_argument_group('model configuration')
    model_group.add_argument('--struct-provider', type=str, default='gemini',
                            choices=['gemini', 'claude', 'gpt', 'groq', 'ollama'],
                            help='Provider for structured extraction (default: gemini)')
    model_group.add_argument('--struct-model', type=str,
                            help='Specific model for structured extraction')
    model_group.add_argument('--reason-provider', type=str, default='gemini',
                            choices=['gemini', 'claude', 'gpt', 'groq', 'ollama'],
                            help='Provider for reasoning (default: gemini)')
    model_group.add_argument('--reason-model', type=str,
                            help='Specific model for reasoning')
    
    # Advanced options
    advanced_group = run_parser.add_argument_group('advanced options')
    advanced_group.add_argument('--top-k', type=int, default=10,
                               help='Number of candidate links per HLR (default: 10)')
    advanced_group.add_argument('--output', type=str, default='data/output',
                               help='Output directory (default: data/output)')
    
    # List models command
    list_parser = subparsers.add_parser('list-models', help='List available models')
    
    args = parser.parse_args()
    
    # Set default models if not specified
    if hasattr(args, 'struct_model') and not args.struct_model:
        args.struct_model = MODEL_CONFIGS[args.struct_provider]['best_for_structured']
    if hasattr(args, 'reason_model') and not args.reason_model:
        args.reason_model = MODEL_CONFIGS[args.reason_provider]['best_for_reasoning']
    
    # Execute command
    if args.command == 'run':
        return run_traceability(args)
    elif args.command == 'list-models':
        return list_models(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
