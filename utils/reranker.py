# utils/reranker.py
import os
import onnxruntime as ort
from transformers import AutoTokenizer
import numpy as np
from functools import lru_cache
from typing import List, Dict

# --- CROSS-ENCODER MODEL (Accurate Reranking) ---
MODEL_DIR = os.environ.get("CROSS_ENCODER_MODEL_PATH", "./models/cross-encoder-ms-marco-MiniLM-L-6-v2/")
MODEL_FILE = os.path.join(MODEL_DIR, "model_qint8_avx512_vnni.onnx")

@lru_cache(maxsize=1)
def get_cross_encoder_tokenizer():
    return AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)

@lru_cache(maxsize=1)
def get_cross_encoder_session():
    return ort.InferenceSession(MODEL_FILE, providers=["CPUExecutionProvider"])

def cross_encode_similarity(query: str, text: str) -> float:
    """Calculates a relevance score for a (query, text) pair using the Cross-Encoder."""
    tokenizer = get_cross_encoder_tokenizer()
    session = get_cross_encoder_session()

    inputs = tokenizer(query, text, return_tensors="np", padding=True, truncation=True, max_length=512)
    
    # ONNX model might not need token_type_ids
    expected_inputs = {i.name for i in session.get_inputs()}
    ort_inputs = {k: v.astype(np.int64) for k, v in inputs.items() if k in expected_inputs}

    outputs = session.run(None, ort_inputs)
    return float(outputs[0][0])

def rerank_with_cross_encoder(
    query: str,
    section_infos: List[Dict],
    top_k: int = 5,
    max_per_doc: int = 2
) -> List[Dict]:
    """Reranks a list of sections using the cross-encoder and returns the top_k."""
    scored_infos = []
    for info in section_infos:
        score = cross_encode_similarity(query, info["text"])
        scored_infos.append({"score": score, "info": info})
    
    # Sort by the new cross-encoder score
    ranked_infos = sorted(scored_infos, key=lambda x: x["score"], reverse=True)

    # Apply diversity and select top_k
    results = []
    doc_counts = {}
    rank = 1
    for item in ranked_infos:
        doc = item["info"]["document"]
        if doc_counts.get(doc, 0) < max_per_doc:
            info_out = item["info"].copy()
            info_out["score"] = item["score"]
            info_out["rank"] = rank
            results.append(info_out)
            doc_counts[doc] = doc_counts.get(doc, 0) + 1
            rank += 1
            if len(results) >= top_k:
                break
    return results