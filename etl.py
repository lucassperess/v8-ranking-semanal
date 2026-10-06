"""Tratamento auditável da extração diária da Economatica (sem ranking)."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from b3_registry import RegistryError, load_bvbg
import b3_registry


VERSION = "1.2.0"
SOURCE_COLUMNS = [
    "Ativo",
    "Data",
    "Fechamento|ajust p/ prov|Em moeda orig",
    "Q T\u00edts|ajust p/ prov",
    "Abertura|ajust p/ prov|Em moeda orig",
    "M\u00e1ximo|ajust p/ prov|Em moeda orig",
    "M\u00ednimo|ajust p/ prov|Em moeda orig",
    "M\u00e9dio|ajust p/ prov|Em moeda orig",
    "Volume$|Em moeda orig",
]
NUMERIC_FIELDS = ["close", "adjusted_quantity", "open", "high", "low", "average", "raw_volume"]
NORMALIZED_COLUMNS = [
    "record_id", "source_line", "ativo_original", "data_original", "ticker", "exchange",
    "trade_date", *NUMERIC_FIELDS, "instrument_type", "classification_source",
    "classification_detail", "raw_fields_json", "parse_status",
]
ISSUE_COLUMNS = ["record_id", "source_line", "ticker", "trade_date", "field", "code", "severity", "reason"]
TICKER_RE = re.compile(r"^(?P<ticker>[A-Z0-9]+)(?:<(?P<exchange>[A-Z0-9]+)>)?$")


class InputError(Exception):
    """Estrutura global que impede interpretação confiável."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode_file(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            pass
    raise InputError("Codificação não reconhecida: esperado UTF-8 ou Windows-1252.")


def parse_csv_line(line: str, delimiter: str = ",") -> list[str]:
    try:
        row = next(csv.reader([line], delimiter=delimiter, strict=True))
    except csv.Error as exc:
        raise ValueError(str(exc)) from exc
    return row


def read_economatica(path: Path) -> tuple[list[dict], str]:
    decoded, encoding = decode_file(path)
    lines = decoded.splitlines()
    if not lines:
        raise InputError("CSV vazio.")
    try:
        header = parse_csv_line(lines[0])
    except ValueError as exc:
        raise InputError(f"Cabeçalho inválido: {exc}") from exc
    if header != SOURCE_COLUMNS:
        raise InputError(
            "Esquema inesperado; nenhuma coluna será interpretada por posição. "
            f"Esperado: {SOURCE_COLUMNS!r}; recebido: {header!r}."
        )
    output = []
    for line_number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            output.append({"line": line_number, "fields": None, "raw": line, "error": "Linha vazia"})
            continue
        try:
            fields = parse_csv_line(line)
            error = None if len(fields) == len(SOURCE_COLUMNS) else f"Esperadas 9 colunas; recebidas {len(fields)}"
        except ValueError as exc:
            fields, error = None, str(exc)
        output.append({"line": line_number, "fields": fields, "raw": line, "error": error})
    return output, encoding


def parse_number(value: str) -> tuple[Decimal | None, str | None]:
    if value.strip() in ("", "-"):
        return None, None
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", value.strip()):
        return None, "Número incompatível com ponto decimal"
    try:
        number = Decimal(value.strip())
    except InvalidOperation:
        return None, "Número inválido"
    if not number.is_finite():
        return None, "Número não finito"
    return number, None


def parse_ticker(value: str) -> tuple[str, str, str | None]:
    matched = TICKER_RE.fullmatch(value.strip().upper())
    if not matched:
        return "", "", "Código de ativo inválido"
    return matched.group("ticker"), matched.group("exchange") or "", None


def provisional_type(ticker: str) -> tuple[str, str]:
    if re.fullmatch(r"[A-Z]{4}[3-8]", ticker):
        return "acao_provisoria", "Padrão do código; confirmar em fonte oficial"
    if re.fullmatch(r"[A-Z]{4}11", ticker):
        return "ambiguo", "Final 11 pode representar instrumentos distintos"
    if re.fullmatch(r"[A-Z]{4}3[23]", ticker):
        return "bdr_provisorio", "Padrão do código; confirmar em fonte oficial"
    return "nao_resolvido", "Padrão do código insuficiente"


