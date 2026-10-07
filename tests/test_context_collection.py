import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from scripts.collect_case_context import ROOT, parse_exa, ranked_tickers, read_keys, safe_search


class ContextCollectionTests(unittest.TestCase):
    def test_case_mapping_covers_both_rankings_and_groups_taurus(self):
        config = json.loads((ROOT / 'context/case-2026-09-22/issuers.json').read_text())
        tickers = [ticker for issuer in config['issuers'] for ticker in issuer['tickers']]
        self.assertEqual(set(tickers), ranked_tickers(ROOT / 'resultados/2026-09-22'))
        self.assertEqual(len(tickers), len(set(tickers)))
        self.assertEqual(len(tickers), 24)
        self.assertEqual(len(config['issuers']), 23)
        taurus = [issuer for issuer in config['issuers'] if 'TASA3' in issuer['tickers']]
        self.assertEqual(taurus[0]['tickers'], ['TASA3', 'TASA4'])

    def test_key_file_keeps_equals_and_environment_takes_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            path.write_text('# comment\nTAVILY_API_KEY=file=value\nOPENAI_API_KEY=local\n',
                            encoding='utf-8-sig')
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'environment'}, clear=True):
                keys = read_keys(path)
            self.assertEqual(keys['TAVILY_API_KEY'], 'file=value')
            self.assertEqual(keys['OPENAI_API_KEY'], 'environment')

    def test_exa_index_results_remain_pending_review(self):
        text = ('Title: Outside the week\nURL: https://example.com/event\n'
                'Published: 2026-09-25\nHighlights:\nExample\n'
                'Title: Missing URL\nPublished: N/A\n')
        items = parse_exa(text)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['published_date'], '2026-09-25')
        self.assertEqual(items[0]['retrieval_status'], 'indexed_only_pending_page_review')

    def test_absent_key_does_not_claim_no_news(self):
        with patch('scripts.collect_case_context.request_bytes') as request:
            result = safe_search(('sample', 'query'), {}, '2026-09-14', '2026-09-20')
        request.assert_not_called()
        self.assertEqual(result['status'], 'missing_credential')

    def test_http_failure_is_distinct_and_does_not_expose_credentials(self):
        error = urllib.error.HTTPError('https://example.com', 401, 'Unauthorized', {}, None)
        with patch('scripts.collect_case_context.request_bytes', side_effect=error):
            result = safe_search(('sample', 'query'), {'TAVILY_API_KEY': 'private-test-key'},
                                 '2026-09-14', '2026-09-20')
        self.assertEqual(result['status'], 'source_failed')
        self.assertEqual(result['http_status'], 401)
        self.assertNotIn('private-test-key', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
