"""Decide o universo de ações do case sem catalogar todo instrumento da B3.

A convenção do código define a hipótese. Evidência oficial datada confirma
ações elegíveis e veta qualquer contradição. Tipos fora de ON/PN ficam fora
do ranking mesmo quando sua espécie detalhada não foi resolvida.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from b3_registry import digest


RULE_VERSION = "1.0.0"
COLUMNS = ["ticker", "code_class", "official_types", "decision", "basis", "reason"]
SHARES = {"acao_on", "acao_pn"}
UNKNOWN = {"", "nao_resolvido", "categoria_oficial_nao_mapeada"}


def code_class(ticker: str) -> str:
    """Aplica a tabela B3 somente a códigos completos no formato padrão."""
    if re.fullmatch(r"[A-Z0-9]{4}3", ticker):
        return "acao_on"
    if re.fullmatch(r"[A-Z0-9]{4}[4-8]", ticker):
        return "acao_pn"
    if re.fullmatch(r"[A-Z0-9]{4}3[1-9]", ticker) or re.fullmatch(r"[A-Z0-9]{4}40", ticker):
        return "bdr"
    return "outro"


def decide(ticker: str, rows: list[dict]) -> dict:
    expected = code_class(ticker)
    observed = {row["instrument_type"] for row in rows if row["instrument_type"] not in UNKNOWN}
    types = "; ".join(sorted(observed))
    # Duplicata de preço, ISIN divergente ou conflito de fontes exige revisão
    # mesmo quando o sufixo parece inequívoco.
    if len(rows) != 2 or len({row["price_date"] for row in rows}) != 2:
        decision, basis, reason = "revisar", "estrutura", "Esperadas exatamente duas datas de preço distintas"
    elif any(row["status"] == "conflict" for row in rows):
        decision, basis, reason = "revisar", "conflito", "Conflito de preço, ISIN ou classificação entre fontes/datas"
    elif expected in SHARES:
        if observed - {expected, "acao"}:
            decision, basis, reason = "revisar", "divergencia", "Fonte oficial contradiz a espécie indicada pelo código"
        elif any(row["status"] != "confirmed" or row["instrument_type"] != expected for row in rows):
            decision, basis, reason = "revisar", "sem_confirmacao", "Ação exige confirmação oficial nas duas datas de preço"
        else:
            decision, basis, reason = "incluir", "codigo_e_b3", "Ação ON/PN confirmada nas duas datas"
    elif expected == "bdr":
        if observed - {"bdr"}:
            decision, basis, reason = "revisar", "divergencia", "Fonte oficial contradiz a faixa de BDR"
        else:
            decision, basis, reason = "excluir", "codigo_b3" if observed else "codigo", "BDR não é ação brasileira ON/PN"
    elif observed & SHARES or "acao" in observed:
        decision, basis, reason = "revisar", "divergencia", "Fonte oficial indica ação fora do código padrão; revisão necessária"
    else:
        decision, basis, reason = "excluir", "codigo_b3" if observed else "codigo", "Fora do universo de ações ON/PN; espécie detalhada não é necessária"
    return {"ticker": ticker, "code_class": expected, "official_types": types,
            "decision": decision, "basis": basis, "reason": reason}


def run(classification_path: Path, output_dir: Path) -> dict:
    grouped = defaultdict(list)
    with classification_path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"ticker", "price_date", "status", "instrument_type"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Classificação exige colunas {sorted(required)}")
        for row in reader:
            grouped[row["ticker"]].append(row)
    decisions = [decide(ticker, grouped[ticker]) for ticker in sorted(grouped)]
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "ranking_universe.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(decisions)
    summary = {"rule_version": RULE_VERSION,
               "universe_definition": "Ações ordinárias e preferenciais da B3, inclusive classes PN, com preço positivo nas duas datas e confirmação oficial em ambas",
               "candidate_tickers": len(decisions),
               "decision_counts": dict(sorted(Counter(row["decision"] for row in decisions).items())),
               "class_counts": dict(sorted(Counter(row["code_class"] for row in decisions).items())),
               "review_tickers": [row["ticker"] for row in decisions if row["decision"] == "revisar"],
               "ranking_gate_passed": bool(decisions) and not any(row["decision"] == "revisar" for row in decisions),
               "classification_sha256": digest(classification_path),
               "rule_code_sha256": digest(Path(__file__))}
    (output_dir / "ranking_universe_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary
