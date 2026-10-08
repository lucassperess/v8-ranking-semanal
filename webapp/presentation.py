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
from webapp.doc_revision import details as documentation_details


DOWNLOADS = {
    'context_manifest.json': ('context', 'manifest.json'),
    'context_company.json': ('context', 'company.json'),
    'context_market.json': ('context', 'market.json'),
    'context_audit.json': ('context', 'audit.json'),
    "documentation_snapshot.json": ("root", "documentation_snapshot.json"),
    "top20.csv": ("principal", "top20.csv"),
    "all_returns.csv": ("principal", "all_returns.csv"),
    "top20_alternativo.csv": ("alternativa", "top20.csv"),
    "all_returns_alternativo.csv": ("alternativa", "all_returns.csv"),
    "quality_context.json": ("principal", "quality_context.json"),
    "quality_context_alternativo.json": ("alternativa", "quality_context.json"),
    "candidate_exclusions.csv": ("classification", "candidate_exclusions.csv"),
    "ranking_report.json": ("root", "ranking_report.json"),
    "README.md": ("root", "README.md"),
    "analysis_request.json": ("root", "analysis_request.json"),
    "etl_manifest.json": ("etl", "manifest.json"),
    "quality_summary.json": ("etl", "quality_summary.json"),
    "quality_by_date.csv": ("etl", "quality_by_date.csv"),
    "quality_issues.csv": ("etl", "quality_issues.csv"),
}
for suffix, group in (("", "classification"), ("_alternativo", "classification_alternative")):
    for filename in ("ranking_universe.csv", "period_classification.csv", "b3_evidence.csv",
                     "classification_manifest.json", "source_acquisition.json", "candidate_exclusions.csv",
                     "classification_summary.json", "ranking_universe_summary.json"):
        DOWNLOADS[Path(filename).stem + suffix + Path(filename).suffix] = (group, filename)


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
    if group == "classification_alternative":
        return root / "classification" / "alternativa" / filename
    if group == "etl":
        return root / "etl" / filename
    if group == 'context':
        return root / 'context' / filename
    return root / "rankings" / group / filename


