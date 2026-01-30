"""
Test script to verify TraceX components work correctly.
Run with: uv run python test_system.py
"""
import sys
from pathlib import Path

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from src.models import HLR, LLR, TraceabilityLink, TraceabilityMatrix
        from src.requirements_loader import RequirementsLoader
        from src.understanding_layer import RequirementUnderstandingLayer
        from src.candidate_generator import CandidateLinkGenerator
        from src.reasoning_engine import LinkReasoningEngine
        from src.matrix_generator import TraceabilityMatrixGenerator
        from src.traceability_system import TraceabilitySystem
        from src.model_provider import create_model_provider, MODEL_CONFIGS
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_sample_data():
    """Test loading sample data."""
    print("\nTesting sample data loading...")
    try:
        from src.requirements_loader import RequirementsLoader
        
        hlrs, llrs = RequirementsLoader.create_sample_requirements()
        print(f"✅ Loaded {len(hlrs)} HLRs and {len(llrs)} LLRs")
        
        # Check structure
        assert len(hlrs) > 0, "No HLRs loaded"
        assert len(llrs) > 0, "No LLRs loaded"
        assert hlrs[0].id, "HLR missing ID"
        assert hlrs[0].title, "HLR missing title"
        assert hlrs[0].description, "HLR missing description"
        
        print("✅ Sample data structure valid")
        return True
    except Exception as e:
        print(f"❌ Sample data test failed: {e}")
        return False


def test_csv_loading():
    """Test loading from CSV files."""
    print("\nTesting CSV file loading...")
    try:
        from src.requirements_loader import RequirementsLoader
        
        sample_dir = Path("sample_data")
        if not sample_dir.exists():
            print("⚠️  Sample data directory not found. Run: uv run python generate_samples.py")
            return False
        
        hlr_file = sample_dir / "sample_hlrs.csv"
        llr_file = sample_dir / "sample_llrs.csv"
        
        if not hlr_file.exists() or not llr_file.exists():
            print("⚠️  Sample CSV files not found. Run: uv run python generate_samples.py")
            return False
        
        hlrs, llrs = RequirementsLoader.load_from_csv(str(hlr_file), str(llr_file))
        print(f"✅ Loaded {len(hlrs)} HLRs and {len(llrs)} LLRs from CSV")
        return True
    except Exception as e:
        print(f"❌ CSV loading test failed: {e}")
        return False


def test_embeddings():
    """Test embedding generation."""
    print("\nTesting embedding generation...")
    try:
        from src.candidate_generator import CandidateLinkGenerator
        from src.requirements_loader import RequirementsLoader
        
        hlrs, llrs = RequirementsLoader.create_sample_requirements()
        
        print("Loading embedding model...")
        generator = CandidateLinkGenerator(top_k=5)
        
        print("Generating embeddings...")
        generator._generate_embeddings(hlrs[:2], llrs[:3])
        
        assert hlrs[0].embedding is not None, "HLR embedding not generated"
        assert llrs[0].embedding is not None, "LLR embedding not generated"
        assert len(hlrs[0].embedding) > 0, "Empty embedding"
        
        print("✅ Embeddings generated successfully")
        return True
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_providers():
    """Test model provider configuration."""
    print("\nTesting model provider configuration...")
    try:
        from src.model_provider import MODEL_CONFIGS
        
        print("Available providers:")
        for provider, config in MODEL_CONFIGS.items():
            print(f"  - {provider}: {len(config['models'])} models")
        
        print("✅ Model provider configuration valid")
        return True
    except Exception as e:
        print(f"❌ Model provider test failed: {e}")
        return False


def test_traceability_system_init():
    """Test TraceabilitySystem initialization with mock models."""
    print("\nTesting TraceabilitySystem initialization...")
    try:
        from src.traceability_system import TraceabilitySystem
        from src.requirements_loader import RequirementsLoader
        
        # We'll create a mock provider for testing without API calls
        class MockProvider:
            def generate(self, prompt, temperature=0.7, max_tokens=2000):
                return "Mock response"
            
            def generate_structured(self, prompt, response_schema):
                return {
                    "intent_verb": "maintain",
                    "subject": "system",
                    "object": "stability",
                    "constraint": None,
                    "requirement_type": "functional",
                    "abstraction_level": "system",
                    "key_concepts": ["control", "stability"]
                }
        
        mock_provider = MockProvider()
        
        system = TraceabilitySystem(
            structured_model=mock_provider,
            reasoning_model=mock_provider,
            top_k_candidates=5
        )
        
        # Load sample data
        hlrs, llrs = RequirementsLoader.create_sample_requirements()
        system.hlrs = hlrs[:2]  # Use only 2 for testing
        system.llrs = llrs[:3]  # Use only 3 for testing
        
        print("✅ TraceabilitySystem initialized successfully")
        return True
    except Exception as e:
        print(f"❌ TraceabilitySystem test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("TraceX System Tests")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_sample_data,
        test_csv_loading,
        test_model_providers,
        test_embeddings,
        test_traceability_system_init,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
        print("\nYou can now run the application:")
        print("  ./run.sh")
        print("  or")
        print("  uv run streamlit run app.py")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed")
        print("\nPlease check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
