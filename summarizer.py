import os
import re
import numpy as np
import logging
from pathlib import Path
from collections import Counter

import onnxruntime as ort
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer

# ONNX model path (from environment variable or default)
MODEL_PATH = os.environ.get("MINILM_MODEL_PATH", "./models/all-MiniLM-L6-v2/model_qint8_avx512_vnni.onnx")
TOKENIZER_PATH = os.path.dirname(MODEL_PATH)

# Load tokenizer & ONNX session
tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_PATH)
session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])

def embed_onnx(text):
    tokens = tokenizer(text, return_tensors="np", padding=True, truncation=True, max_length=512)

    # Add token_type_ids if missing (some models/tokenizers don’t return it)
    if "token_type_ids" not in tokens:
        tokens["token_type_ids"] = np.zeros_like(tokens["input_ids"])

    # Get only the inputs that ONNX model expects
    required_inputs = [i.name for i in session.get_inputs()]
    inputs_onnx = {k: tokens[k] for k in required_inputs if k in tokens}

    outputs = session.run(None, inputs_onnx)[0]
    norm = np.linalg.norm(outputs, axis=1, keepdims=True)
    return (outputs / norm)[0]




def filter_junk_lines(text):
    lines = text.split('\n')
    filtered = []
    junk_patterns = [
        r'copyright', r'feedbooks', r'gutenberg', r'source:', r'brought to you by',
        r'free ebooks? at', r'planet ebook', r'project gutenberg', r'all rights reserved',
        r'public domain', r'similar users also downloaded', r'download', r'license',
        r'www\.', r'https?://', r'\.(com|org|net|info|gov|edu)', r'ebook',
        r'\bchapter\b', r'\bcontents\b', r'\bindex\b', r'\btable of contents\b',
        r'\bpage \d+\b', r'\bthe end\b', r'\babout the author\b', r'\bbiography\b',
        r'\bpublication\b', r'\bpublisher\b', r'\bprinted in', r'\bfirst published',
        r'\bthis book is brought to you by', r'\bfor more free ebooks', r'\bvisit',
        r'\bcontact us\b', r'\bdisclaimer\b', r'\btranscriber\b', r'\bfootnote\b',
        r'\bnotes?\b', r'\bintroduction\b', r'\bforeword\b', r'\bappendix\b',
        r'\bprologue\b', r'\bepilogue\b', r'\bbook [ivxlc]+\b', r'\bpart [ivxlc]+\b'
    ]
    junk_re = re.compile('|'.join(junk_patterns), re.IGNORECASE)
    for line in lines:
        l = line.strip()
        if not l or junk_re.search(l):
            continue
        if len(l.split()) < 5 and l.isupper():
            continue
        filtered.append(l)
    return '\n'.join(dict.fromkeys(filtered))

def clean_text(text):
    return filter_junk_lines(text)

def summarize(text, max_sentences=3):
    sentences = re.split(r'(?<=[.!?]) +', text)
    return ' '.join(sentences[:max_sentences]).strip()

def extract_content_paragraphs(text, top_k=2, min_length=30):
    paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) >= min_length]
    paragraphs = list(dict.fromkeys(paragraphs))
    paragraphs = sorted(paragraphs, key=len, reverse=True)
    if not paragraphs:
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    return paragraphs[:top_k] if paragraphs else []

def textrank_summary(text, top_n=3):
    text = re.sub(r'\s+', ' ', text)
    sentences = re.split(r'(?<=[.!?]) +', text)
    sentences = [s.strip() for s in sentences if len(s.strip().split()) > 6]
    if not sentences:
        return ""
    scores = []
    for i, s1 in enumerate(sentences):
        score = 0
        words1 = set(s1.lower().split())
        for j, s2 in enumerate(sentences):
            if i == j:
                continue
            words2 = set(s2.lower().split())
            score += len(words1 & words2)
        scores.append((score, i, s1))
    top = sorted(scores, reverse=True)[:top_n]
    top_indices = sorted([i for _, i, _ in top])
    return ' '.join([sentences[i] for i in top_indices])

def clean_title(title, content, page):
    bad_titles = [
        "loved this book ?", "about woolf:", "feedbooks", "project gutenberg", "similar users also downloaded",
        "copyright", "download", "license", "public domain", "source:", "brought to you by",
        "chapter", "contents", "index", "table of contents", "page", "the end", "about the author",
        "biography", "publication", "publisher", "printed in", "first published", "this book is brought to you by",
        "for more free ebooks", "visit", "contact us", "disclaimer", "transcriber", "footnote", "notes", "introduction",
        "foreword", "appendix", "prologue", "epilogue", "book", "part"
    ]
    if not title or any(bad in title.lower() for bad in bad_titles) or len(title.strip()) < 4:
        content_clean = clean_text(content)
        first_sentence = summarize(content_clean, max_sentences=1)
        return first_sentence if first_sentence else f"Section on page {page}"
    return title.strip()

def summarize_most_relevant(text, prompt, model=None, max_words=120):
    cleaned_text = clean_text(text)
    paragraphs = [p.strip() for p in cleaned_text.split('\n') if p.strip()]
    if not paragraphs:
        paragraphs = [cleaned_text]
    prompt_emb = embed_onnx(prompt)
    best_para = ""
    best_score = -1
    for para in paragraphs:
        para_emb = embed_onnx(para)
        score = cosine_similarity([prompt_emb], [para_emb])[0][0]
        if score > best_score and para.strip():
            best_score = score
            best_para = para
    if not best_para.strip():
        for para in paragraphs:
            if para.strip():
                best_para = para
                break
    content_paras = extract_content_paragraphs(cleaned_text, top_k=2)
    if not content_paras:
        content_paras = [best_para]
    summary = ' '.join([summarize(p, max_sentences=3) for p in content_paras])
    words = summary.split()
    if len(words) > max_words:
        summary = ' '.join(words[:max_words])
    return summary if summary.strip() else "Content not available."

def summarize_text(text: str) -> str:
    summary = textrank_summary(text)
    if not summary:
        summary = summarize(text)
    return summary

# Logging
logging.basicConfig(level=logging.INFO)
def log_extraction(pdf_name, num_sections):
    logging.info(f"Extracted {num_sections} sections from {pdf_name}")

def log_scoring(section_title, score):
    logging.info(f"Section '{section_title}' scored {score:.4f}")

def check_document_coverage(pdf_paths, processed_sections):
    processed_docs = set([Path(s['doc']).name for s in processed_sections])
    all_docs = set([Path(p).name for p in pdf_paths])
    missing = all_docs - processed_docs
    if missing:
        logging.warning(f"Missing documents in output: {missing}")
    else:
        logging.info("All documents processed.")
