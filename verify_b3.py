"""Checagem independente da espécie ON/PN/UNT no COTAHIST oficial da B3."""

from __future__ import annotations

import argparse
import csv
import json
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path

from b3_registry import digest


def verify(normalized: Path, cotahist: Path, snapshot_date: date) -> dict:
    types = {}
    with normalized.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            ticker, kind = row["ticker"], row["instrument_type"]
            if ticker and kind in {"acao_on", "acao_pn", "unit"}:
                if ticker in types and types[ticker] != kind:
                    raise ValueError(f"Classificação inconsistente no ETL: {ticker}")
                types[ticker] = kind
    expected = {"acao_on": "ON", "acao_pn": "PN", "unit": "UNT"}
    matched, mismatches = {}, []
    with zipfile.ZipFile(cotahist) as archive:
        members = [name for name in archive.namelist() if name.upper().endswith(".TXT")]
        if len(members) != 1:
            raise ValueError("COTAHIST deve conter um único TXT.")
        with archive.open(members[0]) as stream:
            for raw in stream:
                line = raw.decode("cp1252").rstrip("\r\n")
                if not line.startswith("01"):
                    continue
                if len(line) < 49:
                    raise ValueError("Linha COTAHIST menor que o layout fixo.")
                if line[2:10] != snapshot_date.strftime("%Y%m%d"):
                    raise ValueError("Data COTAHIST divergente do snapshot informado.")
                if line[24:27] != "010":
                    continue
                ticker, spec = line[12:24].strip(), line[39:49].strip()
                if ticker not in types:
                    continue
                matched[ticker] = spec
                if not spec.startswith(expected[types[ticker]]):
                    mismatches.append({"ticker": ticker, "b3_xml_type": types[ticker], "cotahist_spec": spec})
    return {
        "snapshot_date": snapshot_date.isoformat(), "normalized_sha256": digest(normalized),
        "cotahist_sha256": digest(cotahist), "classified_tickers": len(types),
        "traded_tickers_compared": len(matched),
        "compared_by_type": dict(sorted(Counter(types[t] for t in matched).items())),
        "mismatches": sorted(mismatches, key=lambda x: x["ticker"]),
        "note": "Ausência no COTAHIST não refuta o cadastro: o instrumento pode não ter negociado no pregão.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--normalized", type=Path, required=True)
    parser.add_argument("--cotahist", type=Path, required=True)
    parser.add_argument("--snapshot-date", type=date.fromisoformat, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.normalized, args.cotahist, args.snapshot_date)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"compared": report["traded_tickers_compared"], "mismatches": len(report["mismatches"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
