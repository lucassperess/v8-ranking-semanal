"""Independent dates, source identity, optional failures and run binding."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from context_pipeline.generate import context_role, coverage_status, financial_explanation, prices, quoted_date, response_json, run, validate_event
from context_pipeline.sources import Collector, sha, write
from webapp.context import load_run_context


class RunContextTests(unittest.TestCase):
    def test_institutional_document_does_not_count_as_business_event(self):
        source = {'title': 'Estatuto Social', 'date_basis': 'cvm_delivery_catalog'}
        role = context_role(source)
        self.assertEqual(role, 'institutional_document')
        self.assertEqual(coverage_status([{'context_role': role}], None), 'institutional_context_only')
        self.assertEqual(coverage_status([{'context_role': role}], {'text': 'result'}), 'financial_antecedent_only')
        self.assertEqual(coverage_status([{'context_role': 'dated_event'}], None), 'dated_company_context')

    def test_date_evidence_handles_year_and_portuguese(self):
        self.assertEqual(quoted_date('Publicado em 2 de outubro de 2025'), {'2025-10-02'})
        self.assertEqual(quoted_date('02/10/2025 às 18h'), {'2025-10-02'})
        self.assertEqual(quoted_date('2025-10-02'), {'2025-10-02'})
        self.assertEqual(quoted_date('October 2, 2025'), {'2025-10-02'})
        self.assertEqual(quoted_date('2 October 2025'), {'2025-10-02'})
        self.assertEqual(quoted_date('02/10 e 31/02/2025'), set())

    def test_only_final_response_is_read(self):
        response = {'status': 'completed', 'output': [
            {'type': 'message', 'phase': 'commentary', 'content': [{'type': 'output_text', 'text': 'Not JSON'}]},
            {'type': 'message', 'phase': 'final_answer', 'content': [{'type': 'output_text', 'text': '{"value": 2}'}]}]}
        self.assertEqual(response_json(response), {'value': 2})
        response['status'] = 'incomplete'
        with self.assertRaises(ValueError):
            response_json(response)

    def test_source_gate_rejects_wrong_company_date_and_snippet(self):
        identity = {'name': 'Empresa Alfa SA', 'search_name': 'Empresa Alfa',
                    'tickers': ['ALFA3'], 'cvm_code': '123'}
        body = 'Empresa Alfa publicou em 02/10/2025. A empresa aprovou uma nova fábrica.'
        source = {'id': 's1', 'body': body, 'date_basis': 'body_publication_date'}
        event = {'source_id': 's1', 'publication_date': '2025-10-02', 'event_date': None,
                 'evidence_quote': 'A empresa aprovou uma nova fábrica.',
                 'identity_quote': 'Empresa Alfa', 'date_quote': '02/10/2025'}
        self.assertTrue(validate_event(event, {'s1': source}, identity, '2025-09-29', '2025-10-05')['date_verified'])
        for change in ({'publication_date': '2025-09-30'}, {'identity_quote': 'Empresa Beta'},
                       {'evidence_quote': 'A empresa comprou a concorrente.'}, {'date_quote': '02/10'}):
            with self.assertRaises(ValueError):
                validate_event({**event, **change}, {'s1': source}, identity, '2025-09-29', '2025-10-05')
        with self.assertRaises(ValueError):
            validate_event(event, {'s1': source}, identity, '2025-10-03', '2025-10-05')

    def test_cvm_delivery_uses_identity_and_catalog_date(self):
        source = {'id': 's', 'body': 'O conselho aprovou uma nova fábrica.',
                  'date_basis': 'cvm_delivery_catalog', 'publication_date': '2025-10-03',
                  'date_evidence': '2025-10-03T18:00:00', 'cvm_code': '123'}
        event = {'source_id': 's', 'publication_date': '2025-10-03', 'event_date': None,
                 'evidence_quote': source['body'], 'identity_quote': '', 'date_quote': ''}
        self.assertTrue(validate_event(event, {'s': source}, {'cvm_code': '123'}, '2025-09-29', '2025-10-05'))
        with self.assertRaises(ValueError):
            validate_event(event, {'s': source}, {'cvm_code': '999'}, '2025-09-29', '2025-10-05')

    def test_price_reading_respects_another_year_and_missing_prices(self):
        payload = {'windows': {'primary': {'start_date': '2025-09-26', 'end_date': '2025-10-03',
                                          'top20': [{'ticker': 'ALFA3'}]},
                               'alternative': {'start_date': '2025-09-30', 'end_date': '2025-10-03',
                                               'top20': [{'ticker': 'ALFA3'}]}},
                   'daily': {'series': {'ALFA3': [{'date': d, 'close': p} for d, p in
                            [('2025-09-26', '10'), ('2025-09-30', '11'), ('2025-10-01', None), ('2025-10-03', '12')]]}}}
        returns = {key: {'ALFA3': {**window, 'start_close': '10' if key == 'primary' else '11',
                                  'end_close': '12', 'return_pct': '20' if key == 'primary' else '9.0909'}}
                   for key, window in payload['windows'].items()}
        asset = prices(payload, returns)[0]
        self.assertIn('26/09/2025', asset['main']['text'])
        self.assertIn('30/09/2025', asset['alternative']['text'])
        self.assertNotIn('2026', asset['window_explanation'])
        self.assertTrue(all(r['return_pct'] is None for r in asset['alternative']['daily_comparisons']))

    def test_missing_credentials_are_explicit_without_network(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            write(root / 'presentation.json', {'week': {'reference_date': '2025-10-07'}})
            with patch('context_pipeline.sources.request_bytes', side_effect=AssertionError('No network')):
                self.assertEqual(run(root, keys={})['status'], 'unavailable')
            self.assertEqual(load_run_context(root)['status'], 'unavailable')

    def test_saved_context_cannot_move_to_another_ranking(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            payload = {'week': {'reference_date': '2025-10-07'},
                       'windows': {'primary': {'top20': [{'ticker': 'ALFA3'}]}}}
            write(root / 'presentation.json', payload)
            write(root / 'context/company.json', {'reference_date': '2025-10-07', 'assets': [{'ticker': 'ALFA3'}]})
            write(root / 'context/market.json', {'reference_date': '2025-10-07'})
            write(root / 'context/audit.json', {})
            write(root / 'context/manifest.json', {'input_sha256': sha(root / 'presentation.json'),
                'files': {name: sha(root / 'context' / name) for name in ('company.json', 'market.json', 'audit.json')}})
            write(root / 'context/state.json', {'status': 'available'})
            self.assertEqual(load_run_context(root)['status'], 'available')
            payload['week']['reference_date'] = '2025-10-14'
            write(root / 'presentation.json', payload)
            self.assertEqual(load_run_context(root)['status'], 'unavailable')

    def test_replay_never_calls_providers(self):
        with tempfile.TemporaryDirectory() as folder:
            collector = Collector(folder, {}, replay=True)
            Path(folder, 'saved.bin').write_text(json.dumps({'value': 1}))
            with patch('context_pipeline.sources.request_bytes', side_effect=AssertionError('No network')):
                self.assertEqual(collector.json('saved', 'https://example.org')['value'], 1)
                with self.assertRaises(ValueError):
                    collector.json('absent', 'https://example.org')

    def test_a_changed_query_gets_a_distinct_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            collector = Collector(folder, {})
            with patch('context_pipeline.sources.request_bytes', side_effect=[b'{"query":"first"}', b'{"query":"second"}']):
                a = collector.json('search', 'https://example.org', {'query': 'first'})
                b = collector.json('search', 'https://example.org', {'query': 'second'})
            self.assertNotEqual(a, b)
            self.assertEqual(json.loads(Path(folder, 'search.bin').read_bytes()), a)

    def test_financial_antecedent_explains_profit_turnaround(self):
        record = {'period_start': '2025-04-01', 'period_end': '2025-06-30',
                  'accounts': {'net_result': {'value_brl': '1000'}, 'prior_net_result': {'value_brl': '-2000'}}}
        text = financial_explanation(record)
        self.assertIn('Passou de prejuízo para lucro', text)
        self.assertIn('2025', text)
        record['accounts']['prior_net_result']['value_brl'] = '500'
        self.assertIn('O lucro foi maior que o do mesmo trimestre', financial_explanation(record))
