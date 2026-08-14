"""FastAPI server — exposes the Python pipeline and Grok Q&A to the React client."""
from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

import os

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.api.store import AnalysisStore
from src.pipeline.drawing_pipeline import analyze_drawing
from src.services.grok_service import GrokService

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "data" / "outputs"
DEFAULT_ANALYSIS = OUTPUT_DIR / "final_analysis.json"

app = FastAPI(title="Vector-PID API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_grok: GrokService | None = None


def _get_grok() -> GrokService:
    global _grok
    if _grok is None:
        _grok = GrokService()
    return _grok


def _run_pipeline_job(job_id: str, file_path: Path) -> None:
    try:
        result = analyze_drawing(file_path, output_dir=OUTPUT_DIR)
        AnalysisStore.complete_job(job_id, result)
    except Exception as exc:
        AnalysisStore.fail_job(job_id, str(exc))
    finally:
        if file_path.parent.name.startswith("vector_pid_"):
            shutil.rmtree(file_path.parent, ignore_errors=True)


def _extract_sources(answer: str) -> list[str]:
    return sorted(set(re.findall(r"\b(?:OBJ|TXT|LINE)-[\w-]+\b", answer)))


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


@app.on_event("startup")
def load_cached_analysis() -> None:
    AnalysisStore.load_from_disk(DEFAULT_ANALYSIS)


@app.get("/api/v1/health")
def health() -> dict:
    current = AnalysisStore.get_current()
    return {
        "status": "ok",
        "has_analysis": current is not None,
        "grok_configured": bool(os.getenv("GROK_API_KEY")),
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")) and os.getenv("GEMINI_API_KEY") != "your_gemini_api_key_here",
    }


@app.get("/api/v1/analysis")
def get_analysis() -> dict:
    current = AnalysisStore.get_current()
    if not current:
        raise HTTPException(status_code=404, detail="No analysis loaded. Upload a P&ID or run the pipeline.")
    return current


@app.get("/api/v1/graph")
def get_graph() -> dict:
    current = AnalysisStore.get_current()
    if not current:
        raise HTTPException(status_code=404, detail="No analysis loaded.")
    return current.get("graph", {})


@app.get("/api/v1/reasoning")
def get_reasoning() -> dict:
    """Return the AI reasoning JSON with connection explanations and process flows."""
    current = AnalysisStore.get_current()
    if not current:
        raise HTTPException(status_code=404, detail="No analysis loaded.")

    reasoning = current.get("ai_reasoning")
    if not reasoning:
        raise HTTPException(
            status_code=404,
            detail="No AI reasoning data available. Ensure GEMINI_API_KEY is configured and re-run the pipeline.",
        )
    return reasoning


@app.post("/api/v1/analyze")
async def analyze_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    allowed = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    tmp_dir = Path(tempfile.mkdtemp(prefix="vector_pid_"))
    dest = tmp_dir / Path(file.filename).name
    content = await file.read()
    dest.write_bytes(content)

    job_id = AnalysisStore.create_job()
    background_tasks.add_task(_run_pipeline_job, job_id, dest)
    return {"job_id": job_id, "status": "pending"}


@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = AnalysisStore.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **job}


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    current = AnalysisStore.get_current()
    if not current:
        raise HTTPException(status_code=404, detail="No analysis loaded. Upload a drawing first.")

    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    try:
        grok = _get_grok()
        answer = await grok.answer_question(question, current)
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Grok API error: {exc}") from exc

    return ChatResponse(answer=answer, sources=_extract_sources(answer))
