import os
import torch
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from prometheus_fastapi_instrumentator import Instrumentator

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

torch.set_num_threads(int(os.getenv("OMP_NUM_THREADS", "1")))

app = FastAPI(
    title="Hardened AI Inference Service",
    version="1.0.0",
    docs_url=None,
    redoc_url=None
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

MODEL_PATH = os.getenv("MODEL_PATH", "/app/model")
try:
    model = SentenceTransformer(MODEL_PATH)
except Exception:
    model = None

class InferenceRequest(BaseModel):
    text: str

class InferenceResponse(BaseModel):
    text: str
    embedding_dim: int
    embedding_sample: list[float]

GRAFANA_URL = "https://educators-ever-females-karma.trycloudflare.com/d/efa86fd1d0c121a26444b636a3f509a8/kubernetes-compute-resources-cluster?kiosk"

@app.get("/", response_class=HTMLResponse)
def index():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>Hardened AI Inference Platform</title>
      <style>
        body {{ font-family: monospace; background: #0f172a; color: #f8fafc; margin: 0; padding: 40px; }}
        .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 24px; max-width: 720px; margin: 0 auto; }}
        h1 {{ color: #38bdf8; font-size: 1.5rem; margin-top: 0; }}
        .badge {{ background: #0369a1; color: #e0f2fe; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; margin-right: 6px; }}
        .btn {{ display: inline-block; background: #2563eb; color: #fff; padding: 10px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 16px; }}
        .btn:hover {{ background: #1d4ed8; }}
        textarea {{ width: 100%; height: 70px; background: #0f172a; border: 1px solid #475569; color: #fff; border-radius: 4px; padding: 8px; box-sizing: border-box; }}
        button {{ background: #10b981; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 8px; font-family: monospace; }}
        pre {{ background: #0f172a; padding: 12px; border-radius: 4px; overflow-x: auto; color: #a7f3d0; border: 1px solid #334155; }}
      </style>
    </head>
    <body>
      <div class="card">
        <h1>AI Inference & Security Platform</h1>
        <p>
          <span class="badge">PSS: Restricted</span>
          <span class="badge">Calico Zero-Trust</span>
          <span class="badge">Falco eBPF Active</span>
        </p>
        <p>Inference engine: SentenceTransformer (all-MiniLM-L6-v2) running offline.</p>
        
        <hr style="border: 0; border-top: 1px solid #334155; margin: 20px 0;">

        <h3>Live Embedding Test</h3>
        <textarea id="inputText" placeholder="Enter text to generate vector embeddings...">Testing production AI platform</textarea><br>
        <button onclick="runInference()">Run Inference</button>
        <pre id="output">Embedding vector output will appear here...</pre>

        <hr style="border: 0; border-top: 1px solid #334155; margin: 20px 0;">

        <h3>Cluster Telemetry & Observability</h3>
        <p>Access read-only Grafana cluster performance dashboard:</p>
        <a href="{GRAFANA_URL}" target="_blank" class="btn">Launch Grafana Dashboard</a>
      </div>

      <script>
        async function runInference() {{
          const text = document.getElementById('inputText').value;
          const out = document.getElementById('output');
          out.innerText = "Processing...";
          try {{
            const res = await fetch('/predict', {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: JSON.stringify({{ text }})
            }});
            const data = await res.json();
            out.innerText = JSON.stringify(data, null, 2);
          }} catch (err) {{
            out.innerText = "Error: " + err;
          }}
        }}
      </script>
    </body>
    </html>
    """

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
