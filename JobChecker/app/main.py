"""
FastAPI application (SRS section 4.3/4.4 - Software/Communication Interfaces).

Run with:
    uvicorn app.main:app --reload --port 8000

Then POST to /classify, or open /docs for interactive Swagger UI.
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .pipeline import ClassificationPipeline
from .schemas import ClassifyRequest, ClassifyResponse, ClassifyUrlRequest

app = FastAPI(
    title="Fake Job Posting Checker API",
    description="Classifies a submitted job posting (link or pasted text) as Safe, Suspicious, or Unsafe.",
    version="1.0.0",
)

# Allow the standalone test HTML page (opened as a local file, or served
# from any localhost port) to call this API directly from the browser.
# Restrict allow_origins to your actual frontend's origin in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = ClassificationPipeline()

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    """Serve the web UI at http://127.0.0.1:8000"""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/patterns")
def patterns():
    """Known scam/legit patterns from the knowledge base (shown in the UI)."""
    return [{"id": p["id"], "label": p["label"], "description": p["description"]} for p in pipeline.kb.patterns]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest):
    try:
        result = pipeline.classify(
            input_type=req.input_type,
            content=req.content,
            company_domain=req.company_domain,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Could not process submission: {e}")


@app.post("/classify-url", response_model=ClassifyResponse)
def classify_url(req: ClassifyUrlRequest):
    """
    Primary flow: give the system a job posting URL. It fetches the page,
    extracts the job-relevant text, and returns the Safe/Suspicious/Unsafe
    classification -- equivalent to POST /classify with input_type='url'.
    """
    try:
        result = pipeline.classify(
            input_type="url",
            content=req.url,
            company_domain=req.company_domain,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Could not process submission: {e}")
