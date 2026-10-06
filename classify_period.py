"""Resolve tipos de instrumentos por data para uma janela explícita do ranking.

Usa arquivos oficiais datados já baixados. Não calcula retornos nem decide
quais tipos entram no universo. Se faltar evidência para um código com preços
nos dois extremos, registra a pendência e não libera o ranking.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import zipfile
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree import ElementTree as ET

import b3_registry
from b3_registry import RegistryError, child, classify, digest, last_xml, local_name, value


VERSION = "1.0.0"
EVIDENCE_COLUMNS = ["ticker", "source_date", "source", "instrument_type", "isin", "detail", "file", "file_sha256"]
RESULT_COLUMNS = ["ticker", "price_date", "close", "status", "instrument_type", "isin", "evidence_sources", "reason"]
EXCLUSION_COLUMNS = ["ticker", "start_date_rows", "end_date_rows", "reason"]


class ClassificationError(ValueError):
    pass


def read_bvbg(path: Path, requested: set[str], cache_dir: Path | None = None) -> tuple[list[dict], dict]:
    """Lê o último XML do ZIP diário sem reter o universo da B3 em memória."""
    outer = nested = None
    try:
        file_hash = digest(path)
        with zipfile.ZipFile(path) as wrapper:
            inner_files = [name for name in wrapper.namelist() if name.upper().endswith(".ZIP")]
            payload_hash = hashlib.sha256(wrapper.read(inner_files[0])).hexdigest() if len(inner_files) == 1 else file_hash
        parser_hash = hashlib.sha256((digest(Path(__file__)) + digest(Path(b3_registry.__file__))).encode()).hexdigest()
        cache_path = cache_dir / f"bvbg_{payload_hash}_{parser_hash}.json" if cache_dir else None
        if cache_path and cache_path.is_file():
            saved = json.loads(cache_path.read_text(encoding="utf-8"))
            all_evidence, info = saved["evidence"], saved["info"]
            selected = [{**item, "file_sha256": file_hash} for item in all_evidence if item["ticker"] in requested]
            return selected, {**info, "sha256": file_hash, "payload_sha256": payload_hash,
                              "matched_rows": len(selected)}
        outer = zipfile.ZipFile(path)
        nested, xml_name = last_xml(outer)
        evidence, dates = [], set()
        scanned = 0
        with nested.open(xml_name) as stream:
            context = ET.iterparse(stream, events=("start", "end"))
            _, root = next(context)
            for event, node in context:
                if event != "end" or local_name(node.tag) != "BizGrp":
                    continue
                scanned += 1
                document = child(node, "Document", "Instrm")
                report_date = value(document, "RptParams", "RptDtAndTm", "Dt")
                if report_date:
                    dates.add(report_date)
                common = child(document, "FinInstrmAttrCmon")
                if value(common, "Sgmt") != "1" or value(common, "Mkt") != "10":
                    root.clear()
                    continue
                equity = child(document, "InstrmInf", "EqtyInf")
                ticker = value(equity, "TckrSymb").upper()
                if ticker:
                    kind, detail = classify(value(equity, "SctyCtgy"), value(common, "Desc"), value(equity, "CFICd"))
                    evidence.append({"ticker": ticker, "source_date": report_date, "source": "BVBG.028.02",
                                     "instrument_type": kind, "isin": value(equity, "ISIN"), "detail": detail,
                                     "file": path.name, "file_sha256": ""})
                root.clear()
        if len(dates) != 1:
            raise ClassificationError(f"{path.name}: esperado um único RptDt, recebido {sorted(dates)!r}")
        report_date = date.fromisoformat(next(iter(dates)))
        for item in evidence:
            item["file_sha256"] = file_hash
        info = {"file": path.name, "sha256": file_hash, "source": "BVBG.028.02",
                "payload_sha256": payload_hash,
                "source_date": report_date.isoformat(), "xml_member": xml_name, "rows_scanned": scanned}
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = cache_path.with_suffix(".tmp")
            temporary.write_text(json.dumps({"info": info, "evidence": evidence}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            temporary.replace(cache_path)
        selected = [item for item in evidence if item["ticker"] in requested]
        return selected, {**info, "matched_rows": len(selected)}
    except (OSError, zipfile.BadZipFile, ET.ParseError, RegistryError) as exc:
        raise ClassificationError(f"Não foi possível ler cadastro B3 {path}: {exc}") from exc
    finally:
        if nested is not None and nested is not outer:
            nested.close()
        if outer is not None:
            outer.close()


def cotahist_type(specification: str) -> str:
    specification = specification.upper().strip()
    if specification.startswith("ON"):
        return "acao_on"
    if specification.startswith("PN"):
        return "acao_pn"
    if specification.startswith("UNT"):
        return "unit"
    if specification.startswith(("DR", "BDR")):
        return "bdr"
    return "nao_resolvido"


def read_cotahist(path: Path, requested: set[str]) -> tuple[list[dict], dict]:
    """Lê o TXT diário conforme layout COTAHIST (campos em posições fixas)."""
    try:
        evidence, dates = [], set()
        with zipfile.ZipFile(path) as archive:
            members = [name for name in archive.namelist() if name.upper().endswith(".TXT")]
            if len(members) != 1:
                raise ClassificationError(f"{path.name}: esperado um TXT COTAHIST no ZIP")
            with archive.open(members[0]) as stream:
                for line_number, raw in enumerate(stream, start=1):
                    line = raw.decode("cp1252").rstrip("\r\n")
                    if not line.startswith("01"):
                        continue
                    if len(line) < 242:
                        raise ClassificationError(f"{path.name}: linha {line_number} menor que o layout COTAHIST")
                    trading_date = date(int(line[2:6]), int(line[6:8]), int(line[8:10]))
                    dates.add(trading_date)
                    if line[24:27] != "010":
                        continue
                    ticker = line[12:24].strip().upper()
                    if ticker not in requested:
                        continue
                    specification = line[39:49].strip()
                    evidence.append({"ticker": ticker, "source_date": trading_date.isoformat(), "source": "COTAHIST",
                                     "instrument_type": cotahist_type(specification), "isin": line[230:242].strip(),
                                     "detail": f"TPMERC=010; ESPECI={specification}", "file": path.name, "file_sha256": ""})
        if len(dates) != 1:
            raise ClassificationError(f"{path.name}: esperado COTAHIST diário, encontradas {len(dates)} datas")
        file_hash = digest(path)
        for item in evidence:
            item["file_sha256"] = file_hash
        return evidence, {"file": path.name, "sha256": file_hash, "source": "COTAHIST",
                          "source_date": next(iter(dates)).isoformat(), "txt_member": members[0], "matched_rows": len(evidence)}
    except (OSError, zipfile.BadZipFile, UnicodeError, ValueError) as exc:
        if isinstance(exc, ClassificationError):
            raise
        raise ClassificationError(f"Não foi possível ler COTAHIST {path}: {exc}") from exc


def candidate_prices(path: Path, start: date, end: date) -> tuple[dict[str, dict[str, str]], set[str], list[dict]]:
    if start >= end:
        raise ClassificationError("A data inicial precisa ser anterior à final.")
    rows = defaultdict(lambda: defaultdict(list))
    all_tickers = set()
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            required = {"ticker", "trade_date", "close", "parse_status"}
            if not required.issubset(set(reader.fieldnames or [])):
                raise ClassificationError(f"normalized.csv requer {sorted(required)}")
            for row in reader:
                if row["ticker"]:
                    all_tickers.add(row["ticker"])
                if row["trade_date"] in (start.isoformat(), end.isoformat()) and row["ticker"]:
                    rows[row["ticker"]][row["trade_date"]].append(row)
    except OSError as exc:
        raise ClassificationError(f"Não foi possível ler {path}: {exc}") from exc
    candidates, duplicates, exclusions = {}, set(), []
    def valid_positive(row: dict) -> bool:
        try:
            return row["parse_status"] == "ok" and Decimal(row["close"]) > 0
        except (InvalidOperation, ValueError):
            return False

    for ticker in sorted(all_tickers):
        by_date = rows[ticker]
        first, last = by_date[start.isoformat()], by_date[end.isoformat()]
        if not first or not last:
            exclusions.append({"ticker": ticker, "start_date_rows": len(first), "end_date_rows": len(last),
                               "reason": "Ausência de linha em uma ou ambas as datas"})
            continue
        positive = all(any(valid_positive(r) for r in group) for group in (first, last))
        if not positive:
            exclusions.append({"ticker": ticker, "start_date_rows": len(first), "end_date_rows": len(last),
                               "reason": "Sem fechamento positivo válido em uma ou ambas as datas"})
            continue
        if len(first) != 1 or len(last) != 1:
            duplicates.add(ticker)
        candidates[ticker] = {start.isoformat(): first[0]["close"], end.isoformat(): last[0]["close"]}
    return candidates, duplicates, exclusions


def resolve_at(ticker: str, day: date, evidence: list[dict]) -> tuple[str, str, str, str, str]:
    same_day = [e for e in evidence if e["ticker"] == ticker and e["source"] == "COTAHIST" and e["source_date"] == day.isoformat()]
    same_day_xml = [e for e in evidence if e["ticker"] == ticker and e["source"] == "BVBG.028.02" and e["source_date"] == day.isoformat()]
    observed = same_day + same_day_xml
    if not observed:
        return "unresolved", "", "", "", "Sem evidência B3 na data exata do preço"
    known = [e for e in observed if e["instrument_type"] not in ("nao_resolvido", "categoria_oficial_nao_mapeada")]
    types = {e["instrument_type"] for e in known}
    isins = {e["isin"] for e in observed if e["isin"]}
    sources = "; ".join(sorted({f"{e['source']}:{e['source_date']}:{e['file']}" for e in observed}))
    if len(isins) > 1:
        return "conflict", "", " | ".join(sorted(isins)), sources, "ISIN divergente para o mesmo ticker"
    if any(e["source"] == "BVBG.028.02" and e["instrument_type"] in ("nao_resolvido", "categoria_oficial_nao_mapeada") for e in observed):
        return "unresolved", "", next(iter(isins), ""), sources, "Categoria do cadastro B3 não interpretável"
    if not types:
        return "unresolved", "", next(iter(isins), ""), sources, "Fontes presentes, mas espécie não interpretável"
    if types in ({"acao", "acao_on"}, {"acao", "acao_pn"}):
        types.remove("acao")
    if len(types) != 1:
        return "conflict", " | ".join(sorted(types)), next(iter(isins), ""), sources, "Tipos oficiais divergentes"
    kind = next(iter(types))
    if kind == "acao":
        return "unresolved", "", next(iter(isins), ""), sources, "Ação sem espécie ON/PN confirmada"
    return "confirmed", kind, next(iter(isins), ""), sources, ""


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(normalized: Path, start: date, end: date, output_dir: Path, b3_files: list[Path],
        cotahist_files: list[Path], cache_dir: Path | None = None) -> dict:
    candidates, duplicates, exclusions = candidate_prices(normalized, start, end)
    tickers = set(candidates)
    evidence, files = [], []
    if cache_dir is None:
        cache_dir = output_dir.parent / "reference_cache"
    for path in sorted(set(b3_files), key=str):
        records, info = read_bvbg(path, tickers, cache_dir)
        if date.fromisoformat(info["source_date"]) > end:
            raise ClassificationError(f"{path.name}: snapshot posterior à data final {end}")
        evidence.extend(records)
        files.append(info)
    for path in sorted(set(cotahist_files), key=str):
        records, info = read_cotahist(path, tickers)
        if date.fromisoformat(info["source_date"]) > end:
            raise ClassificationError(f"{path.name}: COTAHIST posterior à data final {end}")
        evidence.extend(records)
        files.append(info)
    evidence.sort(key=lambda e: (e["ticker"], e["source_date"], e["source"], e["isin"], e["file"]))
    results = []
    for ticker in sorted(tickers):
        pair = []
        for day in (start, end):
            status, kind, isin, sources, reason = resolve_at(ticker, day, evidence)
            if ticker in duplicates:
                status, reason = "conflict", "Chave ticker/data duplicada na extração; revisar preços antes do ranking"
            row = {"ticker": ticker, "price_date": day.isoformat(), "close": candidates[ticker][day.isoformat()],
                   "status": status, "instrument_type": kind, "isin": isin, "evidence_sources": sources, "reason": reason}
            pair.append(row)
        if all(row["status"] == "confirmed" for row in pair):
            if pair[0]["instrument_type"] != pair[1]["instrument_type"] or (pair[0]["isin"] and pair[1]["isin"] and pair[0]["isin"] != pair[1]["isin"]):
                for row in pair:
                    row["status"] = "conflict"
                    row["reason"] = "Tipo ou ISIN mudou entre as datas de preço; revisão necessária"
        results.extend(pair)
    blocked = sorted({r["ticker"] for r in results if r["status"] != "confirmed"})
    summary = {"start_date": start.isoformat(), "end_date": end.isoformat(),
               "candidate_definition": "ticker com fechamento positivo nas duas datas explícitas",
               "candidate_tickers": len(candidates), "excluded_before_classification": len(exclusions),
               "confirmed_tickers": len(candidates) - len(blocked),
               "blocked_tickers": blocked, "status_counts": dict(sorted(Counter(r["status"] for r in results).items())),
               "classification_gate_passed": bool(candidates) and not blocked,
               "note": "Classificação confirmada não define elegibilidade de ON, PN, unit, BDR ou ETF."}
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "period_classification.csv", RESULT_COLUMNS, results)
    write_csv(output_dir / "b3_evidence.csv", EVIDENCE_COLUMNS, evidence)
    write_csv(output_dir / "candidate_exclusions.csv", EXCLUSION_COLUMNS, exclusions)
    (output_dir / "classification_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {"version": VERSION, "code_sha256": digest(Path(__file__)),
                "b3_registry_code_sha256": digest(Path(b3_registry.__file__)),
                "normalized_file": normalized.name, "normalized_sha256": digest(normalized),
                "source_files": files,
                "outputs": {name: digest(output_dir / name) for name in
                            ("period_classification.csv", "b3_evidence.csv", "candidate_exclusions.csv", "classification_summary.json")}}
    (output_dir / "classification_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--normalized", type=Path, required=True)
    parser.add_argument("--start-date", type=date.fromisoformat, required=True)
    parser.add_argument("--end-date", type=date.fromisoformat, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--b3-file", type=Path, action="append", default=[])
    parser.add_argument("--cotahist-file", type=Path, action="append", default=[])
    parser.add_argument("--cache-dir", type=Path, help="Cache compartilhado dos cadastros B3 parseados")
    args = parser.parse_args()
    try:
        summary = run(args.normalized, args.start_date, args.end_date, args.output_dir,
                      args.b3_file, args.cotahist_file, args.cache_dir)
    except (ClassificationError, OSError) as exc:
        parser.exit(2, f"Erro: {exc}\n")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["classification_gate_passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
