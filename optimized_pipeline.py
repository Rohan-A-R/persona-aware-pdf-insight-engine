import os
import json
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import numpy as np
import re

from pdf_parser import extract_sections_from_pdf
from utils.embeddings import embed_text
from utils.similarity import rank_sections_by_similarity
from utils.reranker import rerank_with_cross_encoder

def find_most_relevant_sentences(chunk_text: str, query_embedding: np.ndarray, top_n: int = 1) -> List[str]:
    """Finds the most relevant sentence(s) in a chunk to act as a title or summary."""
    sentences = re.split(r'(?<=[.!?]) +', chunk_text)
    if not sentences: return ["No relevant sentences found."]
    
    valid_sentences = [s.strip() for s in sentences if len(s.split()) > 3]
    if not valid_sentences: return [chunk_text[:100]] # Fallback

    embeddings = [embed_text(s) for s in valid_sentences]
    if not embeddings: return [chunk_text[:100]] # Fallback
    
    # Use dot product for similarity with normalized embeddings
    sims = np.dot(np.array(embeddings), query_embedding)
    top_indices = np.argsort(sims)[-top_n:][::-1]
    
    return [valid_sentences[i] for i in top_indices]

def process_documents(
    pdf_paths: List[str],  # <- CHANGED: previously was pdf_dir
    persona: str, 
    task: str, 
    output_file: str,
    top_k: int = 5, 
    max_per_doc: int = 2
) -> Dict:
    start_time = time.time()
    
    if not pdf_paths:
        print("❌ No PDF files provided.")
        return {}

    print(f"Found {len(pdf_paths)} PDF files to process.")

    # --- Step 1: Chunk Extraction (now with cleaning) ---
    all_chunks = []
    with ThreadPoolExecutor() as executor:
        future_to_pdf = {
            executor.submit(extract_sections_from_pdf, str(pdf_path)): pdf_path
            for pdf_path in pdf_paths
        }
        for future in as_completed(future_to_pdf):
            try:
                chunks = future.result()
                for chunk in chunks:
                    chunk['document'] = Path(future_to_pdf[future]).name
                    all_chunks.append(chunk)
            except Exception as e:
                print(f"❌ Error extracting {future_to_pdf[future]}: {e}")
    print(f"✅ Extracted {len(all_chunks)} cleaned chunks.")

    persona_query = f"{persona}: {task}"

    # --- Step 2: Stage 1 - Fast Retrieval with Bi-Encoder ---
    print("🔍 Stage 1: Retrieving candidates...")
    query_embedding = embed_text(persona_query)
    chunk_embeddings = [embed_text(chunk['text']) for chunk in all_chunks]

    section_infos = [
        {"document": c["document"], "page_number": c["page_number"], "chunk_id": c["chunk_id"], "text": c["text"]}
        for c in all_chunks
    ]

    candidate_sections = rank_sections_by_similarity(
        query_embedding, chunk_embeddings, section_infos, top_k=50
    )
    print(f"✅ Retrieved {len(candidate_sections)} candidates for reranking.")

    # --- Step 3: Stage 2 - Accurate Reranking with Cross-Encoder ---
    print("⚖️ Stage 2: Reranking candidates...")
    ranked_sections = rerank_with_cross_encoder(
        query=persona_query,
        section_infos=candidate_sections,
        top_k=top_k,
        max_per_doc=max_per_doc
    )

    # --- Step 4: Subsection Analysis and Smart Title Generation ---
    subsection_analysis = []
    final_sections = []
    for section in ranked_sections:
        relevant_sentences = find_most_relevant_sentences(
            section["text"], query_embedding, top_n=3
        )
        section_title = relevant_sentences[0] if relevant_sentences else section["text"][:100]

        for sent in relevant_sentences[:2]:
            subsection_analysis.append({
                "document": section["document"],
                "page_number": section["page_number"],
                "refined_text": sent
            })

        final_sections.append({
            "document": section["document"],
            "section_title": section_title,
            "importance_rank": section["rank"],
            "page_number": section["page_number"]
        })

    # --- Final Output ---
    output = {
        "metadata": {
            "input_documents": [Path(p).name for p in pdf_paths],
            "persona": persona,
            "job_to_be_done": task,
            "processing_timestamp": datetime.now().isoformat()
        },
        "extracted_sections": final_sections,
        "subsection_analysis": subsection_analysis
    }

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"🎯 Pipeline completed in {round(time.time() - start_time, 2)} seconds.")
    print(f"📄 Output saved to: {output_file}")
    return output
