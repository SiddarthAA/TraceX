"""
Candidate Link Generator - uses embeddings and BM25 to generate candidate links.
"""
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from src.models import HLR, LLR, CandidateLink


class CandidateLinkGenerator:
    """Generate candidate links using multiple retrieval methods."""
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2", top_k: int = 10):
        self.embedding_model = SentenceTransformer(embedding_model)
        self.top_k = top_k
        self.bm25_index = None
        self.llr_docs = []
    
    def generate_candidates(self, hlrs: List[HLR], llrs: List[LLR]) -> Dict[str, List[CandidateLink]]:
        """Generate candidate links for all HLRs."""
        
        # Generate embeddings for all requirements
        print("Generating embeddings...")
        self._generate_embeddings(hlrs, llrs)
        
        # Build BM25 index for LLRs
        print("Building BM25 index...")
        self._build_bm25_index(llrs)
        
        # Generate candidates for each HLR
        candidates_map = {}
        for hlr in hlrs:
            candidates = self._generate_candidates_for_hlr(hlr, llrs)
            candidates_map[hlr.id] = candidates
        
        return candidates_map
    
    def _generate_embeddings(self, hlrs: List[HLR], llrs: List[LLR]):
        """Generate embeddings for all requirements."""
        # HLRs
        hlr_texts = [f"{req.title}. {req.description}" for req in hlrs]
        hlr_embeddings = self.embedding_model.encode(hlr_texts, show_progress_bar=True)
        for i, hlr in enumerate(hlrs):
            hlr.embedding = hlr_embeddings[i].tolist()
        
        # LLRs
        llr_texts = [f"{req.title}. {req.description}" for req in llrs]
        llr_embeddings = self.embedding_model.encode(llr_texts, show_progress_bar=True)
        for i, llr in enumerate(llrs):
            llr.embedding = llr_embeddings[i].tolist()
    
    def _build_bm25_index(self, llrs: List[LLR]):
        """Build BM25 index for LLRs."""
        self.llr_docs = []
        for llr in llrs:
            doc = f"{llr.title} {llr.description}".lower()
            tokens = doc.split()
            self.llr_docs.append(tokens)
        
        self.bm25_index = BM25Okapi(self.llr_docs)
    
    def _generate_candidates_for_hlr(self, hlr: HLR, llrs: List[LLR]) -> List[CandidateLink]:
        """Generate candidate links for a single HLR."""
        candidates = []
        
        # 1. Semantic similarity (embeddings)
        hlr_emb = np.array(hlr.embedding)
        llr_embs = np.array([llr.embedding for llr in llrs])
        
        # Cosine similarity
        similarities = np.dot(llr_embs, hlr_emb) / (
            np.linalg.norm(llr_embs, axis=1) * np.linalg.norm(hlr_emb)
        )
        
        # 2. BM25 scores
        hlr_query = f"{hlr.title} {hlr.description}".lower().split()
        bm25_scores = self.bm25_index.get_scores(hlr_query)
        
        # 3. Ontology/tag overlap (simple keyword matching for now)
        hlr_keywords = set(hlr.title.lower().split() + hlr.description.lower().split())
        
        # Create candidate links
        for i, llr in enumerate(llrs):
            llr_keywords = set(llr.title.lower().split() + llr.description.lower().split())
            overlap = list(hlr_keywords & llr_keywords)
            
            # Combined score (weighted average)
            embedding_score = float(similarities[i])
            bm25_score = float(bm25_scores[i])
            
            # Normalize BM25 score (simple min-max scaling)
            bm25_normalized = bm25_score / (max(bm25_scores) + 1e-6)
            
            # Weighted combination
            combined_score = 0.6 * embedding_score + 0.4 * bm25_normalized
            
            candidate = CandidateLink(
                hlr_id=hlr.id,
                llr_id=llr.id,
                embedding_score=embedding_score,
                bm25_score=bm25_score,
                ontology_overlap=overlap[:5],  # Top 5 overlapping terms
                combined_score=combined_score
            )
            candidates.append(candidate)
        
        # Sort by combined score and return top-K
        candidates.sort(key=lambda x: x.combined_score, reverse=True)
        return candidates[:self.top_k]
