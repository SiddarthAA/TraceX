"""Embedding generation and FAISS indexing with model caching."""

import numpy as np
import faiss
import os
import warnings
import logging
from typing import Dict, List, Tuple, Any, Optional
from sentence_transformers import SentenceTransformer
from pathlib import Path
from src.utils.file_io import save_json, load_json

# Suppress all warnings
warnings.filterwarnings('ignore')
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# Suppress transformers logging
logging.getLogger('transformers').setLevel(logging.ERROR)
logging.getLogger('sentence_transformers').setLevel(logging.ERROR)

# Global model cache
_MODEL_CACHE = {}


class EmbeddingIndexer:
    """Manages embeddings and FAISS index with model caching."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: Optional[str] = None):
        """
        Initialize embedding model with caching.
        
        Args:
            model_name: Name of the sentence-transformer model
            cache_dir: Directory to cache downloaded models (default: ./model_cache)
        """
        global _MODEL_CACHE
        
        # Set cache directory
        if cache_dir is None:
            cache_dir = str(Path.cwd() / "model_cache")
        
        os.makedirs(cache_dir, exist_ok=True)
        
        # Check if model is already loaded in memory
        if model_name in _MODEL_CACHE:
            print(f"✓ Using cached embedding model from memory")
            self.model = _MODEL_CACHE[model_name]
        else:
            # Check if model exists in cache folder (already downloaded)
            model_path = Path(cache_dir) / model_name.replace('/', '_')
            
            if model_path.exists():
                print(f"✓ Loading embedding model from cache: {cache_dir}")
            else:
                print(f"⏳ Downloading embedding model (first time only)...")
            
            # Suppress ALL output during model loading
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                old_stdout = os.dup(1)
                old_stderr = os.dup(2)
                try:
                    # Redirect stdout and stderr to devnull during load
                    devnull = os.open(os.devnull, os.O_WRONLY)
                    os.dup2(devnull, 1)
                    os.dup2(devnull, 2)
                    
                    # Load model with caching
                    self.model = SentenceTransformer(
                        model_name,
                        cache_folder=cache_dir,
                        device='cpu'  # Use 'cuda' if GPU available
                    )
                finally:
                    # Restore stdout and stderr
                    os.dup2(old_stdout, 1)
                    os.dup2(old_stderr, 2)
                    os.close(devnull)
                    os.close(old_stdout)
                    os.close(old_stderr)
            
            # Cache in memory for reuse
            _MODEL_CACHE[model_name] = self.model
            print(f"✓ Model ready ({self.model.get_sentence_embedding_dimension()}D embeddings)")
        
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.id_mapping = []
        self.embeddings = {}
        self.model_name = model_name
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for single text."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        # Normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        return embedding
    
    def generate_all_embeddings(self, artifacts: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """Generate embeddings for all artifacts."""
        print(f"⏳ Generating embeddings for {len(artifacts)} artifacts...")
        
        embeddings = {}
        texts = []
        ids = []
        
        for art_id, artifact in artifacts.items():
            # Concatenate text and keywords for better matching
            text = artifact['text']
            keywords = artifact.get('extracted', {}).get('keywords', [])
            if keywords:
                text = text + ' ' + ' '.join(keywords)
            
            texts.append(text)
            ids.append(art_id)
        
        # Batch encode for efficiency (suppress progress bar in non-interactive mode)
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            batch_embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=True,
                batch_size=32
            )
        
        # Normalize
        norms = np.linalg.norm(batch_embeddings, axis=1, keepdims=True)
        batch_embeddings = batch_embeddings / norms
        
        # Store
        for art_id, embedding in zip(ids, batch_embeddings):
            embeddings[art_id] = embedding
        
        self.embeddings = embeddings
        print(f"✓ Generated {len(embeddings)} embeddings ({self.dimension}D)")
        return embeddings
    
    def build_faiss_index(self, embeddings: Dict[str, np.ndarray] = None) -> Tuple[faiss.Index, List[str]]:
        """Build FAISS index from embeddings."""
        if embeddings is None:
            embeddings = self.embeddings
        
        print(f"Building FAISS index for {len(embeddings)} vectors...")
        
        # Create index
        index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        
        # Prepare data
        ids = list(embeddings.keys())
        vectors = np.array([embeddings[art_id] for art_id in ids]).astype('float32')
        
        # Add to index
        index.add(vectors)
        
        self.index = index
        self.id_mapping = ids
        
        print(f"Index built with {index.ntotal} vectors")
        return index, ids
    
    def search_similar(
        self,
        query_text: str = None,
        query_embedding: np.ndarray = None,
        top_k: int = 10,
        threshold: float = 0.3,
        filter_type: str = None
    ) -> List[Tuple[str, float]]:
        """
        Search for similar artifacts.
        
        Args:
            query_text: Text to search for (will be embedded)
            query_embedding: Pre-computed embedding
            top_k: Maximum results
            threshold: Minimum similarity score
            filter_type: Filter results by artifact type
        
        Returns:
            List of (artifact_id, similarity_score) tuples
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_faiss_index first.")
        
        # Get query embedding
        if query_embedding is None:
            if query_text is None:
                raise ValueError("Must provide either query_text or query_embedding")
            query_embedding = self.generate_embedding(query_text)
        
        # Ensure 2D array
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Search
        scores, indices = self.index.search(
            query_embedding.astype('float32'),
            min(top_k * 2, self.index.ntotal)  # Get extra for filtering
        )
        
        # Collect results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.id_mapping):
                continue
            
            artifact_id = self.id_mapping[idx]
            
            # Apply threshold
            if score < threshold:
                continue
            
            results.append((artifact_id, float(score)))
        
        return results[:top_k]
    
    def save_index(self, filepath: str) -> None:
        """Save FAISS index and ID mapping to disk."""
        if self.index is None:
            raise ValueError("No index to save")
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{filepath}.index")
        
        # Save ID mapping
        save_json({'id_mapping': self.id_mapping}, f"{filepath}.ids.json")
        
        print(f"Index saved to {filepath}")
    
    def load_index(self, filepath: str) -> None:
        """Load FAISS index and ID mapping from disk."""
        # Load FAISS index
        self.index = faiss.read_index(f"{filepath}.index")
        
        # Load ID mapping
        data = load_json(f"{filepath}.ids.json")
        self.id_mapping = data['id_mapping']
        
        print(f"Index loaded from {filepath} ({self.index.ntotal} vectors)")
    
    def get_embedding(self, artifact_id: str) -> np.ndarray:
        """Get embedding for specific artifact."""
        return self.embeddings.get(artifact_id)
