import os
import torch
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from prometheus_fastapi_instrumentator import Instrumentator

# บังคับโหมด Offline ป้องกันการต่อออกภายนอกขณะ Inference
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# ล็อคจำนวน Threads สำหรับ CPU Inference เพื่อป้องกัน CPU Throttling
torch.set_num_threads(int(os.getenv("OMP_NUM_THREADS", "1")))

app = FastAPI(
    title="Hardened AI Inference Service",
    version="1.0.0",
    docs_url=None,  # ปิด Swagger UI บน Production เพื่อลด Attack Surface
    redoc_url=None
)

# Expose RED metrics สำหรับ Prometheus และ HPA
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

MODEL_PATH = os.getenv("MODEL_PATH", "/app/model")
try:
    model = SentenceTransformer(MODEL_PATH)
except Exception as e:
    model = None

class InferenceRequest(BaseModel):
    text: str

class InferenceResponse(BaseModel):
    text: str
    embedding_dim: int
    embedding_sample: list[float]

@app.get("/healthz")
def healthz():
    if model is not None:
        return {"status": "healthy"}
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "unhealthy", "reason": "Model weights not loaded"}
    )

@app.post("/predict", response_model=InferenceResponse)
def predict(request: InferenceRequest):
    if model is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "Model unavailable"}
        )
    embedding = model.encode(request.text, normalize_embeddings=True).tolist()
    return {
        "text": request.text,
        "embedding_dim": len(embedding),
        "embedding_sample": embedding[:5]
    }
