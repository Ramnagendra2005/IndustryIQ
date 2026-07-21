"""FastAPI surface for IndustryIQ."""
from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .auth import AuthError, get_auth, make_token, verify_token
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
    get_auth()               # seed the demo account + hydrate saved tenants
    get_engine("demo")       # warm the demo graph/index/model at boot


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    industry_name: str = ""   # set to found a new industry
    join_code: str = ""       # set to join an existing one


def _issue(principal: dict) -> dict:
    """Bundle a signed token with the principal for the client to store."""
    return {"token": make_token(principal), "user": principal}


@app.post("/api/auth/login")
def auth_login(req: LoginRequest):
    try:
        return _issue(get_auth().login(req.email, req.password))
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@app.post("/api/auth/register")
def auth_register(req: RegisterRequest):
    try:
        principal = get_auth().register(
            req.email, req.name, req.password,
            industry_name=req.industry_name, join_code=req.join_code)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    get_engine(principal["iid"])   # build the new tenant's (empty) engine now
    return _issue(principal)


def current_user(authorization: str = Header(default=""), token: str = "") -> dict:
    """FastAPI dependency: resolve the Bearer token to a principal, or 401.
    Every data route depends on this, so a request can only ever touch its
    own industry's engine. The `token` query param is a fallback for
    <img src> requests (P&ID images), which can't set an Authorization header."""
    bearer = authorization[7:].strip() if authorization.lower().startswith("bearer ") else ""
    principal = verify_token(bearer or token) if (bearer or token) else None
    if not principal:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return principal


def user_engine(user: dict = Depends(current_user)):
    return get_engine(user.get("iid", "demo"))


@app.get("/api/auth/me")
def auth_me(user: dict = Depends(current_user)):
    return user


@app.get("/api/status")
def status(eng=Depends(user_engine)):
    return eng.status()


@app.post("/api/query")
def query(req: QueryRequest, eng=Depends(user_engine)):
    return eng.answer(req.question, req.mode, req.lang).model_dump()


@app.get("/api/compliance")
def compliance(scope: str = "Unit CDU-1 charge pumps", eng=Depends(user_engine)):
    return eng.compliance(scope).model_dump()


@app.get("/api/trust")
def trust(eng=Depends(user_engine)):
    return eng.trust().model_dump()


@app.get("/api/graph")
def graph(focus: str | None = None, radius: int = 2, eng=Depends(user_engine)):
    return eng.graph_view(focus, radius)


@app.get("/api/pids")
def pids(eng=Depends(user_engine)):
    return eng.pid_list()


@app.get("/api/pid/{doc_id}")
def pid(doc_id: str, eng=Depends(user_engine)):
    d = eng.pid_diagram(doc_id)
    if not d:
        return JSONResponse({"error": "P&ID not found"}, status_code=404)
    return d


@app.get("/api/pid/{doc_id}/image")
def pid_image(doc_id: str, eng=Depends(user_engine)):
    img = eng.pid_image(doc_id)
    if not img:
        return JSONResponse({"error": "image not found"}, status_code=404)
    data, media_type = img
    return Response(content=data, media_type=media_type)


@app.get("/api/entity/{name}")
def entity(name: str, eng=Depends(user_engine)):
    return eng.entity_dossier(name)


@app.get("/api/documents")
def documents(eng=Depends(user_engine)):
    return eng.documents()


@app.get("/api/documents/{doc_id}")
def document(doc_id: str, eng=Depends(user_engine)):
    d = eng.document(doc_id)
    return d or {"error": "not found"}


@app.post("/api/ingest")
async def ingest(file: UploadFile = File(...), eng=Depends(user_engine)):
    content = await file.read()
    return eng.ingest_upload(file.filename or "upload.txt", content)


# ---- serve the built frontend if present (single-origin deploy) ----------- #
_FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="assets")

    @app.get("/")
    def _index():
        return FileResponse(_FRONTEND_DIST / "index.html")
