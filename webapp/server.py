"""API pública limitada e interface do case V8."""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import date
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

import etl
from webapp import store
from webapp import documentation
from webapp.presentation import DOWNLOADS, audit_details, build_presentation, output_path


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "webapp" / "static"
FEATURED = Path(os.environ.get("RANKING_FEATURED_DIR", ROOT / "resultados" / "2026-09-22"))
MAX_UPLOAD = 10 * 1024 * 1024
ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")

app = FastAPI(title="Ranking semanal de ações", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.middleware("http")
async def secure_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    if request.url.path.startswith("/api/analyses"):
        response.headers["Cache-Control"] = "no-store"
    if request.url.path.startswith("/static/") or response.headers.get("content-type", "").startswith("text/html"):
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/healthz")
def healthz():
    store.initialize()
    return {"ok": True}


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/metodologia")
def methodology_page():
    return FileResponse(STATIC / "methodology.html")


@app.get("/documentacao", response_class=HTMLResponse)
def documentation_home():
    return documentation.render("comece-aqui")


@app.get("/documentacao/{slug}", response_class=HTMLResponse)
def documentation_article(slug: str):
    if slug not in documentation.PAGES:
        raise HTTPException(404, "Artigo não encontrado")
    return documentation.render(slug)


@app.get("/api/documentation")
def documentation_index():
    return documentation.search_index()


@app.get("/nova-analise")
def new_analysis_page():
    return FileResponse(STATIC / "new-analysis.html")


@app.get("/analise/{job_id}/metodologia")
def analysis_methodology_page(job_id: str):
    job_or_404(job_id)
    return FileResponse(STATIC / "methodology.html")


@app.get("/analise/{job_id}")
def analysis_page(job_id: str):
    valid_id(job_id)
    return FileResponse(STATIC / "index.html")


def valid_id(job_id: str) -> None:
    if not ID_PATTERN.fullmatch(job_id):
        raise HTTPException(404, "Análise não encontrada")


def job_or_404(job_id: str) -> dict:
    valid_id(job_id)
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(404, "Análise não encontrada")
    return job


@app.get("/api/featured")
def featured():
    try:
        return build_presentation(FEATURED, featured=True)
    except ValueError as exc:
        raise HTTPException(503, f"Não foi possível conferir os arquivos desta execução: {exc}") from None


@app.get("/api/featured/files/{name}")
def featured_file(name: str):
    try:
        path = output_path(FEATURED, name, featured=True)
    except KeyError:
        raise HTTPException(404, "Arquivo indisponível") from None
    if not path.is_file():
        raise HTTPException(404, "Arquivo indisponível")
    return FileResponse(path, filename=name)


@app.post("/api/analyses", status_code=202)
async def create_analysis(request: Request, reference_date: date = Form(...), file: UploadFile = File(...)):
    if reference_date > date.today():
        raise HTTPException(422, "A data de referência não pode estar no futuro")
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(422, "Envie uma extração em arquivo CSV")
    client_ip = request.client.host if request.client else "unknown"
    try:
        store.check_limits(client_ip)
    except store.LimitError as exc:
        raise HTTPException(429, str(exc)) from None
    job_id = uuid.uuid4().hex
    folder = store.DATA_DIR / "uploads"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{job_id}.csv"
    sha = hashlib.sha256()
    size = 0
    try:
        with target.open("xb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD:
                    raise HTTPException(413, "O CSV deve ter no máximo 10 MB")
                sha.update(chunk)
                output.write(chunk)
        rows, _encoding = etl.read_economatica(target)
        if not rows:
            raise HTTPException(422, "O CSV não contém linhas de dados")
        try:
            store.create_job(job_id, reference_date.isoformat(), sha.hexdigest(), client_ip)
        except store.LimitError as exc:
            raise HTTPException(429, str(exc)) from None
    except etl.InputError as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(422, str(exc)) from None
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return {"id": job_id, "status": "queued", "url": f"/analise/{job_id}"}


@app.get("/api/analyses/{job_id}")
def analysis_status(job_id: str):
    job = job_or_404(job_id)
    return {**job, "result_url": f"/api/analyses/{job_id}/result" if job["status"] == "completed" else None}


@app.get("/api/analyses/{job_id}/result")
def analysis_result(job_id: str):
    job = job_or_404(job_id)
    if job["status"] != "completed":
        raise HTTPException(409, "A análise ainda não foi concluída")
    path = store.DATA_DIR / "runs" / job_id / "presentation.json"
    if not path.is_file():
        raise HTTPException(410, "O resultado expirou. Envie o arquivo novamente.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    root = path.parent
    try:
        payload["audit"] = audit_details(root)
    except ValueError as exc:
        raise HTTPException(503, f"Não foi possível conferir os arquivos desta execução: {exc}") from None
    payload["downloads"] = [name for name in DOWNLOADS if output_path(root, name).is_file()]
    return JSONResponse(payload)


@app.get("/api/analyses/{job_id}/files/{name}")
def analysis_file(job_id: str, name: str):
    job = job_or_404(job_id)
    if job["status"] != "completed":
        raise HTTPException(409, "A análise ainda não foi concluída")
    try:
        path = output_path(store.DATA_DIR / "runs" / job_id, name)
    except KeyError:
        raise HTTPException(404, "Arquivo indisponível") from None
    if not path.is_file():
        raise HTTPException(410, "O arquivo expirou ou está indisponível")
    return FileResponse(path, filename=name)
