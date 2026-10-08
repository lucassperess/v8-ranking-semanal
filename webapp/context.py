"""Optional, reviewed context bound to the unchanged case artifacts."""

import hashlib
import json
from pathlib import Path

CONTEXT = Path(__file__).resolve().parents[1] / 'context/case-2026-09-22'


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
        company = json.loads((directory / 'company_context_v2.json').read_text(encoding='utf-8'))
        review = json.loads((directory / 'editorial_review.json').read_text(encoding='utf-8'))
        market = json.loads((directory / 'market_context.json').read_text(encoding='utf-8'))
        if (review['status'] != 'company_content_reviewed_for_integration_not_published'
                or company['reference_date'] != market['reference_date']
                or company['reference_date'] != '2026-09-22'
                or len(company['assets']) != 24 or len(company['issuers']) != 23):
            raise ValueError('Context review is incompatible')
        return {'status': 'available', 'company': company, 'market': market}
    except (OSError, ValueError, KeyError, TypeError):
        return {'status': 'unavailable', 'message': 'O contexto revisado está indisponível para esta base. O ranking continua disponível.'}
