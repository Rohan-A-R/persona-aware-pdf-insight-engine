# 📄 AI-Powered PDF Summarization & Persona-Aware Relevance Extractor

This project is a fully offline, containerized system that processes PDF documents and surfaces the most relevant sections based on a user's **persona** and **task**. It delivers concise summaries and contextual insights using a multi-stage semantic ranking pipeline.

---

## ✅ Key Features

* Extracts **section-level content** from PDFs using font and layout heuristics.
* Uses a **Retriever-Reader architecture** powered by:

  * **MiniLM Bi-Encoder** (quantized, ONNX) for semantic chunk retrieval
  * **Cross-Encoder** (quantized, ONNX) for reranking top candidates
* Runs **entirely offline** inside a **Docker container**
* Optimized for **CPU-only execution** with **total model size ≤ 1GB**
* Outputs structured, ranked summaries in JSON format

---

## 🧠 Solution Architecture

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

## 📥 Input Format

**Location**: `/app/input/challenge1b_input.json`

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

## 📤 Output Format

**Location**: `/app/output/challenge1b_output.json`

Includes:

* `extracted_sections`: top relevant sections with titles, pages, and scores
* `subsection_analysis`: best context sentences per section
* `metadata`: persona, task, input files, timestamp

### Example

```json
{
  "metadata": {
    "input_documents": ["ml_intro.pdf", "deep_learning_basics.pdf"],
    "persona": "Data Scientist",
    "job_to_be_done": "Learn key ML techniques",
    "processing_timestamp": "2025-07-27T12:00:00Z"
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

---

## 🚀 How to Run

### 🐳 Using Docker (Recommended)

```bash
docker build -t pdf-summarizer .
docker run \
  -v /absolute/path/to/input:/app/input \
  -v /absolute/path/to/output:/app/output \
  pdf-summarizer
```

📁 Ensure:

* `/app/input/challenge1b_input.json` contains persona, task, and filenames
* PDFs listed are in `/app/input/`
* Models are in `/app/models/`

### 🐍 Using Python (Alternate)

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python final_submission.py
```

---

## 📁 Project Structure (Minimal)

```
Challenge_1b/
├── Dockerfile
├── requirements.txt
├── final_submission.py
├── optimized_pipeline.py
├── pdf_parser.py
├── /models/
│   ├── all-MiniLM-L6-v2/         # Quantized Bi-Encoder
│   └── cross-encoder-ms-marco/   # Quantized Cross-Encoder
├── /utils/
│   ├── embeddings.py
│   ├── similarity.py
│   └── reranker.py
├── /input/                       # Mounted at runtime
├── /output/                      # Mounted at runtime
├── approach_explanation.md
├── SUBMISSION_REPORT.md
```

---

## ⚡ Optimizations

| Component         | Optimization Detail                                    |
| ----------------- | ------------------------------------------------------ |
| Embedding         | Quantized ONNX models (INT8)                           |
| Section Filtering | Regex-based cleaning + multi-pass heuristic filters    |
| Speed             | Parallel parsing using `ThreadPoolExecutor`            |
| Diversity         | Max 2 results per document                             |
| Size Compliance   | Total model size ≤ 1GB, Docker image size unrestricted |

---

## 📘 Notes for Submission

* Do **not** submit `/input/` or `/output/` folders
* Adobe's system will mount them dynamically at `/app/input` and `/app/output`
* No internet should be required at runtime (fully offline)

---

## 🧪 Evaluation Ready

✔️ Tested on real-world PDF sets
✔️ Optimized for <10s per document on CPU
✔️ Fully reproducible with Docker
✔️ Final models and logic comply with Adobe Hackathon 2025 constraints
