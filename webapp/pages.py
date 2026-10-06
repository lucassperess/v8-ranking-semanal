"""Composição das páginas e navegação compartilhada no servidor.

Somente templates próprios podem ser lidos. Uploads não são templates.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAGES = {"index.html": "ranking", "methodology.html": "documentation",
         "documentation.html": "documentation", "new-analysis.html": "new-analysis"}


def render_page(filename: str) -> str:
    active = PAGES[filename]
    header = (ROOT / "templates" / "header.html").read_text(encoding="utf-8")
    for name in {"ranking", "documentation", "new-analysis"}:
        header = header.replace("{{ACTIVE_" + name + "}}", 'aria-current="page"' if name == active else "")
    return (ROOT / "static" / filename).read_text(encoding="utf-8").replace("{{HEADER}}", header)
