"""Adaptador de saídas auditadas do pipeline para a interface pública.

Retornos e média vêm exclusivamente de weekly_ranking.py. As séries diárias
são contexto visual: nunca alteram o universo nem a ordenação do ranking.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from b3_registry import digest


DOWNLOADS = {
    "top20.csv": ("principal", "top20.csv"),
    "all_returns.csv": ("principal", "all_returns.csv"),
    "top20_alternativo.csv": ("alternativa", "top20.csv"),
    "all_returns_alternativo.csv": ("alternativa", "all_returns.csv"),
    "quality_context.json": ("principal", "quality_context.json"),
    "candidate_exclusions.csv": ("classification", "candidate_exclusions.csv"),
    "ranking_report.json": ("root", "ranking_report.json"),
    "README.md": ("root", "README.md"),
}


def output_path(root: Path, name: str, *, featured: bool = False) -> Path:
    if name not in DOWNLOADS:
        raise KeyError(name)
    group, filename = DOWNLOADS[name]
    if featured:
        return root / name
    if group == "root":
        return root / filename
    if group == "classification":
        return root / "classification" / "principal" / filename
    return root / "rankings" / group / filename


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _decimal(raw: str | None) -> Decimal | None:
    try:
        value = Decimal(raw or "")
        return value if value.is_finite() else None
    except InvalidOperation:
        return None


def daily_context(normalized_path: Path, tickers: set[str], baseline: str, end: str) -> dict:
    """Preços observados e retornos entre pregões consecutivos, sem imputação."""
    selected: dict[tuple[str, str], Decimal] = {}
    conflicting: set[tuple[str, str]] = set()
    dates: set[str] = set()
    with normalized_path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            day = row.get("trade_date", "")
            if not day or not baseline <= day <= end:
                continue
            dates.add(day)
            ticker = row.get("ticker", "")
            if ticker not in tickers or row.get("parse_status") != "ok":
                continue
            price = _decimal(row.get("close"))
            if price is None or price <= 0:
                continue
            key = ticker, day
            if key in selected:
                conflicting.add(key)
            else:
                selected[key] = price
    ordered_dates = sorted(dates)
    if baseline not in ordered_dates:
        ordered_dates.insert(0, baseline)
    if end not in ordered_dates:
        ordered_dates.append(end)
    series = {}
    heatmap = {}
    for ticker in sorted(tickers):
        points = []
        changes = []
        for index, day in enumerate(ordered_dates):
            key = ticker, day
            price = None if key in conflicting else selected.get(key)
            points.append({"date": day, "close": str(price) if price is not None else None})
            if index:
                prior_key = ticker, ordered_dates[index - 1]
                prior = None if prior_key in conflicting else selected.get(prior_key)
                change = (price / prior - 1) * 100 if price is not None and prior is not None else None
                changes.append({"date": day, "return_pct": str(change) if change is not None else None})
        series[ticker] = points
        heatmap[ticker] = changes
    return {"dates": ordered_dates, "series": series, "heatmap": heatmap,
            "note": "Variação diária entre datas consecutivas da extração; célula vazia indica preço ausente ou conflitante."}


def _distribution(rows: list[dict[str, str]]) -> dict:
    buckets = [("< -20%", None, Decimal("-20")),
               ("-20 a -10%", Decimal("-20"), Decimal("-10")),
               ("-10 a 0%", Decimal("-10"), Decimal("0")),
               ("0 a 10%", Decimal("0"), Decimal("10")),
               ("10 a 20%", Decimal("10"), Decimal("20")),
               (">= 20%", Decimal("20"), None)]
    result = Counter()
    up = down = flat = 0
    for row in rows:
        value = Decimal(row["return_pct"])
        up += value > 0
        down += value < 0
        flat += value == 0
        for label, low, high in buckets:
            if (low is None or value >= low) and (high is None or value < high):
                result[label] += 1
                break
    return {"bins": [{"label": label, "count": result[label]} for label, _, _ in buckets],
            "up": up, "down": down, "flat": flat, "denominator": len(rows)}


def build_presentation(root: Path, *, featured: bool = False,
                       normalized_path: Path | None = None) -> dict:
    report = _json(output_path(root, "ranking_report.json", featured=featured))
    windows = {}
    for key, suffix in (("primary", ""), ("alternative", "_alternativo")):
        rows = _csv(output_path(root, "top20.csv" + suffix if not suffix else "top20_alternativo.csv", featured=featured))
        all_rows = _csv(output_path(root, "all_returns.csv" + suffix if not suffix else "all_returns_alternativo.csv", featured=featured))
        summary = report[key]
        if len(rows) != summary["top_n"] or len(all_rows) != summary["ranked_shares"]:
            raise ValueError(f"Contagem inconsistente na janela {key}")
        source_name = "top20.csv" if key == "primary" else "top20_alternativo.csv"
        all_name = "all_returns.csv" if key == "primary" else "all_returns_alternativo.csv"
        for name in (source_name, all_name):
            path = output_path(root, name, featured=featured)
            expected_name = "top20.csv" if name.startswith("top20") else "all_returns.csv"
            expected_hash = summary.get("outputs", {}).get(expected_name)
            if expected_hash and digest(path) != expected_hash:
                raise ValueError(f"Hash divergente: {name}")
        windows[key] = {"start_date": summary["start_date"], "end_date": summary["end_date"],
                        "mean_pct": summary["mean_return_pct_display"],
                        "eligible": summary["eligible_shares"], "excluded": summary["excluded_instruments"],
                        "top20": rows, "breadth": _distribution(all_rows)}
    quality = _json(output_path(root, "quality_context.json", featured=featured))
    exclusions = _csv(output_path(root, "candidate_exclusions.csv", featured=featured))
    tickers = {row["ticker"] for window in windows.values() for row in window["top20"]}
    baseline, end = windows["primary"]["start_date"], windows["primary"]["end_date"]
    if normalized_path and normalized_path.exists():
        daily = daily_context(normalized_path, tickers, baseline, end)
    else:
        series_path = root / "daily_context.json"
        daily = _json(series_path) if series_path.exists() else {"dates": [], "series": {}, "heatmap": {}, "note": "Série diária indisponível."}
    return {"kind": "featured" if featured else "analysis", "week": report["week"],
            "windows": windows, "daily": daily, "quality": quality,
            "exclusions": {"count": len(exclusions), "reasons": dict(Counter(row["reason"] for row in exclusions))},
            "sensitivity": report["sensitivity"], "premises": report["premises"],
            "provenance": {"input_sha256": report["input_sha256"],
                           "code_sha256": report["code_sha256"], "pipeline_version": report["version"]},
            "downloads": [name for name in DOWNLOADS if output_path(root, name, featured=featured).exists()]}


def write_featured_daily(root: Path, normalized_path: Path) -> Path:
    report = _json(root / "ranking_report.json")
    tickers = {row["ticker"] for name in ("top20.csv", "top20_alternativo.csv") for row in _csv(root / name)}
    daily = daily_context(normalized_path, tickers, report["primary"]["start_date"], report["primary"]["end_date"])
    target = root / "daily_context.json"
    target.write_text(json.dumps(daily, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target
