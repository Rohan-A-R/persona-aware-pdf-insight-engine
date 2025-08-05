import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict

def rank_sections_by_similarity(
    query_embedding: np.ndarray,
    section_embeddings: List[np.ndarray],
    section_infos: List[Dict],
    top_k: int = 50
) -> List[Dict]:
    """
    Ranks sections purely by cosine similarity to get initial candidates for the reranker.
    """
    # Ensure there are embeddings to process
    if not section_embeddings or not any(e is not None for e in section_embeddings):
        return []
    
    # Filter out any None embeddings before calculating similarity
    valid_embeddings = [e for e in section_embeddings if e is not None]
    valid_infos = [info for i, info in enumerate(section_infos) if section_embeddings[i] is not None]

    if not valid_embeddings:
        return []

    # Compute cosine similarity
    sims = cosine_similarity([query_embedding], valid_embeddings)[0]
    
    # Pair scores with their corresponding info and sort
    ranked = sorted(zip(sims, valid_infos), key=lambda x: x[0], reverse=True)
    
    # Return the top_k candidates for the next stage
    return [info for score, info in ranked[:top_k]]