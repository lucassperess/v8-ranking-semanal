"""Integridade e leitura de uma revisão dos guias independente dos atuais."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from webapp.doc_revision import archive, read_snapshot
from webapp.documentation import render

ROOT = Path(__file__).resolve().parents[1]


class DocumentationRevisionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copyfile(ROOT / 'resultados/2026-09-22/ranking_report.json', self.root / 'ranking_report.json')

    def test_archive_remains_readable_after_current_guides_change(self):
        path = archive(self.root)
        original = path.read_bytes()
        snapshot = read_snapshot(self.root)
        with patch('webapp.doc_revision.current_documents', return_value={'changed': {'content': 'new'}}):
            archive(self.root)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(snapshot['mode'], 'at_completion')
        with patch('webapp.documentation.source', side_effect=AssertionError('Used current article')):
            page = render('metodologia', snapshot=snapshot, archive_base='/analise/' + 'a' * 32 + '/documentacao')
        self.assertIn(snapshot['revision'][:12], page)
        self.assertIn('registrada na conclusão', page)
        self.assertIn('/analise/' + 'a' * 32 + '/documentacao/como-usar', page)
        self.assertIn('id="docs-search" disabled', page)
        self.assertNotIn('{{', page)

    def test_changed_article_or_execution_is_rejected(self):
        path = archive(self.root, mode='reviewed_after_execution')
        snapshot = json.loads(path.read_text(encoding='utf-8'))
        snapshot['documents']['docs/metodologia.md']['content'] += ' changed'
        path.write_text(json.dumps(snapshot), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Assinatura'):
            read_snapshot(self.root)
        path.unlink()
        archive(self.root)
        report_path = self.root / 'ranking_report.json'
        report = json.loads(report_path.read_text(encoding='utf-8'))
        report['input_sha256'] = '0' * 64
        report_path.write_text(json.dumps(report), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'outra execução'):
            read_snapshot(self.root)
