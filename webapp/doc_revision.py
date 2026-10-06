"""Cópia verificável dos guias aplicáveis, separada dos resultados numéricos."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _revision(documents: dict) -> str:
    return _hash(json.dumps(documents, ensure_ascii=False, sort_keys=True, separators=(',', ':')))


def current_documents() -> dict:
    paths = [ROOT / 'README.md', *sorted((ROOT / 'docs').glob('*.md'))]
    return {path.relative_to(ROOT).as_posix(): {'content': path.read_text(encoding='utf-8'),
            'sha256': _hash(path.read_text(encoding='utf-8'))} for path in paths}


def current_revision() -> str:
    return _revision(current_documents())


def archive(root: Path, *, mode: str = 'at_completion') -> Path:
    """Não sobrescreve uma associação existente nem modifica o relatório."""
    if mode not in {'at_completion', 'reviewed_after_execution'}:
        raise ValueError('Modo de associação inválido')
    target = root / 'documentation_snapshot.json'
    if target.exists():
        read_snapshot(root)
        return target
    report = json.loads((root / 'ranking_report.json').read_text(encoding='utf-8'))
    documents = current_documents()
    payload = {'schema_version': 1, 'revision': _revision(documents), 'documents': documents,
               'associated_at': datetime.now(timezone.utc).isoformat(), 'mode': mode,
               'execution': {key: report[key] for key in ('input_sha256', 'code_sha256', 'version')}}
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    return target


def read_snapshot(root: Path) -> dict | None:
    target = root / 'documentation_snapshot.json'
    if not target.is_file():
        return None
    snapshot = json.loads(target.read_text(encoding='utf-8'))
    try:
        documents = snapshot['documents']
        if (snapshot['schema_version'] != 1 or snapshot['revision'] != _revision(documents)
                or any(item['sha256'] != _hash(item['content']) for item in documents.values())):
            raise ValueError('Assinatura da documentação divergente')
        report = json.loads((root / 'ranking_report.json').read_text(encoding='utf-8'))
        if snapshot['execution'] != {key: report[key] for key in ('input_sha256', 'code_sha256', 'version')}:
            raise ValueError('Documentação associada a outra execução')
        if snapshot['mode'] not in {'at_completion', 'reviewed_after_execution'}:
            raise ValueError('Modo de associação inválido')
    except (KeyError, TypeError):
        raise ValueError('Registro da documentação incompleto') from None
    return snapshot


def details(root: Path) -> dict:
    snapshot = read_snapshot(root)
    if not snapshot:
        return {'available': False, 'note': 'Esta execução não registrou uma revisão dos guias. '
                'A documentação atual pode ter mudado; confira as regras no relatório desta execução.'}
    return {key: snapshot[key] for key in ('revision', 'associated_at', 'mode')} | {'available': True}
