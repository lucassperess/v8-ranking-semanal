"""Deterministic relevance selection before model calls; no causal inference."""

import re
from urllib.parse import urlsplit

from context_pipeline.sources import entity_name, normalized

SOCIAL_HOSTS = {'tiktok.com', 'facebook.com', 'instagram.com', 'youtube.com',
                'youtu.be', 'twitter.com', 'x.com', 'reddit.com', 'pinterest.com'}
BUSINESS_TERMS = ('fato relevante', 'comunicado ao mercado', 'aviso aos acionistas',
                  'aquisicao', 'incorporacao', 'grupamento', 'capital social',
                  'recuperacao judicial', 'debentures', 'assembleia', 'contrato',
                  'dividendos', 'proventos', 'renegociacao', 'operacao', 'resultados')
INSTITUTIONAL_TERMS = ('estatuto', 'politica de', 'codigo de conduta', 'formulario de referencia')


def search_alias(identity):
    # B3 may abbreviate "Participações" as PART in its trading name.
    # Remove only that suffix, retaining the supplied company identity for verification.
    return re.sub(r'\s+PART\.?$', '', identity.get('search_name', ''), flags=re.IGNORECASE)


def identity_present(text, identity):
    words = entity_name(text)
    aliases = {entity_name(identity.get(key, '')) for key in ('name', 'search_name')}
    aliases.add(entity_name(search_alias(identity)))
    aliases -= {'', 'brasil', 'nacional', 'energia', 'companhia', 'banco'}
    return (any(len(alias) >= 4 and re.search(r'\b' + re.escape(alias) + r'\b', words) for alias in aliases)
            or any(re.search(r'\b' + re.escape(ticker.lower()) + r'\b', words)
                   for ticker in identity.get('tickers', [])))


def candidate_reason(row, identity, macro=False):
    try:
        url = urlsplit(row.get('url', ''))
    except ValueError:
        return 'invalid_source_url'
    host = (url.hostname or '').lower()
    if url.scheme not in {'http', 'https'} or not host:
        return 'invalid_source_url'
    if any(host == domain or host.endswith('.' + domain) for domain in SOCIAL_HOSTS):
        return 'social_source_not_selected'
    path = normalized(url.path)
    if any(part in path for part in ('/cotacoes/', '/cotacao/', '/calendario-de-resultados', '/perfil/')):
        return 'navigation_or_quote_page'
    text = (row.get('title') or '') + ' ' + (row.get('content') or '')
    if not macro and not identity_present(text, identity):
        return 'company_not_explicit_in_search_result'
    return None


def select_candidates(candidates, identity, macro=False):
    selected, rejected, seen = [], [], set()
    for index, row in enumerate(candidates):
        reason = candidate_reason(row, identity, macro)
        if not reason and row['url'] in seen:
            reason = 'duplicate_source_url'
        if reason:
            rejected.append({'index': index, 'reason': reason})
        else:
            seen.add(row['url'])
            selected.append(row)
    # Regulatory/RI announcements outrank generic news but require identity too.
    def priority(row):
        text = normalized((row.get('title') or '') + ' ' + (row.get('content') or ''))
        host = (urlsplit(row['url']).hostname or '').lower()
        official = host.endswith('.cvm.gov.br') or host.endswith('.b3.com.br') or host.startswith('ri.')
        return (not official, -sum(term in text for term in BUSINESS_TERMS))
    return sorted(selected, key=priority), rejected


def select_documents(documents, code, start, week_start, end, limit=5):
    matching = []
    for row in documents:
        try:
            same = str(int(row.get('Codigo_CVM', ''))) == code
        except ValueError:
            continue
        if same and start <= row.get('Data_Entrega', '')[:10] <= end and row.get('Link_Download'):
            matching.append(row)
    # One latest version per catalog document; preserve the catalog metadata.
    latest = {}
    for row in sorted(matching, key=lambda r: r['Data_Entrega'], reverse=True):
        key = row.get('ID_Documento') or row['Link_Download']
        latest.setdefault(key, row)
    def priority(row):
        text = normalized(row.get('Categoria', '') + ' ' + row.get('Assunto', '') + ' ' + row.get('Tipo', ''))
        if any(term in text for term in INSTITUTIONAL_TERMS):
            return 2
        return 0 if any(term in text for term in BUSINESS_TERMS) else 1
    weekly = sorted((r for r in latest.values() if r['Data_Entrega'][:10] >= week_start), key=priority)
    prior = sorted((r for r in latest.values() if r['Data_Entrega'][:10] < week_start), key=priority)
    # Reserve room for antecedents without letting them displace every weekly fact.
    selected = weekly[:3] + prior[:2]
    chosen = {r['Link_Download'] for r in selected}
    selected += [r for r in weekly[3:] + prior[2:] if r['Link_Download'] not in chosen][:limit - len(selected)]
    return selected[:limit]


def readable_excerpt(body, identity, limit=3000):
    """Return one continuous passage, retaining exact original characters."""
    if len(body) <= limit:
        return body, 0
    anchors = {0}
    # Whitespace-collapsed lookup maps matches back to the original PDF text.
    lookup, positions = [], []
    for match in re.finditer(r'\S+', body):
        token = normalized(match.group())
        lookup.extend(token + ' ')
        positions.extend([match.start()] * (len(token) + 1))
    searchable = ''.join(lookup)
    terms = [*BUSINESS_TERMS, *identity.get('tickers', []), identity.get('search_name', '')]
    for term in terms:
        if len(term) < 4:
            continue
        for match in list(re.finditer(re.escape(normalized(term)), searchable))[:12]:
            anchors.add(max(0, positions[match.start()] - limit // 3))
    def score(offset):
        text = normalized(body[offset:offset + limit])
        nav = sum(text.count(term) for term in ('buscar', 'fazer login', 'ebook', 'planilha gratis', 'newsletter'))
        return (sum(term in text for term in BUSINESS_TERMS) * 3 +
                int(identity_present(text, identity)) * 4 - nav * 3, -offset)
    offset = max(anchors, key=score)
    # Avoid starting in the middle of a token; retain a contiguous original slice.
    if offset and not body[offset - 1].isspace():
        while offset < len(body) and not body[offset].isspace():
            offset += 1
    return body[offset:offset + limit], offset
