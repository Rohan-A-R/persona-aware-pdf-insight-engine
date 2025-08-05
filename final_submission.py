import json
import time
import os
import sys
from pathlib import Path
from optimized_pipeline import process_documents

def load_input_config():
    """Reads input config from /app/input/challenge1b_input.json."""
    input_path = "/app/input/challenge1b_input.json"
    if not os.path.exists(input_path):
        print("[ERROR] Missing challenge1b_input.json in input directory.")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    persona = data.get("persona", {}).get("role", "").strip()
    task = data.get("job_to_be_done", {}).get("task", "").strip()
    documents = data.get("documents", [])
    pdf_filenames = [doc.get("filename") for doc in documents if doc.get("filename")]

    if not persona or not task:
        print("[ERROR] Persona or task missing from input JSON.")
        sys.exit(1)

    if not pdf_filenames:
        print("[ERROR] No document filenames found in input JSON.")
        sys.exit(1)

    return persona, task, pdf_filenames

def main():
    """Main submission process."""
    print("🚀 Starting Document Intelligence Pipeline...")

    input_dir = "/app/input"
    output_dir = "/app/output"
    output_path = os.path.join(output_dir, "challenge1b_output.json")

    if not os.path.exists(input_dir):
        print(f"[ERROR] Input directory '{input_dir}' not found inside the container.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    persona, task, filenames = load_input_config()

    # Resolve full paths to the PDFs inside the container
    pdf_paths = [os.path.join(input_dir, fname) for fname in filenames]

    print(f"\n🔍 Processing Documents for:")
    print(f"  👤 Persona: {persona}")
    print(f"  🎯 Task: {task}")
    print(f"  📄 Files: {len(pdf_paths)}")

    start_time = time.time()

    try:
        process_documents(
            pdf_paths=pdf_paths,
            persona=persona,
            task=task,
            output_file=output_path,
            top_k=5,
            max_per_doc=2
        )
    except Exception as e:
        print(f"❌ An error occurred during processing: {e}")
        sys.exit(1)

    elapsed = time.time() - start_time
    print(f"\n✅ Finished in {elapsed:.2f} seconds.")
    print(f"📁 Output saved to: {output_path}")

if __name__ == "__main__":
    main()
