import fitz  # PyMuPDF
import hashlib
import re
from typing import List, Dict

def clean_pdf_text(text: str) -> str:
    """
    Cleans raw text extracted from a PDF page by removing common artifacts.
    """
    # Remove headers and footers (lines that are mostly numbers or short)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        # Heuristic: Ignore lines that are just numbers (page numbers) or very short
        if line.isdigit() or len(line.split()) < 4:
            continue
        cleaned_lines.append(line)
    
    text = " ".join(cleaned_lines)
    
    # Remove excessive whitespace and fix hyphenated words at line breaks
    text = re.sub(r'-\s+', '', text)  # Re-join hyphenated words
    text = re.sub(r'\s+', ' ', text).strip() # Normalize whitespace
    
    return text

def split_text_into_chunks(text: str, chunk_size: int = 250, overlap: int = 50) -> List[str]:
    """Splits text into chunks of ~chunk_size words with overlap."""
    words = text.split()
    if not words:
        return []
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i + chunk_size]
        chunks.append(" ".join(chunk))
        if i + chunk_size >= len(words):
            break
        i += chunk_size - overlap
    return chunks

def extract_sections_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extracts granular, cleaned, and uniformly-sized text chunks from a PDF.
    """
    doc = fitz.open(pdf_path)
    chunks = []
    for page_num, page in enumerate(doc):
        raw_text = page.get_text("text")
        
        # --- NEW: Clean the text before chunking ---
        cleaned_text = clean_pdf_text(raw_text)
        
        if not cleaned_text:
            continue
            
        page_chunks = split_text_into_chunks(cleaned_text)
        for idx, chunk_text in enumerate(page_chunks):
            chunk_id = hashlib.md5(
                (f"{pdf_path}-{page_num}-{idx}-{chunk_text[:30]}").encode()
            ).hexdigest()
            chunks.append({
                "text": chunk_text,
                "document": str(pdf_path).split("/")[-1],
                "page_number": page_num + 1,
                "chunk_id": chunk_id
            })
    doc.close()
    return chunks