def audit_details(root: Path, *, featured: bool = False) -> dict:
    """Conferência dos derivados publicados; nenhum preço é recalculado aqui."""
    path = lambda name: output_path(root, name, featured=featured)
    report = _json(path("ranking_report.json"))
    required = ["etl_manifest.json", "quality_summary.json", "quality_issues.csv", "quality_by_date.csv"]
    required += [name + suffix + "." + extension for suffix in ("", "_alternativo")
                 for name, extension in (("classification_manifest", "json"), ("ranking_universe", "csv"),
                                         ("b3_evidence", "csv"), ("period_classification", "csv"),
                                         ("source_acquisition", "json"), ("candidate_exclusions", "csv"),
                                         ("classification_summary", "json"), ("ranking_universe_summary", "json"))]
    missing = [name for name in required if not path(name).is_file()]
    if missing:
        return {"available": False, "missing_files": missing,
                "note": "Evidências detalhadas indisponíveis nesta execução histórica; consulte os derivados disponíveis."}
    etl_manifest = _json(path("etl_manifest.json"))
    if etl_manifest["input_sha256"] != report["input_sha256"]:
        raise ValueError("Manifesto ETL usa outra entrada")
    if digest(path("etl_manifest.json")) != report["etl_manifest_sha256"]:
        raise ValueError("Hash divergente: etl_manifest.json")
    for name in ("quality_summary.json", "quality_issues.csv", "quality_by_date.csv"):
        if not path(name).is_file() or digest(path(name)) != etl_manifest["outputs"][name]:
            raise ValueError(f"Hash divergente ou arquivo ausente: {name}")
    issues = _csv(path("quality_issues.csv"))
    windows = {}
    for key, suffix in (("primary", ""), ("alternative", "_alternativo")):
        summary = report[key]
        manifest_name = "classification_manifest" + suffix + ".json"
        manifest = _json(path(manifest_name))
        if digest(path(manifest_name)) != summary["classification_manifest_sha256"]:
            raise ValueError(f"Hash divergente: {manifest_name}")
        for name in ("ranking_universe.csv", "period_classification.csv", "b3_evidence.csv", "candidate_exclusions.csv",
                     "classification_summary.json", "ranking_universe_summary.json"):
            public_name = Path(name).stem + suffix + Path(name).suffix
            if not path(public_name).is_file() or digest(path(public_name)) != manifest["outputs"][name]:
                raise ValueError(f"Hash divergente ou arquivo ausente: {public_name}")
        if manifest["normalized_sha256"] != etl_manifest["outputs"]["normalized.csv"]:
            raise ValueError("Classificação e tratamento usam entradas diferentes")
        acquisition = _json(path("source_acquisition" + suffix + ".json"))
        if (acquisition["normalized_sha256"] != manifest["normalized_sha256"]
                or acquisition["start_date"] != summary["start_date"]
                or acquisition["end_date"] != summary["end_date"]):
            raise ValueError("Aquisição B3 incompatível com a janela")
        obtained = {row["file"]: row.get("sha256") for row in acquisition["sources"]}
        if any(obtained.get(row["file"]) != row["sha256"] for row in manifest["source_files"]):
            raise ValueError("Assinaturas das fontes adquiridas divergem da classificação")
        universe = _csv(path("ranking_universe" + suffix + ".csv"))
        eligible = {row["ticker"] for row in universe if row["decision"] == "incluir"}
        excluded = [row for row in universe if row["decision"] != "incluir"]
        if len(eligible) != summary["eligible_shares"] or len(excluded) != summary["excluded_instruments"]:
            raise ValueError("Contagem de decisões divergente do relatório")
        top = {row["ticker"] for row in _csv(path("top20" + suffix + ".csv"))}
        dates = {summary["start_date"], summary["end_date"]}
        selected = [row for row in issues if row["trade_date"] in dates]
        counts = []
        for code in sorted({row["code"] for row in issues}):
            rows = [row for row in selected if row["code"] == code]
            counts.append({"code": code, "file_occurrences": sum(row["code"] == code for row in issues),
                           "endpoint_occurrences": len(rows),
                           "eligible_occurrences": sum(row["ticker"] in eligible for row in rows),
                           "top20_occurrences": sum(row["ticker"] in top for row in rows)})
        eligible_issues = [{**row, "impact": (
            "Hipótese provisória do ETL resolvida na confirmação oficial do universo."
            if row["code"] == "INSTRUMENT_AMBIGUOUS" else
            "Alerta no fechamento utilizado; valor preservado, sem correção automática."
            if row["field"] == "close" else
            "Campo não usado na fórmula do retorno; fechamento preservado.")}
            for row in selected if row["ticker"] in eligible]
        for issue in eligible_issues:
            issue['explanation'] = explain_issue(issue)
            issue['impact'] = issue['explanation']['impact']
        windows[key] = {"type_exclusions": excluded, "issue_counts": counts,
                        "eligible_issues": eligible_issues,
                        "sources": acquisition["sources"],
                        "dates": sorted(dates)}
    return {"available": True, "summary": _json(path("quality_summary.json")), "windows": windows,
            "note": "Ocorrências são contadas por campo e linha, não por ação; uma linha pode gerar vários alertas. "
                    "As colunas de janela consideram somente as duas pontas, não os dias intermediários."}


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


