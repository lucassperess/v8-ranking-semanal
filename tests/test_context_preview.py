import json
import tempfile
import unittest
from pathlib import Path
from shutil import copytree

from scripts.build_market_context import pair
from webapp.context import CONTEXT, load_context
from webapp.server import FEATURED, app
from fastapi.testclient import TestClient


class ContextPreviewTests(unittest.TestCase):
    def test_reviewed_context_covers_both_rankings(self):
        with TestClient(app) as client:
            context = client.get('/api/featured/context').json()
            ranking = client.get('/api/featured').json()
        self.assertEqual(context['status'], 'available')
        tickers = {row['ticker'] for row in context['company']['assets']}
        for window in ranking['windows'].values():
            self.assertTrue({row['ticker'] for row in window['top20']} <= tickers)
        self.assertEqual(len(context['market']['indicators']), 4)
        for issuer in context['company']['issuers']:
            self.assertTrue(issuer['interpretation']['text'])
            self.assertEqual(issuer['causal_effect_on_return'], 'not_established')

    def test_changed_or_missing_content_is_optional(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'context'
            copytree(CONTEXT, target)
            market = target / 'market_context.json'
            data = json.loads(market.read_text(encoding='utf-8'))
            data['events'][0]['text'] = 'Changed without review'
            market.write_text(json.dumps(data), encoding='utf-8')
            self.assertEqual(load_context(FEATURED, target)['status'], 'unavailable')
            market.unlink()
            self.assertEqual(load_context(FEATURED, target)['status'], 'unavailable')
        self.assertEqual(load_context(Path(directory))['status'], 'unavailable')

    def test_line_endings_do_not_invalidate_editorial_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'context'
            copytree(CONTEXT, target)
            for path in target.glob('*.json'):
                path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n'))
            self.assertEqual(load_context(FEATURED, target)['status'], 'available')

    def test_market_comparisons_require_exact_positive_endpoints(self):
        self.assertEqual(pair({'a': '100', 'b': '110'}, 'a', 'b')['change_pct'], '10.0')
        with self.assertRaises(ValueError):
            pair({'a': '100', 'b': '110'}, 'missing', 'b')
        with self.assertRaises(ValueError):
            pair({'a': '0', 'b': '110'}, 'a', 'b')


if __name__ == '__main__':
    unittest.main()
