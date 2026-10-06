"""Leitura em fluxo do Cadastro de Instrumentos B3 (BVBG.028.02).

O ZIP diário da B3 contém outro ZIP e duas versões de XML. Usa a última
versão do pregão, sem carregar o XML inteiro em memória. Não baixa dados.
"""

from __future__ import annotations

import hashlib
import io
import re
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET


SOURCE_URL_TEMPLATE = "https://www.b3.com.br/pesquisapregao/download?filelist=IN{date}.zip,"
# Códigos observados no BVBG.028.02 e conferidos com descrições/CFI do
# próprio cadastro. Códigos fora deste conjunto ficam sem classificação.
CATEGORIES = {"1": "bdr", "3": "etf", "11": "acao", "13": "unit"}


class RegistryError(ValueError):
    pass


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child(element: ET.Element | None, *names: str) -> ET.Element | None:
    node = element
    for name in names:
        if node is None:
            return None
        node = next((item for item in node if local_name(item.tag) == name), None)
    return node


def value(element: ET.Element | None, *names: str) -> str:
    node = child(element, *names)
    return (node.text or "").strip() if node is not None else ""


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def last_xml(zipped: zipfile.ZipFile) -> tuple[zipfile.ZipFile, str]:
    names = zipped.namelist()
    inner = [name for name in names if name.upper().endswith(".ZIP")]
    if inner:
        if len(inner) != 1:
            raise RegistryError("ZIP B3 contém múltiplos arquivos internos; escolha o snapshot explicitamente.")
        nested = zipfile.ZipFile(io.BytesIO(zipped.read(inner[0])))
    else:
        nested = zipped
    xmls = sorted(name for name in nested.namelist() if name.lower().endswith(".xml") and "BVBG.028.02" in name)
    if not xmls:
        raise RegistryError("Nenhum BVBG.028.02 XML encontrado no ZIP B3.")
    return nested, xmls[-1]


def classify(code: str, description: str, cfi: str) -> tuple[str, str]:
    base = CATEGORIES.get(code)
    desc = description.upper()
    if base is None:
        return "categoria_oficial_nao_mapeada", f"SctyCtgy={code}; Desc={description}; CFI={cfi}"
    if base == "acao":
        # A categoria 11 identifica ação. A espécie exige evidência adicional.
        has_on = bool(re.search(r"ON(?:\s+|$)", desc))
        has_pn = bool(re.search(r"PN[A-E]?(?:\s+|$)", desc))
        if has_on and cfi.startswith("ES"):
            base = "acao_on"
        elif has_pn and cfi.startswith("EP"):
            base = "acao_pn"
        elif has_on or has_pn:
            return "nao_resolvido", f"Espécie e CFI divergentes: SctyCtgy={code}; Desc={description}; CFI={cfi}"
    if base == "unit" and not ("UNT" in desc or "UNIT" in desc):
        return "nao_resolvido", f"Unit sem descrição compatível: SctyCtgy={code}; Desc={description}; CFI={cfi}"
    if base == "bdr" and not ("DR" in desc or "BDR" in desc):
        return "nao_resolvido", f"BDR sem descrição compatível: SctyCtgy={code}; Desc={description}; CFI={cfi}"
    return base, f"SctyCtgy={code}; Desc={description}; CFI={cfi}"


def load_bvbg(path: Path, reference_date: date, requested_tickers: set[str],
              declared_snapshot_date: date | None = None) -> tuple[dict, dict]:
    if not path.is_file():
        raise RegistryError(f"Arquivo B3 inexistente: {path}")
    outer = nested = None
    try:
        outer = zipfile.ZipFile(path)
        nested, xml_name = last_xml(outer)
        candidates = defaultdict(set)
        dates = set()
        scanned = spot = 0
        with nested.open(xml_name) as stream:
            context = ET.iterparse(stream, events=("start", "end"))
            parents: list[ET.Element] = []
            for event, node in context:
                if event == "start":
                    parents.append(node)
                    continue
                if local_name(node.tag) != "BizGrp":
                    parents.pop()
                    continue
                scanned += 1
                document = child(node, "Document", "Instrm")
                report = value(document, "RptParams", "RptDtAndTm", "Dt")
                if report:
                    dates.add(report)
                common = child(document, "FinInstrmAttrCmon")
                if value(common, "Sgmt") != "1" or value(common, "Mkt") != "10":
                    parents[-2].remove(node)
                    parents.pop()
                    continue
                spot += 1
                equity = child(document, "InstrmInf", "EqtyInf")
                ticker = value(equity, "TckrSymb").upper()
                if ticker in requested_tickers:
                    category = value(equity, "SctyCtgy")
                    description = value(common, "Desc")
                    cfi = value(equity, "CFICd")
                    isin = value(equity, "ISIN")
                    kind, detail = classify(category, description, cfi)
                    candidates[ticker].add((kind, f"{detail}; ISIN={isin}"))
                # BizGrp é filho de Xchg, não do elemento raiz Document.
                # Remover do pai libera cada registro antes de ler o próximo.
                parents[-2].remove(node)
                parents.pop()
        if len(dates) != 1:
            raise RegistryError(f"XML B3 deve conter uma única RptDt; encontradas {sorted(dates)!r}.")
        snapshot = date.fromisoformat(next(iter(dates)))
        if declared_snapshot_date and declared_snapshot_date != snapshot:
            raise RegistryError("--b3-snapshot-date diverge da RptDt do XML.")
        if snapshot > reference_date:
            raise RegistryError("Cadastro B3 posterior à data de referência; viés temporal.")
        resolved = {}
        conflicts = []
        for ticker, observations in sorted(candidates.items()):
            kinds = {kind for kind, _ in observations}
            details = " | ".join(sorted(detail for _, detail in observations))
            if len(kinds) == 1:
                resolved[ticker] = (next(iter(kinds)), details)
            else:
                resolved[ticker] = ("nao_resolvido", "Registros B3 conflitantes: " + details)
                conflicts.append(ticker)
        info = {
            "used": True, "format": "BVBG.028.02_XML", "filename": path.name,
            "sha256": digest(path), "xml_member": xml_name,
            "snapshot_date": snapshot.isoformat(), "source_url": SOURCE_URL_TEMPLATE.format(date=snapshot.strftime("%y%m%d")),
            "rows_scanned": scanned, "spot_rows": spot, "requested_tickers": len(requested_tickers),
            "matched_tickers": len(resolved), "unmatched_tickers": sorted(requested_tickers - resolved.keys()),
            "conflicted_tickers": conflicts,
            "stale_over_7_days": (reference_date - snapshot).days > 7,
        }
        return resolved, info
    except (zipfile.BadZipFile, ET.ParseError, ValueError) as exc:
        if isinstance(exc, RegistryError):
            raise
        raise RegistryError(f"Falha ao ler BVBG.028.02: {exc}") from exc
    finally:
        if nested is not None and nested is not outer:
            nested.close()
        if outer is not None:
            outer.close()