def explain_issue(issue: dict) -> dict:
    """Explica a ocorrência e seu alcance sem presumir a causa do problema."""
    descriptions = {
        'OUTSIDE_DAILY_RANGE': (
            'O preço informado está abaixo do mínimo ou acima do máximo registrado no CSV para esse dia.',
            'Um preço do dia deveria ficar entre esses dois limites. Essa diferença merece conferência na extração; não sabemos sua causa.'),
        'MISSING_VALUE': (
            'Esse campo veio sem valor no CSV.',
            'O programa manteve a ausência: não colocou zero nem copiou o valor de outro dia.'),
        'VOLUME_PRICE_DIVERGENCE': (
            'O volume bruto difere em mais de 10% do resultado de quantidade ajustada × preço médio ajustado.',
            'Os campos podem usar bases de ajuste diferentes. Essa comparação, sozinha, não prova erro no volume.'),
        'LOW_ABOVE_HIGH': (
            'O menor preço informado para o dia é maior que o maior preço informado.',
            'Os dois valores são incompatíveis entre si. É preciso conferir a linha no CSV original.'),
        'NONPOSITIVE_PRICE': (
            'O preço informado é zero ou negativo.',
            'Esse valor não pode ser usado como preço válido. O programa não o substitui por outro valor.'),
        'NEGATIVE_AMOUNT': (
            'A quantidade ou o volume informado é negativo.',
            'O registro merece conferência na extração; o programa não corrige esse valor automaticamente.'),
        'INSTRUMENT_AMBIGUOUS': (
            'Na leitura inicial, não foi possível confirmar o tipo de instrumento apenas pelo CSV.',
            'A confirmação é feita depois com as evidências da B3. Nas ações elegíveis desta execução, essa etapa já foi concluída.'),
    }
    observed, context = descriptions.get(issue['code'], (
        issue['reason'], 'Confira o registro na extração e os arquivos de auditoria para entender a ocorrência.'))
    impact = ('O alerta envolve o fechamento, que é o preço usado para calcular o retorno. '
              'O valor do CSV não foi corrigido automaticamente; confira-o antes de interpretar o resultado.'
              if issue['field'] == 'close' else
              'O ranking usa o fechamento inicial e o final, não este campo. '
              'Este alerta não altera o retorno calculado e não prova que o fechamento esteja errado.')
    if issue['code'] == 'INSTRUMENT_AMBIGUOUS':
        impact = 'A ação só entrou no ranking depois da confirmação oficial do seu tipo nas duas datas usadas no cálculo.'
    return {'observed': observed, 'context': context, 'impact': impact}


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


def submission_details(root: Path, *, featured: bool = False) -> dict | None:
    path = output_path(root, 'analysis_request.json', featured=featured)
    if not path.exists():
        return None  # Execuções anteriores e execuções pelo comando Python.
    request = _json(path)
    report = _json(output_path(root, 'ranking_report.json', featured=featured))
    try:
        options = request['options']
        compatible = (request['input_sha256'] == report['input_sha256']
                      and request['reference_date'] == report['week']['reference_date']
                      and options['reviewed_week'] == report['week']
                      and bool(options['allow_nonfriday_end']) == report['week']['nonfriday_end_accepted']
                      and (not options['allow_nonfriday_end'] or options['accepted_at']))
    except (KeyError, TypeError):
        raise ValueError('Registro do envio incompleto') from None
    if not compatible:
        raise ValueError('Decisão do envio diverge da execução')
    return request


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
        window_quality = _json(output_path(root, "quality_context" + suffix + ".json", featured=featured))
        windows[key] = {"start_date": summary["start_date"], "end_date": summary["end_date"],
                        "mean_pct": summary["mean_return_pct_display"],
                        "eligible": summary["eligible_shares"], "excluded": summary["excluded_instruments"],
                        "top20": rows, "breadth": _distribution(all_rows), "quality": window_quality}
    quality = _json(output_path(root, "quality_context.json", featured=featured))
    exclusions = _csv(output_path(root, "candidate_exclusions.csv", featured=featured))
    tickers = {row["ticker"] for window in windows.values() for row in window["top20"]}
    baseline, end = windows["primary"]["start_date"], windows["primary"]["end_date"]
    if normalized_path and normalized_path.exists():
        daily = daily_context(normalized_path, tickers, baseline, end)
    else:
        series_path = root / "daily_context.json"
        daily = _json(series_path) if series_path.exists() else {"dates": [], "series": {}, "heatmap": {}, "note": "Série diária indisponível."}
    payload = {"kind": "featured" if featured else "analysis", "week": report["week"],
            'documentation': documentation_details(root),
            'submission': submission_details(root, featured=featured),
            "windows": windows, "daily": daily, "quality": quality,
            "exclusions": {"count": len(exclusions), "reasons": dict(Counter(row["reason"] for row in exclusions))},
            "sensitivity": report["sensitivity"], "premises": report["premises"],
            "provenance": {"input_sha256": report["input_sha256"],
                           "code_sha256": report["code_sha256"], "pipeline_version": report["version"]},
            "audit": audit_details(root, featured=featured),
            "downloads": [name for name in DOWNLOADS if output_path(root, name, featured=featured).exists()]}
    return enrich_interpretation(payload)


