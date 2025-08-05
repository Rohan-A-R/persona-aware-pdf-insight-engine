import os
import numpy as np
import onnxruntime
from transformers import AutoTokenizer
from functools import lru_cache

# Define model paths
MODEL_DIR = os.environ.get("MINILM_MODEL_PATH", "./models/all-MiniLM-L6-v2/")
MODEL_FILE = os.path.join(MODEL_DIR, "model_qint8_avx512_vnni.onnx")

@lru_cache(maxsize=1)
def get_tokenizer():
    return AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)


@lru_cache(maxsize=1)
def get_onnx_session():
    return onnxruntime.InferenceSession(MODEL_FILE, providers=["CPUExecutionProvider"])

def mean_pooling(model_output, attention_mask):
    """Helper function for pooling ONNX model output."""
    token_embeddings = model_output[0]
    input_mask_expanded = np.expand_dims(attention_mask, axis=-1).astype(float)
    sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
    sum_mask = np.maximum(np.sum(input_mask_expanded, axis=1), 1e-9)
    return sum_embeddings / sum_mask

def embed_text(text: str) -> np.ndarray:
    tokenizer = get_tokenizer()
    session = get_onnx_session()

    encoded = tokenizer(
        [text],
        return_tensors="np",
        padding=True,
        truncation=True
    )
    
    if "token_type_ids" not in encoded:
        encoded["token_type_ids"] = np.zeros_like(encoded["input_ids"])

    # --- FIX: Convert all inputs to int64 ---
    input_feed = {
        "input_ids": encoded["input_ids"].astype(np.int64),
        "attention_mask": encoded["attention_mask"].astype(np.int64),
        "token_type_ids": encoded["token_type_ids"].astype(np.int64)
    }

    outputs = session.run(None, input_feed)
    
    pooled_embedding = mean_pooling(outputs, encoded["attention_mask"])
    norm = np.linalg.norm(pooled_embedding, axis=1, keepdims=True)
    normalized_embedding = pooled_embedding / np.maximum(norm, 1e-9)
    
    return normalized_embedding[0]

if __name__ == "__main__":
    import sys
    text = sys.argv[1] if len(sys.argv) > 1 else "Test embedding with ONNX"
    embedding = embed_text(text)
    print(embedding)
    print("Shape:", embedding.shape)