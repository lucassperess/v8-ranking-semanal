"""Publica artigos versionados do repositório, sem ler conteúdo de uploads."""

import html
import re
from pathlib import Path

import markdown
from webapp.pages import render_page
from webapp.doc_revision import current_revision

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "comece-aqui": ("Comece aqui", "comece-aqui.md", "Objetivo, fontes e caminhos para explorar a ferramenta."),
    "como-usar": ("Como usar o dashboard", "como-usar.md", "Indicadores, gráficos, downloads e novas análises."),
    "metodologia": ("Metodologia do ranking", "metodologia.md", "Semana, elegibilidade, retornos e média do top 20."),
    "dados": ("Dados e tratamento", "dados.md", "Formato da extração, campos e controles de qualidade."),
    "classificacao": ("Classificação dos instrumentos", "classificacao.md", "Regras de código, confirmação B3 e conflitos."),
    "sistema": ("Como o sistema funciona", "sistema.md", "Do envio à fila, ao Python e à apresentação."),
    "auditoria": ("Auditoria e reprodução", "auditoria.md", "Arquivos, procedência e reprodução pelo comando."),
    "duvidas": ("Problemas e dúvidas", "duvidas.md", "Lacunas, erros, limites e disponibilidade."),
}
REPO = "https://github.com/lucassperess/v8-ranking-semanal/blob/main/"
FLOW = '<div class="docs-flow" role="group" aria-label="Fluxo do processamento"><ol>' + ''.join(
    f'<li><span>{i:02d}</span><strong>{title}</strong><p>{desc}</p></li>'
    for i, (title, desc) in enumerate([
        ("Receber e tratar", "CSV preservado, campos interpretados e problemas registrados."),
        ("Definir as pontas", "Semana anterior e datas com cobertura suficiente."),
        ("Confirmar o universo", "Dois preços válidos e evidência B3 para ON/PN."),
        ("Calcular", "Retornos, ordenação e média produzidos em Python."),
        ("Apresentar", "Ranking, gráficos e arquivos da execução."),
    ], 1)
) + '</ol><p class="docs-flow-warning">Pendência relevante → processamento interrompido com motivo explícito.</p></div>'


def source(slug: str) -> str:
    return (ROOT / "docs" / PAGES[slug][1]).read_text(encoding="utf-8")


def rewrite_link(match: re.Match) -> str:
    label, target = match.groups()
    by_file = {value[1]: key for key, value in PAGES.items()}
    filename, _, fragment = target.partition("#")
    if filename in by_file:
        target = "/documentacao/" + by_file[filename] + ("#" + fragment if fragment else "")
    elif filename == "README.md":
        target = "/documentacao"
    elif filename.startswith("../"):
        target = REPO + filename[3:] + ("#" + fragment if fragment else "")
    elif filename.startswith('assets/'):
        target = '/documentation-assets/' + filename[7:]
    elif filename.endswith('.md'):
        target = REPO + 'docs/' + filename + ('#' + fragment if fragment else '')
    return f"[{label}]({target})"


def render(slug: str, *, snapshot: dict | None = None, archive_base: str = '') -> str:
    text = snapshot['documents']['docs/' + PAGES[slug][1]]['content'] if snapshot else source(slug)
    # O índice é gerado dos títulos reais. O diagrama tem equivalente HTML/textual,
    # sem scripts ou dependência de um serviço externo para desenhá-lo.
    text = re.sub(r"## Nesta página\n.*?(?=\n## )", "", text, flags=re.S)
    text = re.sub(r"```mermaid\n.*?```", FLOW, text, flags=re.S)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", rewrite_link, text)
    engine = markdown.Markdown(extensions=["tables", "fenced_code", "toc"], extension_configs={
        "toc": {"toc_depth": "2-3", "slugify": lambda value, separator: re.sub(r"[^\w-]", "", re.sub(r"\s+", separator, value.lower()))}
    })
    content = engine.convert(text)
    content = re.sub(r"(<table>.*?</table>)", r'<div class="docs-table">\1</div>', content, flags=re.S)
    nav = ''.join(f'<a href="/documentacao/{key}"' + (' aria-current="page"' if key == slug else '') + f'>{html.escape(value[0])}</a>' for key, value in PAGES.items())
    cards = ''
    if slug == "comece-aqui":
        cards = '<div class="docs-cards">' + ''.join(f'<a href="/documentacao/{key}"><strong>{html.escape(value[0])}</strong><p>{html.escape(value[2])}</p><span>Explorar →</span></a>' for key, value in PAGES.items() if key != slug) + '</div>'
    keys = list(PAGES)
    pos = keys.index(slug)
    adjacent = ''.join(f'<a href="/documentacao/{keys[index]}"><small>{direction}</small>{html.escape(PAGES[keys[index]][0])} {arrow}</a>' for index, direction, arrow in [(pos - 1, "Anterior", "←"), (pos + 1, "Próximo", "→")] if 0 <= index < len(keys))
    template = render_page("documentation.html")
    for key, value in {"TITLE": html.escape(PAGES[slug][0]), "NAV": nav, "CONTENT": content, "TOC": engine.toc,
                       "CARDS": cards, "ADJACENT": adjacent, "SOURCE": REPO + "docs/" + PAGES[slug][1],
                       'REVISION': (snapshot['revision'] if snapshot else current_revision())[:12]}.items():
        template = template.replace("{{" + key + "}}", value)
    if snapshot:
        template = re.sub(r'href="/documentacao/([^"?#]+)',
                          lambda m: f'href="{archive_base}/{m[1]}', template)
        template = template.replace('Regras e guias da ferramenta · exemplos históricos identificados no artigo.',
            'Cópia arquivada desta execução · ' + (
            'associada após revisão; não foi registrada na data do processamento.'
            if snapshot['mode'] == 'reviewed_after_execution' else 'registrada na conclusão do processamento.'))
        template = template.replace('id="docs-search"', 'id="docs-search" disabled')
        template = template.replace('class="docs-search-area"', 'class="docs-search-area" hidden')
        template = template.replace('Ex.: preço ausente, semana, B3', 'Use o menu de assuntos nesta revisão')
        template = template.replace('Consultar fonte e histórico no GitHub ↗', 'Consultar artigo atual no GitHub ↗')
        template = template.replace('id="docs-context"', 'id="docs-context" data-archived="true"')
    return template


def search_index() -> list[dict]:
    aliases = {"duvidas": "dados faltando sem cotação célula vazia erro arquivo indisponível",
               "dados": "formato arquivo base dados faltando ausência CSV colunas",
               "classificacao": "tipo ação ordinária preferencial unit BDR não encontrado",
               "sistema": "por debaixo dos panos arquitetura API fila worker"}
    return [{"title": value[0], "description": value[2], "url": "/documentacao/" + key,
             "text": aliases.get(key, "") + " " + re.sub(r"[#*`|\[\]()]", " ", source(key))} for key, value in PAGES.items()]
