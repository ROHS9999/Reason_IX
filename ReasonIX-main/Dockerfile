# Backend image. Python 3.12 has ready-made wheels for every dependency (chromadb, pymupdf, torch...).
FROM python:3.12-slim
WORKDIR /app

# CPU-only torch first: the default wheel bundles CUDA and makes the image ~4 GB bigger.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt requirements-extras.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-extras.txt

# Bake the models into the image so the first request is not slow (and works without internet at run time).
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('all-MiniLM-L6-v2'); CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2'); \
CrossEncoder('cross-encoder/nli-deberta-v3-base')"

COPY . .
ENV DATA_DIR=/app/data
EXPOSE 8000
# GROQ_API_KEY and ALLOWED_ORIGINS are passed at run time (never baked into the image).
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