def official_type(description: str) -> str:
    value = description.casefold()
    if "bdr" in value or "depositary receipt" in value:
        return "bdr"
    if "etf" in value or "exchange traded fund" in value:
        return "etf"
    if "fii" in value or "fundo imobili" in value:
        return "fii"
    if "unit" in value:
        return "unit"
    if "aç" in value or "acoes" in value or "shares" in value or "equity" in value:
        return "acao"
    return "categoria_oficial_nao_mapeada"


def load_registry(path: Path | None, reference_date: date, snapshot_date: date | None) -> tuple[dict, dict]:
    if path is None:
        return {}, {"used": False}
    content, encoding = decode_file(path)
    try:
        dialect = csv.Sniffer().sniff(content[:8192], delimiters=",;")
        delimiter = dialect.delimiter
    except csv.Error as exc:
        raise InputError("Não foi possível identificar separador do cadastro B3 (vírgula ou ponto e vírgula).") from exc
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    cols = reader.fieldnames or []
    ticker_col = next((c for c in ("TckrSymb", "TickerSymbol", "ticker") if c in cols), None)
    category_col = next((c for c in ("SctyCtgyNm", "SecurityCategoryName", "category") if c in cols), None)
    report_col = next((c for c in ("RptDt", "ReportDate") if c in cols), None)
    if not ticker_col or not category_col:
        raise InputError("Cadastro B3 requer TckrSymb/TickerSymbol/ticker e SctyCtgyNm/SecurityCategoryName/category.")
    registry = defaultdict(set)
    dates = set()
    rows = 0
    for row in reader:
        rows += 1
        if None in row:
            raise InputError(f"Linha {reader.line_num} do cadastro B3 tem colunas excedentes.")
        if report_col and row.get(report_col):
            try:
                dates.add(date.fromisoformat(row[report_col]))
            except ValueError as exc:
                raise InputError(f"Data inválida no cadastro B3, linha {reader.line_num}.") from exc
        ticker = (row[ticker_col] or "").strip().upper()
        if ticker:
            registry[ticker].add((row[category_col] or "").strip())
    if report_col and len(dates) > 1:
        raise InputError("Cadastro B3 contém múltiplas datas de referência; forneça um único snapshot.")
    embedded_date = next(iter(dates), None)
    if snapshot_date and embedded_date and snapshot_date != embedded_date:
        raise InputError("--b3-snapshot-date diverge de RptDt/ReportDate do cadastro.")
    effective_date = embedded_date or snapshot_date
    if effective_date is None:
        raise InputError("Cadastro sem RptDt/ReportDate: informe --b3-snapshot-date.")
    if effective_date > reference_date:
        raise InputError("Cadastro B3 posterior à data de referência; isso introduziria viés temporal.")
    resolved = {}
    for ticker, descriptions in registry.items():
        mapped = {(official_type(desc), desc) for desc in descriptions if desc}
        types = {kind for kind, _ in mapped}
        if len(types) == 1:
            resolved[ticker] = (next(iter(types)), " | ".join(sorted(descriptions)))
        else:
            resolved[ticker] = ("nao_resolvido", "Categorias B3 ausentes ou conflitantes: " + " | ".join(sorted(descriptions)))
    info = {
        "used": True, "filename": path.name, "sha256": sha256(path), "encoding": encoding,
        "snapshot_date": effective_date.isoformat(), "rows": rows, "unique_tickers": len(resolved),
        "stale_over_7_days": (reference_date - effective_date).days > 7,
    }
    return resolved, info


