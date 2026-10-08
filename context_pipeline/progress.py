"""Atomic public progress containing only completed, verified company results."""
import hashlib
import json

DISCLOSURE = 'Contexto gerado por IA com conferência automática de trechos, datas e identidade, e segunda leitura por IA. Não recebeu revisão humana individual. As fontes não comprovam a causa de cada retorno.'


def signature(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def publish(root, assets, unknown, identified, results, financial_sources, week):
    ready = set(identified) & set(results)
    issuers = [*unknown, *(results[code][0] for code in sorted(ready))]
    sources = [row for row in financial_sources if row.get('cvm_code') in ready]
    for code in sorted(ready):
        sources.extend(results[code][1])
    public_fields = {'id', 'url', 'title', 'publication_date', 'date_basis', 'date_evidence',
                     'cvm_code', 'body_excerpt_offset', 'claim_evidence', 'identity_quote',
                     'identity_confirmed', 'date_verified', 'verification', 'body_sha256',
                     'after_price_end', 'before_week'}
    sources = [{key: value for key, value in row.items() if key in public_fields} for row in sources]
    company = {'schema_version': 1, 'reference_date': week['reference_date'],
               'price_end': week['last_week_close'],
               'calendar_week': {'start': week['week_start'], 'end': week['week_end']},
               'assets': assets, 'issuers': sorted(issuers, key=lambda row: row['cvm_code']),
               'sources': sorted({row['id']: row for row in sources}.values(), key=lambda row: row['id']),
               'disclosure': DISCLOSURE}
    content = {'company': company, 'completed_companies': len(ready) + len(unknown),
               'total_companies': len(identified) + len(unknown)}
    envelope = {'input_sha256': hashlib.sha256((root / 'presentation.json').read_bytes()).hexdigest(),
                'content_sha256': signature(content), 'content': content}
    path = root / 'context/progress.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(envelope, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(path)
