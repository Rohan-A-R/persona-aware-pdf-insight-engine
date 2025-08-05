# ---- STAGE 1: The Builder ----
# This stage builds the Python packages into wheels
FROM --platform=linux/amd64 python:3.10-slim AS builder

WORKDIR /app

# Install minimal build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ build-essential \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements and build the wheels for offline installation
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# ---- STAGE 2: The Final Image ----
# This stage is the minimal runtime environment
FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app

# Copy the pre-built wheels from the builder stage
COPY --from=builder /wheels /wheels
COPY requirements.txt .

# Install the packages from the local wheels without hitting the network
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels ~/.cache/pip

# --- AGGRESSIVE CLEANUP ---
# This step removes non-essential files to reduce image size.
RUN find /usr/local/lib/python3.10/site-packages/ -name "tests" -type d -exec rm -rf {} + \
 && find /usr/local/lib/python3.10/site-packages/ -name "*.pyc" -delete \
 && find /usr/local/lib/python3.10/site-packages/ -name "__pycache__" -type d -exec rm -rf {} +

# Copy your application code and models
COPY optimized_pipeline.py .
COPY summarizer.py .
COPY final_submission.py .
COPY pdf_parser.py .
COPY utils/ ./utils/
COPY models/ ./models/

# --- CORRECTED ENVIRONMENT VARIABLES (No trailing slashes) ---
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV MINILM_MODEL_PATH=/app/models/all-MiniLM-L6-v2
ENV CROSS_ENCODER_MODEL_PATH=/app/models/cross-encoder-ms-marco-MiniLM-L-6-v2

# Create I/O directories
RUN mkdir -p /app/input /app/output

# Set the entrypoint
CMD ["python", "final_submission.py"]
