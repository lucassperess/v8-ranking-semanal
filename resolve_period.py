"""Busca por data as fontes B3 necessárias e executa a classificação da janela.

Arquivos oficiais são guardados por data e nunca sobrescritos. Falha de acesso
não produz classificação por sufixo: a etapa gera um relatório de pendências.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import urllib.error
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

from b3_registry import digest
from classify_period import ClassificationError, run as classify


def source(kind: str, day: date) -> tuple[str, str]:
    if kind == "registry":
        name = f"IN{day:%y%m%d}.zip"
        return name, f"https://www.b3.com.br/pesquisapregao/download?filelist={name},"
    if kind == "cotahist":
        name = f"COTAHIST_D{day:%d%m%Y}.ZIP"
        return name, f"https://bvmf.bmfbovespa.com.br/InstDados/SerHist/{name}"
    raise ValueError(f"Fonte desconhecida: {kind}")


def acquire(kind: str, day: date, reference_dir: Path, offline: bool = False) -> tuple[Path | None, dict]:
    name, url = source(kind, day)
    target = reference_dir / name
    event = {"kind": kind, "source_date": day.isoformat(), "url": url, "file": name}
    if target.is_file():
        if not zipfile.is_zipfile(target):
            return None, {**event, "status": "invalid_cache", "reason": "Arquivo local não é ZIP válido"}
        return target, {**event, "status": "available", "sha256": digest(target)}
    if offline:
        return None, {**event, "status": "unavailable", "reason": "Arquivo ausente e modo offline"}
    reference_dir.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; V8RankingResearch/1.0)"})
        with tempfile.NamedTemporaryFile(dir=reference_dir, suffix=".part", delete=False) as output:
            temporary = Path(output.name)
            with urllib.request.urlopen(request, timeout=45) as response:
                while block := response.read(1024 * 1024):
                    output.write(block)
        if not zipfile.is_zipfile(temporary):
            return None, {**event, "status": "unavailable", "reason": "Resposta não é ZIP válido"}
        # Nunca substitui um arquivo de referência já existente.
        if target.exists():
            return None, {**event, "status": "invalid_cache", "reason": "Destino apareceu durante o download; revisar manualmente"}
        temporary.replace(target)
        temporary = None
        return target, {**event, "status": "available", "sha256": digest(target)}
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        return None, {**event, "status": "unavailable", "reason": f"{type(exc).__name__}: {exc}"}
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def run(normalized: Path, start: date, end: date, output_dir: Path, reference_dir: Path,
        offline: bool = False) -> dict:
    if start >= end:
        raise ClassificationError("Data inicial deve ser anterior à data final")
    events, registries, quotes = [], [], []
    # O COTAHIST pequeno cobre a espécie na data do preço; o cadastro do fim
    # da janela fornece a classificação oficial e checagem de ISIN.
    for kind, day in (("cotahist", start), ("cotahist", end), ("registry", end)):
        path, event = acquire(kind, day, reference_dir, offline)
        events.append(event)
        if path:
            (registries if kind == "registry" else quotes).append(path)
    summary = classify(normalized, start, end, output_dir, registries, quotes)
    # Se a espécie no início ainda não foi resolvida, tenta o cadastro daquele
    # próprio pregão. Divergência real permanece bloqueada para revisão.
    classification_path = output_dir / "period_classification.csv"
    import csv
    with classification_path.open(encoding="utf-8", newline="") as stream:
        unresolved_start = any(row["price_date"] == start.isoformat() and row["status"] == "unresolved"
                               for row in csv.DictReader(stream))
    if unresolved_start:
        path, event = acquire("registry", start, reference_dir, offline)
        events.append(event)
        if path:
            registries.append(path)
            summary = classify(normalized, start, end, output_dir, registries, quotes)
    report = {"start_date": start.isoformat(), "end_date": end.isoformat(),
              "normalized_sha256": digest(normalized), "sources": events,
              "classification_gate_passed": summary["classification_gate_passed"],
              "blocked_tickers": summary["blocked_tickers"]}
    (output_dir / "source_acquisition.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--normalized", type=Path, required=True)
    parser.add_argument("--start-date", type=date.fromisoformat, required=True)
    parser.add_argument("--end-date", type=date.fromisoformat, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reference-dir", type=Path, default=Path(__file__).parent / "data" / "reference")
    parser.add_argument("--offline", action="store_true", help="Não tenta baixar arquivos ausentes")
    args = parser.parse_args()
    try:
        summary = run(args.normalized, args.start_date, args.end_date, args.output_dir, args.reference_dir, args.offline)
    except (ClassificationError, OSError) as exc:
        parser.exit(2, f"Erro: {exc}\n")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["classification_gate_passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
