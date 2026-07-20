"""FastAPI surface for IndustryIQ."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .engine import get_engine
from .schemas import QueryRequest

app = FastAPI(title="IndustryIQ — Unified Asset & Operations Brain", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    get_engine()  # warm the graph/index/model at boot


@app.get("/api/status")
def status():
    return get_engine().status()


@app.post("/api/query")
def query(req: QueryRequest):
    return get_engine().answer(req.question, req.mode).model_dump()


@app.get("/api/compliance")
def compliance(scope: str = "Unit CDU-1 charge pumps"):
    return get_engine().compliance(scope).model_dump()


@app.get("/api/trust")
def trust():
    return get_engine().trust().model_dump()


@app.get("/api/graph")
def graph(focus: str | None = None, radius: int = 2):
    return get_engine().graph_view(focus, radius)


@app.get("/api/documents")
def documents():
    return get_engine().documents()


@app.get("/api/documents/{doc_id}")
def document(doc_id: str):
    d = get_engine().document(doc_id)
    return d or {"error": "not found"}


@app.post("/api/ingest")
async def ingest(file: UploadFile = File(...)):
    content = await file.read()
    return get_engine().ingest_upload(file.filename or "upload.txt", content)


# ---- serve the built frontend if present (single-origin deploy) ----------- #
_FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="assets")

    @app.get("/")
    def _index():
        return FileResponse(_FRONTEND_DIST / "index.html")
