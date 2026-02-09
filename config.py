"""Configuration management for traceability engine."""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Load .env file from current directory
load_dotenv()


@dataclass
class GroqConfig:
    """Configuration for Groq LLM."""
    api_key: str
    model: str = "openai/gpt-oss-120b"
    temperature: float = 0.1
    max_tokens: int = 2000


@dataclass
class EmbeddingConfig:
    """Configuration for embedding model."""
    model_name: str = "all-MiniLM-L6-v2"
    normalize: bool = True


@dataclass
class LinkingConfig:
    """Configuration for linking algorithm with quality controls."""
    
    # Base thresholds - more lenient to catch more genuine links
    embedding_threshold: float = 0.10  # Lower to allow more candidates
    confidence_threshold: float = 0.25  # Lower baseline - quality filters validate
    top_k_candidates: int = 20  # Consider more candidates
    
    # Scoring weights - balanced approach emphasizing multiple signals
    weights: dict = field(default_factory=lambda: {
        'embedding': 0.35,   # Semantic similarity - reduced, not sole decision maker
        'keyword': 0.35,     # Keyword overlap - increased, strong indicator
        'quantity': 0.15,    # Numerical values
        'name': 0.15         # Variable names
    })
    
    # Hierarchical linking - more lenient thresholds to improve coverage
    layer_thresholds: dict = field(default_factory=lambda: {
        'SYSTEM_REQ_DECOMPOSED->HLR': 0.28,  # Lower - catch more HLR links
        'HLR->LLR': 0.25,                     # Lower - catch more LLR links
        'LLR->CODE_VAR': 0.23                 # Lower - catch more variable links
    })
    
    # Quality filters - balanced validation (catch genuine links, prevent noise)
    quality_filters: dict = field(default_factory=lambda: {
        'min_text_overlap': 0.05,        # Lower baseline (was 0.08)
        'min_combined_signals': 2,        # Still require 2 signals for corroboration
        'require_id_or_keyword': False,   # Real-world compatible
        'max_links_per_source': 15,       # Allow more links (was 10)
    })
    
    # Confidence bands - for reporting
    confidence_bands: dict = field(default_factory=lambda: {
        'high': 0.60,      # Lowered (was 0.65)
        'medium': 0.40,    # Lowered (was 0.45)
        'low': 0.25        # Lowered (was 0.30)
    })


@dataclass
class Config:
    """Main configuration."""
    data_dir: str = "./data"
    groq: Optional[GroqConfig] = None
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    linking: LinkingConfig = field(default_factory=LinkingConfig)
    
    @classmethod
    def from_env(cls):
        """Create config from environment variables."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        return cls(
            groq=GroqConfig(api_key=api_key),
            embedding=EmbeddingConfig(),
            linking=LinkingConfig()
        )