def load_overrides(path: Path | None) -> tuple[dict, dict]:
    if path is None:
        return {}, {"used": False}
    content, encoding = decode_file(path)
    reader = csv.DictReader(io.StringIO(content))
    expected = ["ticker", "category", "source_url", "approved_by", "approved_at", "reason"]
    if reader.fieldnames != expected:
        raise InputError(f"Mapeamento manual requer colunas, nesta ordem: {expected!r}.")
    overrides = {}
    for row in reader:
        if None in row or any(not (row[field] or "").strip() for field in expected):
            raise InputError(f"Mapeamento manual incompleto na linha {reader.line_num}.")
        ticker = row["ticker"].strip().upper()
        if not TICKER_RE.fullmatch(ticker) or "<" in ticker:
            raise InputError(f"Ticker inválido no mapeamento manual, linha {reader.line_num}.")
        if ticker in overrides:
            raise InputError(f"Ticker duplicado no mapeamento manual: {ticker}.")
        if not row["source_url"].startswith("https://"):
            raise InputError(f"Fonte deve ser URL HTTPS na linha {reader.line_num}.")
        try:
            date.fromisoformat(row["approved_at"])
        except ValueError as exc:
            raise InputError(f"Data de aprovação inválida na linha {reader.line_num}.") from exc
        overrides[ticker] = {key: row[key].strip() for key in expected}
    return overrides, {"used": True, "filename": path.name, "sha256": sha256(path), "encoding": encoding, "rows": len(overrides)}


def add_issue(issues: list[dict], record: dict, field: str, code: str, severity: str, reason: str) -> None:
    issues.append({
        "record_id": record["record_id"], "source_line": record["source_line"],
        "ticker": record["ticker"], "trade_date": record["trade_date"],
        "field": field, "code": code, "severity": severity, "reason": reason,
    })


