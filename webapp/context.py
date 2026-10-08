"""Optional, reviewed context bound to the unchanged case artifacts."""

import hashlib
import json
from pathlib import Path

CONTEXT = Path(__file__).resolve().parents[1] / 'context/case-2026-09-22'


def load_run_context(root):
    """Expose only a signed result bound to this run, never the private collection."""
    directory = root / 'context'
    try:
        state = json.loads((directory / 'state.json').read_text(encoding='utf-8'))
        if state['status'] != 'available':
            return state
        manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
        if hashlib.sha256((root / 'presentation.json').read_bytes()).hexdigest() != manifest['input_sha256']:
            raise ValueError('Context belongs to another run')
        for name in ('company.json', 'market.json', 'audit.json'):
            if hashlib.sha256((directory / name).read_bytes()).hexdigest() != manifest['files'][name]:
                raise ValueError('Context content changed')
        company = json.loads((directory / 'company.json').read_text(encoding='utf-8'))
        market = json.loads((directory / 'market.json').read_text(encoding='utf-8'))
        payload = json.loads((root / 'presentation.json').read_text(encoding='utf-8'))
        expected = {r['ticker'] for w in payload['windows'].values() for r in w['top20']}
        if (company['reference_date'] != payload['week']['reference_date'] or
                market['reference_date'] != company['reference_date'] or
                {r['ticker'] for r in company['assets']} != expected):
            raise ValueError('Context is incompatible with the ranking')
        return {'status': 'available', 'company': company, 'market': market}
    except (OSError, ValueError, KeyError, TypeError):
        return {'status': 'unavailable', 'message': 'Contexto indisponível para esta execução. O ranking e os gráficos continuam disponíveis.'}


def digest(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def load_context(featured, directory=CONTEXT):
    try:
        manifest = json.loads((directory / 'preview_manifest.json').read_text(encoding='utf-8'))
        if manifest['status'] != 'reviewed_for_local_preview_not_published':
            raise ValueError('Preview is not reviewed')
        for name, signature in manifest['context_sha256_lf'].items():
            if Path(name).name != name or digest(directory / name) != signature:
                raise ValueError('Context content changed')
        for name, signature in manifest['historical_input_sha256'].items():
            if Path(name).name != name or hashlib.sha256((featured / name).read_bytes()).hexdigest() != signature:
                raise ValueError('Context belongs to another dataset')
        company_file = manifest.get('company_file', 'company_context_v2.json')
        review_file = manifest.get('company_review_file', 'editorial_review.json')
        if company_file not in manifest['context_sha256_lf'] or review_file not in manifest['context_sha256_lf']:
            raise ValueError('Content review is not bound to the preview')
        company = json.loads((directory / company_file).read_text(encoding='utf-8'))
        review = json.loads((directory / review_file).read_text(encoding='utf-8'))
        if review.get('content_sha256_lf') and (review['content_file'] != company_file or review['content_sha256_lf'] != digest(directory / company_file)):
            raise ValueError('Review belongs to different content')
        market = json.loads((directory / 'market_context.json').read_text(encoding='utf-8'))
        if (review['status'] != 'company_content_reviewed_for_integration_not_published'
                or company['reference_date'] != market['reference_date']
                or company['reference_date'] != '2026-09-22'
                or len(company['assets']) != 24 or len(company['issuers']) != 23):
            raise ValueError('Context review is incompatible')
        return {'status': 'available', 'company': company, 'market': market}
    except (OSError, ValueError, KeyError, TypeError):
        return {'status': 'unavailable', 'message': 'O contexto revisado está indisponível para esta base. O ranking continua disponível.'}
