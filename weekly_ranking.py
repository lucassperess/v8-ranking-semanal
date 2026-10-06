"""ETL, seleção da semana, classificação B3 e ranking reproduzível de ações.

Uso: python weekly_ranking.py --input economatica.csv --reference-date AAAA-MM-DD
     --output-dir runs/semana-AAAA-MM-DD [--reference-dir data/reference]
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

import etl
import resolve_period
from b3_registry import digest
from classify_period import ClassificationError


VERSION = "1.0.0"
TOP_N = 20
PRICE_COLUMNS = ["ticker", "instrument_type", "start_date", "end_date", "start_close", "end_close", "return_fraction", "return_pct"]


class RankingError(ValueError):
    pass


def write_text_lf(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def choose_week(quality_path: Path, reference_date: date, allow_nonfriday_end: bool = False) -> dict:
    """Semana calendário anterior, usando pregões presentes e com cobertura."""
    current_monday = reference_date - timedelta(days=reference_date.weekday())
    monday = current_monday - timedelta(days=7)
    sunday = monday + timedelta(days=6)
    friday = monday + timedelta(days=4)
    with quality_path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"date", "positive_close"}.issubset(reader.fieldnames or []):
            raise RankingError("quality_by_date.csv sem date e positive_close")
        available = [(date.fromisoformat(row["date"]), int(row["positive_close"])) for row in reader]
    quoted = [(day, count) for day, count in available if count > 0 and day < current_monday]
    in_week = [(day, count) for day, count in quoted if monday <= day <= sunday]
    before = [(day, count) for day, count in quoted if day < monday]
    if not in_week or not before:
        raise RankingError("Faltam cotações positivas na semana anterior ou antes dela")
    first, end, baseline = min(in_week)[0], max(in_week)[0], max(before)[0]
    if end < friday and not allow_nonfriday_end:
        raise RankingError(f"Última cotação da semana foi {end}, antes de sexta {friday}; "
                           "verifique feriado/extração ou use --allow-nonfriday-end")
    if (monday - baseline).days > 10:
        raise RankingError(f"Fechamento anterior à semana está distante: {baseline}")
    # Uma data com pouquíssimos papéis pode indicar extração parcial. Não a
    # escolhemos silenciosamente como ponta do retorno.
    recent_dates = sorted((day, count) for day, count in quoted if day <= end)[-10:]
    recent_counts = sorted(count for _, count in recent_dates)
    median = recent_counts[len(recent_counts) // 2]
    selected = {day: count for day, count in available}
    for label, day in (("anterior", baseline), ("primeiro", first), ("último", end)):
        if selected[day] * 2 < median:
            raise RankingError(f"Cobertura insuficiente no fechamento {label} {day}: "
                               f"{selected[day]} contra mediana recente {median}")
    if first == end:
        raise RankingError("Só há um dia com cotação na semana; comparação alternativa indisponível")
    return {"reference_date": reference_date.isoformat(), "week_start": monday.isoformat(),
            "week_end": sunday.isoformat(), "preceding_close": baseline.isoformat(),
            "first_week_close": first.isoformat(), "last_week_close": end.isoformat(),
            "recent_median_positive_closes": median,
            "selected_date_coverage": {day.isoformat(): selected[day] for day in (baseline, first, end)},
            "nonfriday_end_accepted": end < friday}


def positive_price(raw: str, ticker: str, day: str) -> Decimal:
    try:
        price = Decimal(raw)
    except (InvalidOperation, TypeError):
        raise RankingError(f"Fechamento não numérico para {ticker} em {day}") from None
    if not price.is_finite() or price <= 0:
        raise RankingError(f"Fechamento não positivo/finito para {ticker} em {day}")
    return price


def quality_context(path: Path, start: date, end: date,
                    eligible_tickers: set[str], top_tickers: set[str]) -> dict:
    selected_dates = {start.isoformat(), end.isoformat()}
    relevant, top_issues = [], []
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"ticker", "trade_date", "field", "code", "severity", "reason"}
        if not required.issubset(reader.fieldnames or []):
            raise RankingError("quality_issues.csv incompleto")
        for row in reader:
            if row["trade_date"] not in selected_dates:
                continue
            relevant.append(row)
            if row["ticker"] in eligible_tickers and row["field"] == "close" and row["severity"] == "error":
                raise RankingError(f"Fechamento de {row['ticker']} em {row['trade_date']} possui erro de qualidade")
            if row["ticker"] in top_tickers:
                top_issues.append({key: row[key] for key in ("ticker", "trade_date", "field", "code", "severity", "reason")})
    return {"source_sha256": digest(path), "dates": sorted(selected_dates),
            "etl_issue_counts_raw": dict(sorted(Counter(row["code"] for row in relevant).items())),
            "note": "Alertas provisórios de tipo no ETL podem ter sido resolvidos pela classificação B3 posterior",
            "top20_issues": sorted(top_issues, key=lambda row: (row["ticker"], row["trade_date"], row["code"], row["field"]))}


def rank_pair(classification_dir: Path, start: date, end: date, output_dir: Path,
              quality_issues_path: Path | None = None) -> dict:
    manifest = json.loads((classification_dir / "classification_manifest.json").read_text(encoding="utf-8"))
    for name in ("period_classification.csv", "ranking_universe.csv", "classification_summary.json"):
        if digest(classification_dir / name) != manifest["outputs"][name]:
            raise RankingError(f"Arquivo de classificação modificado após a execução: {name}")
    summary_path = classification_dir / "classification_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if (summary["start_date"], summary["end_date"]) != (start.isoformat(), end.isoformat()):
        raise RankingError("As datas da classificação não coincidem com as datas solicitadas")
    if not summary["ranking_gate_passed"]:
        raise RankingError(f"Classificação pendente para o ranking: {summary['ranking_review_tickers']}")
    with (classification_dir / "ranking_universe.csv").open(encoding="utf-8", newline="") as stream:
        decisions = list(csv.DictReader(stream))
    if len(decisions) != len({row["ticker"] for row in decisions}):
        raise RankingError("Ticker duplicado no universo de ranking")
    allowed = {row["ticker"]: row for row in decisions if row["decision"] == "incluir"}
    if any(row["decision"] not in ("incluir", "excluir") for row in decisions):
        raise RankingError("Universo contém decisão pendente")
    classified = {}
    with (classification_dir / "period_classification.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            key = (row["ticker"], row["price_date"])
            if key in classified:
                raise RankingError(f"Preço duplicado na classificação: {key}")
            classified[key] = row
    all_returns = []
    for ticker in sorted(allowed):
        try:
            first = classified[ticker, start.isoformat()]
            last = classified[ticker, end.isoformat()]
        except KeyError:
            raise RankingError(f"Falta uma das pontas do retorno para {ticker}") from None
        kind = allowed[ticker]["code_class"]
        if kind not in ("acao_on", "acao_pn") or any(
            row["status"] != "confirmed" or row["instrument_type"] != kind for row in (first, last)
        ):
            raise RankingError(f"Ação {ticker} sem classificação oficial consistente")
        p0 = positive_price(first["close"], ticker, start.isoformat())
        p1 = positive_price(last["close"], ticker, end.isoformat())
        ret = p1 / p0 - 1
        all_returns.append({"ticker": ticker, "instrument_type": kind,
                            "start_date": start.isoformat(), "end_date": end.isoformat(),
                            "start_close": str(p0), "end_close": str(p1),
                            "return_fraction": str(ret), "return_pct": str(ret * 100)})
    if len(all_returns) < TOP_N:
        raise RankingError(f"Apenas {len(all_returns)} ações elegíveis; são necessárias {TOP_N}")
    all_returns.sort(key=lambda row: (-Decimal(row["return_fraction"]), row["ticker"]))
    top = all_returns[:TOP_N]
    if len(all_returns) > TOP_N and Decimal(top[-1]["return_fraction"]) < Decimal(all_returns[TOP_N]["return_fraction"]):
        raise RankingError("Ordenação do top 20 inconsistente")
    mean = sum((Decimal(row["return_fraction"]) for row in top), Decimal(0)) / TOP_N
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in (("all_returns.csv", all_returns), ("top20.csv", top)):
        with (output_dir / name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=PRICE_COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    if quality_issues_path is not None:
        context = quality_context(quality_issues_path, start, end, set(allowed), {row["ticker"] for row in top})
        write_text_lf(output_dir / "quality_context.json", json.dumps(context, ensure_ascii=False, indent=2) + "\n")
    extreme = [row["ticker"] for row in all_returns if abs(Decimal(row["return_fraction"])) >= Decimal("0.50")]
    result = {"start_date": start.isoformat(), "end_date": end.isoformat(),
              "universe_candidates": len(decisions), "eligible_shares": len(allowed),
              "excluded_instruments": len(decisions) - len(allowed), "ranked_shares": len(all_returns),
              "top_n": TOP_N, "mean_return_fraction": str(mean),
              "mean_return_pct_exact": str(mean * 100),
              "mean_return_pct_display": str((mean * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
              "extreme_return_tickers_at_least_50pct_abs": extreme,
              "tie_breaker": "ticker crescente quando retornos exatos empatam",
              "classification_manifest_sha256": digest(classification_dir / "classification_manifest.json"),
              "outputs": {name: digest(output_dir / name) for name in
                          (("all_returns.csv", "top20.csv", "quality_context.json") if quality_issues_path else
                           ("all_returns.csv", "top20.csv"))}}
    write_text_lf(output_dir / "ranking_summary.json", json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def display_pct(raw: str) -> str:
    return f"{Decimal(raw).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}".replace(".", ",") + "%"


def write_case_readme(output_dir: Path, report: dict) -> None:
    primary, alternative, week = report["primary"], report["alternative"], report["week"]
    with (output_dir / "rankings" / "principal" / "top20.csv").open(encoding="utf-8", newline="") as stream:
        top = list(csv.DictReader(stream))
    quality = json.loads((output_dir / "rankings" / "principal" / "quality_context.json").read_text(encoding="utf-8"))
    lines = [f"Média dos retornos do top 20: {display_pct(primary['mean_return_pct_display'])}", "",
             "# Ações que mais subiram na semana anterior", "",
             f"Referência: {week['reference_date']}. Semana analisada: {week['week_start']} a {week['week_end']}. "
             f"Variação principal: fechamento ajustado de {primary['start_date']} a {primary['end_date']}.", "",
             "| Posição | Ação | Espécie | Fechamento inicial | Fechamento final | Retorno |",
             "| ---: | --- | --- | ---: | ---: | ---: |"]
    for index, row in enumerate(top, start=1):
        kind = "ON" if row["instrument_type"] == "acao_on" else "PN"
        lines.append(f"| {index} | {row['ticker']} | {kind} | {row['start_close']} | {row['end_close']} | "
                     f"{display_pct(row['return_pct'])} |")
    lines.extend(["", "## Leitura e premissas", "",
                  f"A semana-calendário anterior vai de {week['week_start']} a {week['week_end']}. "
                  "O fechamento imediatamente anterior à semana mede também o movimento da segunda-feira. "
                  "Retorno = fechamento ajustado final da Economatica / fechamento ajustado inicial - 1. "
                  "Entram ações ON e PN confirmadas pela B3 nas duas pontas; BDRs, units e outros instrumentos ficam fora. "
                  "Não foi aplicado filtro de liquidez. A ordenação usa retorno sem arredondamento, "
                  "com ticker como desempate. A média é aritmética e usa os 20 retornos sem arredondamento.", "",
                  f"Na interpretação alternativa ({alternative['start_date']} a {alternative['end_date']}), "
                  f"a média é {display_pct(alternative['mean_return_pct_display'])}; "
                  f"{report['sensitivity']['top20_overlap']} ações aparecem nos dois top 20. "
                  "Essa alternativa não substitui o resultado principal.", "",
                  f"Foram consideradas {primary['ranked_shares']} ações com preços válidos nas duas datas; "
                  f"{primary['excluded_instruments']} outros instrumentos com dois preços ficaram fora. "
                  "Códigos sem os dois fechamentos constam em `classification/principal/candidate_exclusions.csv`.", ""])
    if quality["top20_issues"]:
        lines.append("Alertas de qualidade envolvendo o top 20 (não alteram preços automaticamente): " +
                     "; ".join(f"{item['ticker']} em {item['trade_date']}: {item['field']} — {item['reason']}"
                               for item in quality["top20_issues"]) + ".")
    else:
        lines.append("Não houve alertas de qualidade nas linhas do top 20 nas duas datas de preço.")
    lines.extend(["", "## Reproduzir", "",
                  "Com Python 3.11+ e o CSV original disponível, rode na raiz do projeto:", "",
                  "```powershell",
                  f'python weekly_ranking.py --input "CAMINHO\\economatica.csv" --reference-date {week["reference_date"]} --output-dir "runs\\semana-{week["reference_date"]}"',
                  "```", "",
                  "O programa obtém cadastros e cotações oficiais da B3 quando não estão em `data/reference/`. "
                  "Com os arquivos já guardados, acrescente `--offline`. "
                  "Os CSVs de retornos, classificações, alertas e manifestos ficam na pasta da execução.", ""])
    write_text_lf(output_dir / "README.md", "\n".join(lines))


def run(input_path: Path, reference_date: date, output_dir: Path, reference_dir: Path,
        offline: bool = False, allow_nonfriday_end: bool = False) -> dict:
    etl_dir = output_dir / "etl"
    etl_manifest = etl.run(input_path, reference_date, etl_dir)
    for name in ("normalized.csv", "quality_by_date.csv", "quality_issues.csv"):
        if digest(etl_dir / name) != etl_manifest["outputs"][name]:
            raise RankingError(f"Saída do tratamento modificada após a execução: {name}")
    week = choose_week(etl_dir / "quality_by_date.csv", reference_date, allow_nonfriday_end)
    end = date.fromisoformat(week["last_week_close"])
    results = {}
    for label, key in (("principal", "preceding_close"), ("alternativa", "first_week_close")):
        start = date.fromisoformat(week[key])
        classified_dir = output_dir / "classification" / label
        resolve_period.run(etl_dir / "normalized.csv", start, end, classified_dir, reference_dir, offline)
        results[label] = rank_pair(classified_dir, start, end, output_dir / "rankings" / label,
                                   etl_dir / "quality_issues.csv")
    primary = results["principal"]
    alternate = results["alternativa"]
    with (output_dir / "rankings" / "principal" / "top20.csv").open(encoding="utf-8", newline="") as stream:
        primary_tickers = {row["ticker"] for row in csv.DictReader(stream)}
    with (output_dir / "rankings" / "alternativa" / "top20.csv").open(encoding="utf-8", newline="") as stream:
        alternative_tickers = {row["ticker"] for row in csv.DictReader(stream)}
    result = {"version": VERSION, "code_sha256": digest(Path(__file__)), "week": week,
              "primary": primary, "alternative": alternate,
              "sensitivity": {"top20_overlap": len(primary_tickers & alternative_tickers),
                              "mean_difference_percentage_points": str(
                                  Decimal(primary["mean_return_pct_exact"]) - Decimal(alternate["mean_return_pct_exact"]))},
              "input_sha256": etl_manifest["input_sha256"],
              "etl_manifest_sha256": digest(etl_dir / "manifest.json"),
              "premises": ["Semana anterior de segunda a domingo",
                           "Principal: último fechamento antes da semana até último fechamento nela",
                           "Alternativa: primeiro até último fechamento na semana",
                           "Preços de fechamento ajustados da Economatica; B3 apenas para espécie do instrumento",
                           "Retorno = preço final / preço inicial - 1",
                           "Universo ON/PN confirmado; sem filtro de liquidez",
                           "Média aritmética dos 20 maiores retornos exatos; arredondamento só na apresentação"]}
    write_text_lf(output_dir / "ranking_report.json", json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    write_case_readme(output_dir, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--reference-date", type=date.fromisoformat, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reference-dir", type=Path, default=Path(__file__).parent / "data" / "reference")
    parser.add_argument("--offline", action="store_true", help="Usa somente fontes B3 já baixadas")
    parser.add_argument("--allow-nonfriday-end", action="store_true", help="Aceita semana cujo último pregão disponível foi antes de sexta")
    args = parser.parse_args()
    try:
        report = run(args.input, args.reference_date, args.output_dir, args.reference_dir,
                     args.offline, args.allow_nonfriday_end)
    except (etl.InputError, ClassificationError, RankingError, OSError, ValueError) as exc:
        parser.exit(2, f"Erro: {exc}\n")
    print(json.dumps({"week": report["week"],
                      "primary_mean_pct": report["primary"]["mean_return_pct_display"],
                      "alternative_mean_pct": report["alternative"]["mean_return_pct_display"],
                      "top20_overlap": report["sensitivity"]["top20_overlap"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
