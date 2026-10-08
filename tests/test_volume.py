"""Volumes observados, cobertura e identidade da execução sem rede."""

import csv
import hashlib
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from webapp.volume import attach, collect, enrich
from webapp.presentation import build_presentation


class VolumeTests(unittest.TestCase):
    def test_missing_zero_invalid_and_duplicates_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'normalized.csv'
            with path.open('w', newline='', encoding='utf-8') as stream:
                writer = csv.writer(stream)
                writer.writerow(['ticker', 'trade_date', 'parse_status', 'close', 'raw_volume'])
                for day, values in [('14', ['0']), ('15', ['10']), ('16', ['']), ('17', ['-5']), ('18', ['20', '20'])]:
                    writer.writerow(['BASE3', '2026-09-' + day, 'ok', '1', '100'])
                    for value in values:
                        writer.writerow(['TEST3', '2026-09-' + day, 'ok', '', value])
                writer.writerow(['TEST3', '2026-09-11', 'ok', '1', '999'])
            week = {'week_start': '2026-09-14', 'last_week_close': '2026-09-18'}
            volume = collect(path, {'TEST3', 'NONE4'}, week, 'input', hashlib.sha256(path.read_bytes()).hexdigest())
            points = volume['series']['TEST3']
            self.assertEqual([p['volume'] for p in points], ['0', '10', None, None, None])
            self.assertEqual([p['reason'] for p in points][2:], ['missing_volume', 'invalid_volume', 'duplicate_record'])
            payload = enrich({'volume': volume, 'windows': {'primary': {'top20': [{'ticker': 'TEST3'}, {'ticker': 'NONE4'}]}}})
            stats = payload['windows']['primary']['top20'][0]['volume']
            self.assertEqual(stats['mean_daily'], '5')
            self.assertEqual(stats['valid_days'], 2)
            self.assertEqual(stats['positive_days'], 1)
            self.assertFalse(stats['complete'])
            self.assertIsNone(payload['windows']['primary']['top20'][1]['volume']['mean_daily'])
            with self.assertRaisesRegex(ValueError, 'Hash divergente'):
                collect(path, {'TEST3'}, week, 'input', 'wrong')

    def test_saved_derivative_rejects_tampering_and_other_execution(self):
        root = Path(__file__).resolve().parents[1] / 'resultados/2026-09-22'
        source = build_presentation(root, featured=True)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / 'etl_manifest.json').write_bytes((root / 'etl_manifest.json').read_bytes())
            volume = json.loads((root / 'volume_context.json').read_text(encoding='utf-8'))
            (target / 'volume_context.json').write_text(json.dumps(volume), encoding='utf-8')
            source.pop('volume')
            self.assertEqual(attach(source, target)['volume']['content_sha256'], volume['content_sha256'])
            source['volume']['series']['ESTR4'][0]['volume'] = '9999'
            with self.assertRaisesRegex(ValueError, 'não corresponde'):
                attach(source, target)
            source.pop('volume')
            source['provenance']['input_sha256'] = 'other'
            with self.assertRaisesRegex(ValueError, 'não corresponde'):
                attach(source, target)

    def test_case_volumes_do_not_change_rankings_and_share_week(self):
        root = Path(__file__).resolve().parents[1] / 'resultados/2026-09-22'
        payload = build_presentation(root, featured=True)
        main, alt = payload['windows']['primary'], payload['windows']['alternative']
        self.assertEqual(main['volume']['dates'], alt['volume']['dates'])
        self.assertEqual(main['volume']['dates'][0], '2026-09-14')
        estr = next(r for r in main['top20'] if r['ticker'] == 'ESTR4')
        self.assertEqual(Decimal(estr['volume']['mean_daily']), Decimal('1191.2'))
        self.assertEqual(main['volume']['lowest']['ticker'], 'ESTR4')
        self.assertEqual(main['volume']['highest']['ticker'], 'TASA4')
        self.assertEqual(main['volume']['incomplete_tickers'], ['MGEL4'])
        plas = next(r for r in alt['top20'] if r['ticker'] == 'PLAS3')
        self.assertEqual(plas['volume']['valid_days'], 4)
        self.assertEqual(plas['volume']['mean_daily'], '12261')
        self.assertEqual(main['mean_pct'], '17.78')
        self.assertEqual(alt['mean_pct'], '15.93')
        self.assertEqual(main['volume']['largest_move']['ticker'], 'FASA3')
