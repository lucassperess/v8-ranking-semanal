"""Confere integridade e aritmética dos resultados versionados sem rede ou bruto."""
import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from b3_registry import digest
from webapp.presentation import build_presentation, output_path

ROOT = Path(__file__).resolve().parents[1]


def verify(root: Path) -> None:
    result = build_presentation(root, featured=True)
    if not result["audit"]["available"]:
        raise ValueError(f"Auditoria incompleta: {root.name}")
    report = json.loads((root / "ranking_report.json").read_text(encoding="utf-8"))
    for key, suffix in (("primary", ""), ("alternative", "_alternativo")):
        summary = report[key]
        if summary["top_n"] != 20:
            raise ValueError("A entrega deve conter exatamente 20 ações no top")
        for name, expected in summary["outputs"].items():
            public_name = Path(name).stem + suffix + Path(name).suffix
            if digest(output_path(root, public_name, featured=True)) != expected:
                raise ValueError(f"Assinatura divergente: {public_name}")
        with (root / f"all_returns{suffix}.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        values = {}
        for row in rows:
            start, end = Decimal(row["start_close"]), Decimal(row["end_close"])
            if not start.is_finite() or not end.is_finite() or start <= 0 or end <= 0:
                raise ValueError(f"Preço inválido: {row['ticker']}")
            value = end / start - 1
            if value != Decimal(row["return_fraction"]) or value * 100 != Decimal(row["return_pct"]):
                raise ValueError(f"Retorno divergente: {row['ticker']}")
            if row["ticker"] in values:
                raise ValueError(f"Código duplicado: {row['ticker']}")
            values[row["ticker"]] = value
        ordered = sorted(rows, key=lambda row: (-values[row["ticker"]], row["ticker"]))
        if rows != ordered:
            raise ValueError("Ordenação divergente")
        if result["windows"][key]["top20"] != ordered[:summary["top_n"]]:
            raise ValueError("Top 20 divergente")
        mean = sum((values[row["ticker"]] for row in ordered[:summary["top_n"]]), Decimal(0)) / summary["top_n"]
        if mean != Decimal(summary["mean_return_fraction"]):
            raise ValueError("Média divergente")
        display = f"{(mean * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"
        if display != summary["mean_return_pct_display"]:
            raise ValueError("Média apresentada divergente")
    first_line = (root / "README.md").read_text(encoding="utf-8").splitlines()[0]
    if report["primary"]["mean_return_pct_display"].replace('.', ',') + '%' not in first_line:
        raise ValueError("Primeira linha do README diverge da média")
    print(f"{root.name}: assinaturas, retornos, ordenação, top 20 e médias conferidos.")


if __name__ == "__main__":
    reports = sorted((ROOT / "resultados").glob("*/ranking_report.json"))
    if not reports:
        raise SystemExit("Nenhum resultado versionado para conferir")
    for report in reports:
        verify(report.parent)
