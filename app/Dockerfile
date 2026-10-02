# Stage 1: Build & Pre-cache Dependencies
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

ENV PATH="/opt/venv/bin:$PATH"
ENV HF_HOME="/tmp/hf_build_cache"

# Pre-download Model Weight และบันทึกลงโฟลเดอร์ปลายทางโดยตรง
RUN python3 -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); model.save('/app/model')"

# Stage 2: Hardened Runtime Image
FROM python:3.11-slim

WORKDIR /app

# คัดลอก Virtual Environment และ Model Artifacts ที่ Build เสร็จแล้ว
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/model /app/model

ENV PATH="/opt/venv/bin:$PATH"
ENV MODEL_PATH="/app/model"
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_DISABLE_SYMLINKS_WARNING=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV OMP_NUM_THREADS=1

COPY main.py .

# สร้าง Non-root User (UID 10001) และตั้ง Permission
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -d /app -s /sbin/nologin appuser && \
    chown -R appuser:appgroup /app && \
    chmod -R 555 /app/model

USER 10001

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--timeout-keep-alive", "30"]