def transform(raw_rows: list[dict], reference_date: date, registry: dict, coverage_drop: Decimal,
              registry_used: bool = False, overrides: dict | None = None,
              registry_snapshot_date: date | None = None) -> tuple[list[dict], list[dict], dict]:
    overrides = overrides or {}
    records, issues = [], []
    key_groups = defaultdict(list)
    per_date = defaultdict(lambda: {"rows": 0, "positive_close": 0, "missing_close": 0, "tickers": set()})
    for record_id, raw in enumerate(raw_rows, start=1):
        fields = raw["fields"]
        record = {key: "" for key in NORMALIZED_COLUMNS}
        record.update({
            "record_id": record_id, "source_line": raw["line"], "parse_status": "ok" if raw["error"] is None else "invalid",
            "raw_fields_json": json.dumps(fields if fields is not None else raw["raw"], ensure_ascii=False, separators=(",", ":")),
        })
        if fields:
            record["ativo_original"], record["data_original"] = fields[:2]
            record["ticker"], record["exchange"], ticker_error = parse_ticker(fields[0])
            if ticker_error:
                add_issue(issues, record, "Ativo", "INVALID_TICKER", "error", ticker_error)
            try:
                parsed_date = date.fromisoformat(fields[1])
                if parsed_date.isoformat() != fields[1]:
                    raise ValueError("Formato não canônico")
                record["trade_date"] = parsed_date.isoformat()
                if parsed_date > reference_date:
                    add_issue(issues, record, "Data", "FUTURE_DATE", "error", "Data posterior à referência")
            except ValueError:
                add_issue(issues, record, "Data", "INVALID_DATE", "error", "Esperado AAAA-MM-DD válido")
            for field, value in zip(NUMERIC_FIELDS, fields[2:]):
                parsed, error = parse_number(value)
                record[field] = "" if parsed is None else str(parsed)
                if error:
                    add_issue(issues, record, field, "INVALID_NUMBER", "error", f"{error}: {value!r}")
                elif parsed is None:
                    add_issue(issues, record, field, "MISSING_VALUE", "info", "Valor ausente na extração")
            if record["ticker"]:
                trade_date = date.fromisoformat(record["trade_date"]) if record["trade_date"] else None
                if registry_used and trade_date and registry_snapshot_date and trade_date < registry_snapshot_date:
                    record.update(instrument_type="nao_resolvido", classification_source="snapshot_posterior",
                                  classification_detail=f"Cadastro B3 de {registry_snapshot_date} posterior à linha de {trade_date}; consultar evidência histórica")
                    add_issue(issues, record, "Ativo", "B3_SNAPSHOT_AFTER_TRADE_DATE", "warning",
                              "Cadastro posterior à data da linha; classificação histórica não inferida")
                elif record["ticker"] in registry and registry[record["ticker"]][0] not in ("nao_resolvido", "categoria_oficial_nao_mapeada"):
                    kind, detail = registry[record["ticker"]]
                    record.update(instrument_type=kind, classification_source="b3", classification_detail=detail)
                elif record["ticker"] in overrides:
                    override = overrides[record["ticker"]]
                    record.update(instrument_type=override["category"], classification_source="manual_approved",
                                  classification_detail=f"{override['source_url']} | {override['approved_by']} | {override['approved_at']} | {override['reason']}")
                elif record["ticker"] in registry:
                    kind, detail = registry[record["ticker"]]
                    record.update(instrument_type=kind, classification_source="b3", classification_detail=detail)
                    add_issue(issues, record, "Ativo", "B3_CATEGORY_UNRESOLVED", "warning", detail)
                else:
                    kind, detail = provisional_type(record["ticker"])
                    record.update(instrument_type=kind, classification_source="codigo_provisorio", classification_detail=detail)
                    if registry_used:
                        add_issue(issues, record, "Ativo", "B3_TICKER_UNMATCHED", "warning", "Código ausente no snapshot B3; registro preservado")
                    if kind in ("ambiguo", "nao_resolvido"):
                        add_issue(issues, record, "Ativo", "INSTRUMENT_AMBIGUOUS", "warning", detail)
            if record["ticker"] and record["trade_date"]:
                key_groups[(record["ticker"], record["exchange"], record["trade_date"])].append((record, tuple(fields)))
            if record["trade_date"]:
                bucket = per_date[record["trade_date"]]
                bucket["rows"] += 1
                if record["ticker"]:
                    bucket["tickers"].add(record["ticker"])
                if record["close"] and Decimal(record["close"]) > 0:
                    bucket["positive_close"] += 1
                elif not record["close"]:
                    bucket["missing_close"] += 1
            numeric = {field: Decimal(record[field]) if record[field] else None for field in NUMERIC_FIELDS}
            for field in ("close", "open", "high", "low", "average"):
                if numeric[field] is not None and numeric[field] <= 0:
                    add_issue(issues, record, field, "NONPOSITIVE_PRICE", "error", "Preço deve ser positivo")
            for field in ("adjusted_quantity", "raw_volume"):
                if numeric[field] is not None and numeric[field] < 0:
                    add_issue(issues, record, field, "NEGATIVE_AMOUNT", "error", "Quantidade ou volume negativo")
            low, high = numeric["low"], numeric["high"]
            if low is not None and high is not None:
                if low > high:
                    add_issue(issues, record, "low/high", "LOW_ABOVE_HIGH", "error", "Mínimo acima do máximo")
                else:
                    for field in ("open", "close", "average"):
                        value = numeric[field]
                        if value is not None and (value < low or value > high):
                            add_issue(issues, record, field, "OUTSIDE_DAILY_RANGE", "warning", "Valor fora do intervalo mínimo–máximo")
            quantity, average, volume = numeric["adjusted_quantity"], numeric["average"], numeric["raw_volume"]
            if quantity and average and volume is not None:
                estimated = quantity * average
                if estimated and abs(volume - estimated) > 1 and abs(volume - estimated) / abs(estimated) > Decimal("0.10"):
                    add_issue(issues, record, "raw_volume", "VOLUME_PRICE_DIVERGENCE", "info", "Volume bruto difere mais de 10% de quantidade ajustada × preço médio ajustado; bases de ajuste podem diferir")
        if raw["error"]:
            add_issue(issues, record, "_row", "MALFORMED_ROW", "error", raw["error"])
        records.append(record)
    for _, items in key_groups.items():
        if len(items) > 1:
            code = "DUPLICATE_EXACT" if len({raw for _, raw in items}) == 1 else "DUPLICATE_CONFLICT"
            for record, _ in items:
                add_issue(issues, record, "Ativo+Data", code, "error", f"Chave repetida em {len(items)} registros")
    date_rows = []
    previous = None
    for iso_date, bucket in sorted(per_date.items()):
        row = {"date": iso_date, "rows": bucket["rows"], "distinct_tickers": len(bucket["tickers"]), "positive_close": bucket["positive_close"], "missing_close": bucket["missing_close"], "coverage_drop_vs_previous": ""}
        current_date = date.fromisoformat(iso_date)
        if previous and (reference_date - current_date).days <= 30 and previous["positive_close"] >= 50:
            drop = Decimal(previous["positive_close"] - row["positive_close"]) / Decimal(previous["positive_close"])
            if drop > coverage_drop:
                row["coverage_drop_vs_previous"] = f"{drop:.4f}"
                issues.append({"record_id": "", "source_line": "", "ticker": "", "trade_date": iso_date, "field": "positive_close", "code": "COVERAGE_DROP", "severity": "warning", "reason": f"Queda de {drop:.2%} frente à data anterior presente no arquivo; verificar calendário e extração"})
        previous = row
        date_rows.append(row)
        if row["rows"] and row["positive_close"] == 0 and 0 <= (reference_date - current_date).days <= 30:
            issues.append({"record_id": "", "source_line": "", "ticker": "", "trade_date": iso_date, "field": "close", "code": "DATE_WITHOUT_QUOTES", "severity": "info", "reason": "Há linhas na data, mas nenhum fechamento positivo; verificar calendário, suspensão ou extração"})
    summary = {
        "rows_input": len(raw_rows), "rows_output": len(records),
        "distinct_tickers": len({r["ticker"] for r in records if r["ticker"]}),
        "missing_close": sum(not r["close"] for r in records),
        "records_on_1920_01_02": sum(r["trade_date"] == "1920-01-02" for r in records),
        "quantity_and_volume_without_any_price": sum(
            bool(r["adjusted_quantity"] and r["raw_volume"])
            and all(not r[p] for p in ("close", "open", "high", "low", "average"))
            for r in records
        ),
        "issue_counts": dict(sorted(Counter(i["code"] for i in issues).items())),
        "issue_severity_counts": dict(sorted(Counter(i["severity"] for i in issues).items())),
        "dates": date_rows,
    }
    return records, issues, summary