def enrich_daily_windows(payload: dict) -> dict:
    """Recorta séries auditadas em memória, inclusive apresentações antigas.

    Não depende do bruto, não grava derivados e não recalcula retornos.
    O primeiro fechamento da alternativa não tem comparação dentro da janela.
    """
    daily = payload.get('daily', {})
    source_dates = daily.get('dates', [])
    for key, window in payload['windows'].items():
        dates = [day for day in source_dates if window['start_date'] <= day <= window['end_date']]
        return_dates = dates if key == 'alternative' else dates[1:]
        series, heatmap = {}, {}
        prior_dates = dict(zip(source_dates[1:], source_dates[:-1]))
        for row in window['top20']:
            ticker = row['ticker']
            prices = {point['date']: point for point in daily.get('series', {}).get(ticker, [])}
            changes = {point['date']: point for point in daily.get('heatmap', {}).get(ticker, [])}
            series[ticker] = [dict(prices.get(day, {'date': day, 'close': None})) for day in dates]
            heatmap[ticker] = []
            for day in return_dates:
                initial = key == 'alternative' and day == window['start_date']
                prior = prior_dates.get(day)
                inside = prior is not None and window['start_date'] <= prior < day
                value = changes.get(day, {}).get('return_pct') if inside and not initial else None
                heatmap[ticker].append({'date': day, 'previous_date': prior if inside and not initial else None,
                                        'return_pct': value,
                                        'reason': 'window_start' if initial else 'missing_comparison' if value is None else None})
        window['daily'] = {'dates': dates, 'return_dates': return_dates, 'series': series, 'heatmap': heatmap,
                           'note': ('O fechamento do primeiro dia é o preço inicial: — nesse dia não é zero nem dado ausente. '
                                    'O primeiro retorno compara esse fechamento com o da próxima data da extração. '
                                    if key == 'alternative' else '') +
                                   'Retornos entre datas consecutivas da extração; outras células vazias indicam preços ausentes ou conflitantes.'}
    return payload


def enrich_interpretation(payload: dict) -> dict:
    """Contexto determinístico em Decimal, separado dos derivados auditados."""
    for key, window in payload['windows'].items():
        rows = window['top20']
        issues = window.get('quality', {}).get('top20_issues')
        if issues is None:
            audit_window = payload.get('audit', {}).get('windows', {}).get(key)
            issues = audit_window['eligible_issues'] if audit_window else (
                payload.get('quality', {}).get('top20_issues', []) if key == 'primary' else [])
        tickers = {row['ticker'] for row in rows}
        issues = [issue for issue in issues if issue['ticker'] in tickers]
        for row in rows:
            row['change_brl'] = str(Decimal(row['end_close']) - Decimal(row['start_close']))
            row['issues'] = [{**issue, 'explanation': explain_issue(issue)}
                             for issue in issues if issue['ticker'] == row['ticker']]
        if key == 'primary':
            for issue in payload.get('quality', {}).get('top20_issues', []):
                issue['explanation'] = explain_issue(issue)
        window['interpretation'] = {
            'leader': {field: rows[0][field] for field in ('ticker', 'return_pct', 'change_brl')} if rows else None,
            'last_return_pct': rows[-1]['return_pct'] if rows else None,
            'low_initial_price_count': sum(Decimal(row['start_close']) < 1 for row in rows),
            'alerted_tickers': sorted({issue['ticker'] for issue in issues}),
            'negotiation_note': 'O CSV contém volume bruto e quantidade ajustada. As bases podem divergir; '
                                'sem confirmação de escala e comparabilidade, não há medida de liquidez nesta tela. '
                                'O ranking não usa filtro de liquidez.',
        }
    if 'daily' in payload:
        enrich_daily_windows(payload)
    return payload


def write_featured_daily(root: Path, normalized_path: Path) -> Path:
    report = _json(root / "ranking_report.json")
    tickers = {row["ticker"] for name in ("top20.csv", "top20_alternativo.csv") for row in _csv(root / name)}
    daily = daily_context(normalized_path, tickers, report["primary"]["start_date"], report["primary"]["end_date"])
    target = root / "daily_context.json"
    target.write_text(json.dumps(daily, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target
