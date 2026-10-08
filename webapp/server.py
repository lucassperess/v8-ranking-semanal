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
from starlette.concurrency import run_in_threadpool

import etl
from webapp import store
from webapp import documentation
from webapp.context import load_context
from webapp.doc_revision import details as documentation_details, read_snapshot
from webapp.pages import render_page
from webapp.review import review_input, problem
from weekly_ranking import RankingError
from webapp.presentation import DOWNLOADS, audit_details, build_presentation, enrich_interpretation, output_path, submission_details


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "webapp" / "static"
FEATURED = Path(os.environ.get("RANKING_FEATURED_DIR", ROOT / "resultados" / "2026-09-22"))
MAX_UPLOAD = 10 * 1024 * 1024
ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")

app = FastAPI(title="Ranking semanal de ações", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=STATIC), name="static")
app.mount('/documentation-assets', StaticFiles(directory=ROOT / 'docs' / 'assets'), name='documentation-assets')


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
    return HTMLResponse(render_page("index.html"))


@app.get("/metodologia")
def methodology_page():
    return HTMLResponse(render_page("methodology.html"))


@app.get("/documentacao", response_class=HTMLResponse)
def documentation_home():
    return documentation.render("comece-aqui")


@app.get("/documentacao/{slug}", response_class=HTMLResponse)
def documentation_article(slug: str):
    if slug not in documentation.PAGES:
        raise HTTPException(404, "Artigo não encontrado")
    return documentation.render(slug)


def archived_article(root: Path, slug: str, base: str):
    if slug not in documentation.PAGES:
        raise HTTPException(404, 'Artigo não encontrado')
    try:
        snapshot = read_snapshot(root)
    except ValueError as exc:
        raise HTTPException(503, str(exc)) from None
    if not snapshot:
        raise HTTPException(404, 'Esta execução não registrou uma cópia dos guias')
    return HTMLResponse(documentation.render(slug, snapshot=snapshot, archive_base=base))


@app.get('/documentacao/referencia/{slug}')
def featured_documentation(slug: str):
    return archived_article(FEATURED, slug, '/documentacao/referencia')


@app.get('/analise/{job_id}/documentacao/{slug}')
def analysis_documentation(job_id: str, slug: str):
    job = job_or_404(job_id)
    if job['status'] != 'completed':
        raise HTTPException(409, 'A análise ainda não foi concluída')
    return archived_article(store.DATA_DIR / 'runs' / job_id, slug, f'/analise/{job_id}/documentacao')


@app.get("/api/documentation")
def documentation_index():
    return documentation.search_index()


@app.get("/nova-analise")
def new_analysis_page():
    return HTMLResponse(render_page("new-analysis.html"))


@app.get("/analise/{job_id}/metodologia")
def analysis_methodology_page(job_id: str):
    job_or_404(job_id)
    return HTMLResponse(render_page("methodology.html"))


@app.get("/analise/{job_id}")
def analysis_page(job_id: str):
    valid_id(job_id)
    return HTMLResponse(render_page("index.html"))


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


@app.get('/api/featured/context')
def featured_context():
    return JSONResponse(load_context(FEATURED), headers={'Cache-Control': 'no-store'})


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
async def create_analysis(request: Request, reference_date: date = Form(...), file: UploadFile = File(...),
                          allow_nonfriday_end: bool = Form(False), reviewed_sha256: str = Form(''),
                          reviewed_reference_date: str = Form('')):
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
        week = await run_in_threadpool(review_input, target, reference_date)
        review = {'week': week, 'input_sha256': sha.hexdigest(),
                  'reference_date': reference_date.isoformat()}
        if week['nonfriday_end_accepted']:
            if not (allow_nonfriday_end and reviewed_sha256 == sha.hexdigest()
                    and reviewed_reference_date == reference_date.isoformat()):
                raise HTTPException(409, {
                    'code': 'short_week_review',
                    'message': 'A última data com fechamento positivo é anterior à sexta-feira. Revise a extração antes de continuar.',
                    'guidance': 'A ausência pode ser feriado ou extração incompleta. O sistema não presume a causa. Aceite apenas depois de conferir as datas disponíveis.',
                    'review': review,
                })
        elif allow_nonfriday_end:
            raise HTTPException(422, 'As datas mudaram e não exigem aceitação de semana encurtada. Confira novamente o envio.')
        options = {'allow_nonfriday_end': allow_nonfriday_end, 'reviewed_week': week,
                   'accepted_at': store.stamp() if allow_nonfriday_end else None}
        try:
            store.create_job(job_id, reference_date.isoformat(), sha.hexdigest(), client_ip, options)
        except store.LimitError as exc:
            raise HTTPException(429, str(exc)) from None
    except etl.InputError as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(422, str(exc) + ' ' + problem(str(exc))['guidance']) from None
    except RankingError as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(422, problem(str(exc))) from None
    except (ValueError, IndexError):
        target.unlink(missing_ok=True)
        raise HTTPException(422, 'Estrutura de linha inválida. Exporte novamente as nove colunas documentadas; confira campos e datas antes de reenviar.') from None
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return {"id": job_id, "status": "queued", "url": f"/analise/{job_id}"}


@app.get("/api/analyses/{job_id}")
def analysis_status(job_id: str):
    job = job_or_404(job_id)
    return {**job, 'problem': problem(job['error']) if job['error'] else None,
            "result_url": f"/api/analyses/{job_id}/result" if job["status"] == "completed" else None}


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
        payload['submission'] = submission_details(root)
        payload['documentation'] = documentation_details(root)
    except ValueError as exc:
        raise HTTPException(503, f"Não foi possível conferir os arquivos desta execução: {exc}") from None
    payload["downloads"] = [name for name in DOWNLOADS if output_path(root, name).is_file()]
    for key, name in (('primary', 'quality_context.json'), ('alternative', 'quality_context_alternativo.json')):
        quality_path = output_path(root, name)
        if quality_path.is_file():
            payload['windows'][key]['quality'] = json.loads(quality_path.read_text(encoding='utf-8'))
    return JSONResponse(enrich_interpretation(payload))


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