def compare_baseline(summary: dict, issues: list[dict], baseline_path: Path | None,
                     threshold: Decimal) -> dict:
    if baseline_path is None:
        return {"used": False}
    try:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        prior = max((item for item in baseline["dates"] if item["positive_close"] > 0), key=lambda item: item["date"])
        current = max((item for item in summary["dates"] if item["positive_close"] > 0), key=lambda item: item["date"])
        previous_count = int(prior["positive_close"])
        current_count = int(current["positive_close"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise InputError("Resumo anterior inválido: esperado quality_summary.json com datas e positive_close.") from exc
    drop = Decimal(previous_count - current_count) / Decimal(previous_count)
    if drop > threshold:
        issues.append({"record_id": "", "source_line": "", "ticker": "", "trade_date": current["date"], "field": "positive_close", "code": "EXTRACTION_COVERAGE_DROP", "severity": "warning", "reason": f"Última data com fechamento: {current_count} ativos; anterior {previous_count} em {prior['date']}; queda {drop:.2%}"})
    summary["issue_counts"] = dict(sorted(Counter(i["code"] for i in issues).items()))
    summary["issue_severity_counts"] = dict(sorted(Counter(i["severity"] for i in issues).items()))
    return {"used": True, "filename": baseline_path.name, "sha256": sha256(baseline_path), "baseline_latest_quote_date": prior["date"], "baseline_latest_positive_close": previous_count, "current_latest_quote_date": current["date"], "current_latest_positive_close": current_count}


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(input_path: Path, reference_date: date, output_dir: Path, b3_path: Path | None = None,
        b3_snapshot_date: date | None = None, coverage_drop: Decimal = Decimal("0.25"),
        overrides_path: Path | None = None, baseline_summary: Path | None = None) -> dict:
    if not input_path.is_file():
        raise InputError(f"CSV não encontrado: {input_path}")
    if not Decimal("0") <= coverage_drop <= Decimal("1"):
        raise InputError("--coverage-drop deve estar entre 0 e 1.")
    rows, encoding = read_economatica(input_path)
    requested_tickers = {
        parse_ticker(row["fields"][0])[0]
        for row in rows if row["fields"] and row["fields"][0]
    } - {""}
    if b3_path is not None and b3_path.suffix.lower() == ".zip":
        try:
            registry, b3_info = load_bvbg(b3_path, reference_date, requested_tickers, b3_snapshot_date)
        except RegistryError as exc:
            raise InputError(str(exc)) from exc
    else:
        registry, b3_info = load_registry(b3_path, reference_date, b3_snapshot_date)
    overrides, overrides_info = load_overrides(overrides_path)
    snapshot_date = date.fromisoformat(b3_info["snapshot_date"]) if b3_info.get("snapshot_date") else None
    records, issues, summary = transform(rows, reference_date, registry, coverage_drop, b3_info["used"], overrides, snapshot_date)
    if b3_info.get("stale_over_7_days"):
        issues.append({"record_id": "", "source_line": "", "ticker": "", "trade_date": "", "field": "b3_registry", "code": "B3_STALE_SNAPSHOT", "severity": "warning", "reason": "Cadastro B3 tem mais de sete dias frente à data de referência; códigos recentes podem não aparecer"})
    baseline_info = compare_baseline(summary, issues, baseline_summary, coverage_drop)
    summary["issue_counts"] = dict(sorted(Counter(i["code"] for i in issues).items()))
    summary["issue_severity_counts"] = dict(sorted(Counter(i["severity"] for i in issues).items()))
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_copy = output_dir / "economatica_original.csv"
    if input_path.resolve() != raw_copy.resolve():
        shutil.copyfile(input_path, raw_copy)
    if sha256(raw_copy) != sha256(input_path):
        raise InputError("Falha na preservação do arquivo bruto: hash divergente.")
    write_csv(output_dir / "normalized.csv", NORMALIZED_COLUMNS, records)
    write_csv(output_dir / "quality_issues.csv", ISSUE_COLUMNS, issues)
    write_csv(output_dir / "quality_by_date.csv", ["date", "rows", "distinct_tickers", "positive_close", "missing_close", "coverage_drop_vs_previous"], summary["dates"])
    (output_dir / "quality_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "etl_version": VERSION, "code_sha256": sha256(Path(__file__)),
        "b3_parser_sha256": sha256(Path(b3_registry.__file__)) if b3_info["used"] and b3_info.get("format") == "BVBG.028.02_XML" else None,
        "input_filename": input_path.name, "input_sha256": sha256(input_path),
        "input_encoding": encoding, "reference_date": reference_date.isoformat(),
        "coverage_drop_threshold": str(coverage_drop), "b3_registry": b3_info,
        "manual_overrides": overrides_info, "baseline_summary": baseline_info,
        "rows_input": len(rows), "rows_output": len(records),
        "outputs": {name: sha256(output_dir / name) for name in ("normalized.csv", "quality_issues.csv", "quality_by_date.csv", "quality_summary.json")},
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="CSV original da Economatica")
    parser.add_argument("--reference-date", type=date.fromisoformat, required=True, help="AAAA-MM-DD; apenas diagnóstico")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--b3-registry", type=Path, help="ZIP oficial BVBG.028.02 da B3 (ou CSV de cadastro validado)")
    parser.add_argument("--b3-snapshot-date", type=date.fromisoformat, help="AAAA-MM-DD se o cadastro não tiver RptDt")
    parser.add_argument("--overrides", type=Path, help="CSV versionado de classificações aprovadas manualmente")
    parser.add_argument("--baseline-summary", type=Path, help="quality_summary.json de extração anterior para comparar cobertura")
    parser.add_argument("--coverage-drop", type=Decimal, default=Decimal("0.25"), help="Fração de queda que aciona alerta (padrão: 0.25)")
    args = parser.parse_args()
    try:
        manifest = run(args.input, args.reference_date, args.output_dir, args.b3_registry, args.b3_snapshot_date, args.coverage_drop, args.overrides, args.baseline_summary)
    except (InputError, OSError) as exc:
        parser.exit(2, f"Erro de entrada: {exc}\n")
    print(json.dumps({"output_dir": str(args.output_dir), "rows": manifest["rows_output"], "input_sha256": manifest["input_sha256"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
