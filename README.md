# 📄 PDF Summarization & Persona-Aware Relevance Extractor

This system processes PDF documents and outputs the most relevant content based on a given **persona** and **task**. It is designed for **offline execution**, supports **containerized deployment**, and produces structured, ranked summaries.

---

## ✅ Key Features

- Extracts **section-level content** from PDFs using heuristics.
- Ranks relevance using **MiniLM Bi-Encoder + Cross-Encoder** (quantized ONNX models).
- Runs **offline entirely**—no internet required.
- **Dockerized** and **CPU-optimized** (≤ 1GB total size).
- Outputs results in **structured JSON** format to `/app/output/`.

---

## 🚀 How to Run

### 🐫 Using Docker (Recommended)

```bash
docker build -t pdf-summarizer .
docker run \
  -v /absolute/path/to/input:/app/input \
  -v /absolute/path/to/output:/app/output \
  pdf-summarizer
```

📁 Ensure:

- `/app/input/challenge1b_input.json` contains the input config
- PDFs listed are in `/app/input/`
- Models are in `/app/models/`

---

### 🐍 Using Python (Alternate)

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python final_submission.py
```

---

## 📅 Input Format

**Location**: `/app/input/challenge1b_input.json`

```json
{
  "persona": { "role": "Travel Enthusiast" },
  "job_to_be_done": { "task": "Plan a cultural trip to the South of France" },
  "documents": [
    { "filename": "France.pdf" },
    { "filename": "Culture.pdf" }
  ]
}
```

---

## 📄 Output Format

**Location**: `/app/output/challenge1b_output.json`

Includes:

- `extracted_sections`: top relevant sections with titles, pages, and scores
- `subsection_analysis`: best context sentences per section
- `metadata`: persona, task, input files, timestamp

### Example

```json
{
  "metadata": {
    "input_documents": ["France.pdf", "Culture.pdf"],
    "persona": "Travel Enthusiast",
    "job_to_be_done": "Plan a cultural trip to the South of France",
    "processing_timestamp": "2025-07-27T12:00:00Z"
  },
  "extracted_sections": [
    {
      "document": "France.pdf",
      "section_title": "Cultural Highlights in Provence",
      "importance_rank": 1,
      "page_number": 3
    }
  ],
  "subsection_analysis": [
    {
      "document": "France.pdf",
      "page_number": 3,
      "refined_text": "Provence is known for its Roman heritage and lavender fields."
    }
  ]
}
```

---

## 📂 Project Structure (Minimal)

```
Challenge_1b/
├── Dockerfile
├── requirements.txt
├── final_submission.py
├── optimized_pipeline.py
├── pdf_parser.py
├── /models/
│   ├── all-MiniLM-L6-v2/
│   └── cross-encoder-ms-marco-MiniLM-L-6-v2/
├── /utils/
│   ├── embeddings.py
│   ├── similarity.py
│   └── reranker.py
├── approach_explanation.md
├── SUBMISSION_REPORT.md
```

---

## 📘 Additional Documentation

- 🔍 **Approach Overview**: `approach_explanation.md`
- 📊 **Final Notes**: `SUBMISSION_REPORT.md`
