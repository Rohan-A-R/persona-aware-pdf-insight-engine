# 📘 AI Persona-Based PDF Analyzer

## 🚀 Problem Statement Summary
Build a system that:
- Takes as input:
  - A **persona** (e.g., `"Data Scientist"`)
  - A **job to be done** (e.g., `"Learn key ML techniques"`)
  - A collection of **PDF documents**
- Outputs:
  - The **most relevant sections** from the documents
  - A **refined analysis** of those sections

**Constraints**:
- Must run offline inside a **Docker container** on **CPU**
- Entire system (model + code) ≤ **1gb
- Input: `/app/input/challenge1b_input.json`
- Output: `/app/output/challenge1b_output.json`

---

## 🧠 High-Level Solution Architecture

```text
+------------------------+
| challenge1b_input.json |
+------------------------+
           |
           v
+-------------------------------+
| Read persona, task, and PDFs |
+-------------------------------+
           |
           v
+-----------------------------------------+
| Extract & clean sections using PyMuPDF |
+-----------------------------------------+
           |
           v
+----------------------------------------+
| Embed using quantized MiniLM BiEncoder |
+----------------------------------------+
           |
           v
+----------------------------------------+
| Retrieve Top-50 chunks by similarity   |
+----------------------------------------+
           |
           v
+----------------------------------------+
| Cross-Encoder reranks top-K (ONNX)     |
+----------------------------------------+
           |
           v
+--------------------------------------------+
| Refine output: title & smart subsections   |
+--------------------------------------------+
           |
           v
+-------------------------+
| challenge1b_output.json |
+-------------------------+
```

---

## 🧩 Detailed Components

### 1. PDF Section Extraction
- Uses **PyMuPDF** (`fitz`) to extract text page-by-page
- Cleans using regex/heuristics: removes headers, footers, TOCs, copyrights
- Splits into overlapping 250-word chunks with metadata:
  - `text`, `page_number`, `chunk_id`, `document name`

### 2. Stage 1: Fast Retrieval with Bi-Encoder
- Query format:
  ```python
  persona_query = f"{persona}: {task}"
  ```
- Embeds query and chunks using **quantized all-MiniLM-L6-v2**
- Retrieves **top 50 chunks** using **cosine similarity**

### 3. Stage 2: Accurate Reranking with Cross-Encoder
- Uses **ms-marco-MiniLM-L-6-v2** ONNX model
- Scores relevance for top 50 pairs (query, chunk)
- Selects top K (default: 5) with **2-chunk per document max**

### 4. Smart Title & Subsection Extraction
- Finds the most relevant sentence for `section_title`
- Extracts top 2–3 context sentences for `subsection_analysis`
- Fallbacks for short/empty chunks

### 5. Output Format (JSON)
- `metadata`: persona, task, document list, timestamp
- `extracted_sections`: top-ranked sections per doc
- `subsection_analysis`: refined sentences

---

## ⚡ Performance Optimizations

| Component          | Optimization Detail                                           |
|-------------------|---------------------------------------------------------------|
| Embedding          | Quantized ONNX models (INT8)                                  |
| Section Filtering  | Regex-based cleaning + multi-pass heuristic filters           |
| Speed              | Parallel extraction using `ThreadPoolExecutor`                |
| Diversity          | Limits to 2 results per document                              |
| System Size        | ≤ 200MB using light-weight dependencies and quantization      |

---

## 📁 File Structure

```
/app
├── input/
│   └── challenge1b_input.json      # Input configuration
├── output/
│   └── challenge1b_output.json     # Output result
├── models/
│   ├── all-MiniLM-L6-v2/           # Quantized BiEncoder
│   └── cross-encoder-ms-marco/     # Quantized CrossEncoder
├── utils/
│   ├── embeddings.py               # Embedding utilities
│   ├── similarity.py               # Cosine similarity logic
│   └── reranker.py                 # Cross-encoder reranking logic
├── pdf_parser.py                   # PDF extraction & chunking
├── optimized_pipeline.py           # Main pipeline logic
└── final_submission.py             # Entry point for Docker
```

---

## 🧪 Example Input Format

```json
{
  "persona": { "role": "Data Scientist" },
  "job_to_be_done": { "task": "Learn key ML techniques" },
  "documents": [
    { "filename": "ml_intro.pdf" },
    { "filename": "deep_learning_basics.pdf" }
  ]
}
```

---

## ✅ Output Schema

```json
{
  "metadata": {
    "input_documents": ["ml_intro.pdf", "deep_learning_basics.pdf"],
    "persona": "Data Scientist",
    "job_to_be_done": "Learn key ML techniques",
    "processing_timestamp": "2025-07-27T14:03:01.123Z"
  },
  "extracted_sections": [
    {
      "document": "ml_intro.pdf",
      "section_title": "Gradient descent optimization techniques",
      "importance_rank": 1,
      "page_number": 5
    }
  ],
  "subsection_analysis": [
    {
      "document": "ml_intro.pdf",
      "page_number": 5,
      "refined_text": "Gradient descent is used to minimize loss functions in training."
    }
  ]
}
```