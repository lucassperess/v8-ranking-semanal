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
