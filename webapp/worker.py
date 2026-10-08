"""Worker único: executa o pipeline existente em processos isolados."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from webapp import store
from webapp.doc_revision import archive
from webapp.presentation import build_presentation
from context_pipeline.sources import write


ROOT = Path(__file__).resolve().parents[1]
STOP = False


def request_stop(_signum: int, _frame: object) -> None:
    global STOP
    STOP = True


def stage_for(root: Path) -> str:
    if (root / "ranking_report.json").exists():
        return "Preparando resultado"
    if (root / "rankings" / "alternativa" / "top20.csv").exists():
        return "Calculando janela alternativa"
    if (root / "rankings" / "principal" / "top20.csv").exists():
        return "Calculando janela alternativa"
    if (root / "classification" / "principal" / "source_acquisition.json").exists():
        return "Classificando instrumentos"
    if (root / "etl" / "manifest.json").exists():
        return "Consultando fontes B3"
    return "Lendo e validando extração"


def process(job: dict) -> None:
    job_id = job["id"]
    input_path = store.DATA_DIR / "uploads" / f"{job_id}.csv"
    output_dir = store.DATA_DIR / "runs" / job_id
    reference_dir = store.DATA_DIR / "reference"
    log_path = store.DATA_DIR / "logs" / f"{job_id}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(ROOT / "weekly_ranking.py"), "--input", str(input_path),
               "--reference-date", job["reference_date"], "--output-dir", str(output_dir),
               "--reference-dir", str(reference_dir)]
    options = job.get('options', {})
    if options.get('allow_nonfriday_end'):
        command.append('--allow-nonfriday-end')
    request = {'input_sha256': job['input_sha256'], 'reference_date': job['reference_date'],
               'submitted_at': job['created_at'], 'options': options}
    if options.get('reviewed_week'):
        (output_dir / 'analysis_request.json').write_text(
            json.dumps(request, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    last_stage = ""
    started = time.monotonic()
    with log_path.open("w", encoding="utf-8") as log:
        child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                 shell=False, text=True,
                                 env={**os.environ, 'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'})
        while child.poll() is None:
            if STOP or time.monotonic() - started > 600:
                child.terminate()
                try:
                    child.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
                reason = "Servidor em encerramento" if STOP else "Processamento excedeu dez minutos"
                raise RuntimeError(reason)
            current = stage_for(output_dir)
            if current != last_stage:
                store.update_job(job_id, stage=current)
                last_stage = current
            time.sleep(1)
    if child.returncode:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        message = next((line.removeprefix("Erro: ") for line in reversed(lines) if line.startswith("Erro: ")), None)
        raise RuntimeError(message or "Não foi possível concluir a análise. Consulte o formato e a data informados.")
    archive(output_dir)
    payload = build_presentation(output_dir, normalized_path=output_dir / "etl" / "normalized.csv")
    (output_dir / "presentation.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write(output_dir / 'context/state.json', {'status': 'processing',
          'message': 'Ranking concluído. Consultando fontes para o contexto desta execução…'})
    store.update_job(job_id, status="completed", stage="Concluída")
    # Context remains optional and isolated; the completed ranking is already readable.
    try:
        prepare_context(output_dir, log_path, started)
    except Exception:
        write(output_dir / 'context/state.json', {'status': 'unavailable',
              'message': 'Não foi possível iniciar ou concluir o contexto. O ranking permanece disponível.'})


def prepare_context(output_dir, log_path, started):
    with log_path.open('a', encoding='utf-8') as log:
        context_child = subprocess.Popen([sys.executable, '-m', 'context_pipeline.generate',
                                         '--run-dir', str(output_dir)], cwd=ROOT,
                                        stdout=log, stderr=subprocess.STDOUT, shell=False,
                                        env={**os.environ, 'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'})
        while context_child.poll() is None:
            if STOP or time.monotonic() - started > 600:
                context_child.terminate()
                try:
                    context_child.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    context_child.kill()
                    context_child.wait()
                write(output_dir / 'context/state.json', {'status': 'unavailable',
                      'message': 'A coleta de contexto não terminou no prazo. O ranking está concluído e disponível.'})
                break
            time.sleep(1)
        if context_child.returncode and (output_dir / 'context/state.json').is_file():
            state = json.loads((output_dir / 'context/state.json').read_text(encoding='utf-8'))
            if state.get('status') == 'processing':
                write(output_dir / 'context/state.json', {'status': 'unavailable',
                      'message': 'A geração de contexto foi interrompida. O ranking permanece disponível.'})


def main() -> None:
    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    store.recover_interrupted()
    for state_path in (store.DATA_DIR / 'runs').glob('*/context/state.json'):
        try:
            if json.loads(state_path.read_text(encoding='utf-8')).get('status') == 'processing':
                write(state_path, {'status': 'unavailable',
                      'message': 'O servidor reiniciou durante a coleta de contexto. O ranking permanece disponível.'})
        except (OSError, ValueError):
            continue
    last_cleanup = 0.0
    while not STOP:
        if time.monotonic() - last_cleanup > 60:
            store.cleanup()
            last_cleanup = time.monotonic()
        job = store.next_job()
        if job is None:
            time.sleep(1)
            continue
        try:
            process(job)
        except Exception as exc:
            store.update_job(job["id"], status="failed", stage="Falhou", error=str(exc)[:500])


if __name__ == "__main__":
    main()
