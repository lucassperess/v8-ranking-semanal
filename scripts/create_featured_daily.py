"""Gera a série diária pública a partir do CSV original, sem publicá-lo."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import etl
from webapp.presentation import write_featured_daily


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--featured-dir", type=Path, default=ROOT / "resultados" / "2026-09-22")
    args = parser.parse_args()
    report = json.loads((args.featured_dir / "ranking_report.json").read_text(encoding="utf-8"))
    if etl.sha256(args.input) != report["input_sha256"]:
        parser.error("O CSV informado não é a extração que gerou o resultado de referência")
    with tempfile.TemporaryDirectory() as temporary:
        output = Path(temporary) / "etl"
        etl.run(args.input, date.fromisoformat(report["week"]["reference_date"]), output)
        target = write_featured_daily(args.featured_dir, output / "normalized.csv")
    print(target)


if __name__ == "__main__":
    main()
