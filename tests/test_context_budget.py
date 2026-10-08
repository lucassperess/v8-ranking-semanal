"""Reserve isolation, concurrency, saved responses and bounded recovery."""

import concurrent.futures
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from context_pipeline.budget import BudgetLedger
from context_pipeline.diagnostics import BudgetExceeded
from context_pipeline.generate import Models, disclosed_identity, process_subjects
from context_pipeline.selection import identity_present
from context_pipeline.sources import Collector, write


class BudgetTests(unittest.TestCase):
    def test_first_company_cannot_spend_other_company_or_market_allocation(self):
        ledger = BudgetLedger('1')
        ledger.allocate(['a', 'b'], ['market'])
        ledger.reserve(Decimal('.35'), 'a', True)
        with self.assertRaises(BudgetExceeded) as error:
            ledger.reserve(Decimal('.10'), 'a', True)
        self.assertEqual(error.exception.scope, 'subject')
        ledger.reserve(Decimal('.35'), 'b', True)
        ledger.reserve(Decimal('.15'), 'market', True)
        ledger.reserve(Decimal('.10'), 'a', False)
        self.assertEqual(ledger.reserved, Decimal('.95'))

    def test_concurrent_reservations_never_exceed_total(self):
        ledger = BudgetLedger('1')
        def reserve(_):
            try:
                ledger.reserve(Decimal('.05'))
                return True
            except BudgetExceeded:
                return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(reserve, range(40))), 20)
        self.assertEqual(ledger.reserved, Decimal('1'))

    def test_invalid_reserves_cannot_increase_available_funds(self):
        for value in ['-1', 'NaN', 'Infinity']:
            with self.assertRaises(ValueError):
                BudgetLedger(value)
            with self.assertRaises(ValueError):
                BudgetLedger('1').reserve(value)

    def test_zero_companies_and_many_companies_have_bounded_allocations(self):
        for count in [0, 1, 23, 40]:
            ledger = BudgetLedger('6')
            ledger.allocate([str(i) for i in range(count)], ['m1', 'm2', 'm3'])
            self.assertLessEqual(sum(ledger.allocations.values()), ledger.total + Decimal('1e-25'))
            self.assertGreater(ledger.allocations['m1'], 0)

    def test_saved_model_response_has_no_new_reserve_or_token_charge(self):
        with tempfile.TemporaryDirectory() as folder:
            collector = Collector(folder, {})
            response = {'status': 'completed', 'output': [{'type': 'message', 'phase': 'final',
                        'content': [{'type': 'output_text', 'text': '{"ok":true}'}]}],
                        'usage': {'input_tokens': 100, 'output_tokens': 20,
                                  'input_tokens_details': {'cached_tokens': 10}}}
            models = Models(collector, Decimal('1'))
            with patch('context_pipeline.sources.request_bytes', return_value=json.dumps(response).encode()) as request:
                self.assertEqual(models.call('generate-1', 'instructions', {}, {}), {'ok': True})
                first = models.reserved
                self.assertEqual(models.call('generate-1', 'instructions', {}, {}), {'ok': True})
            self.assertEqual(request.call_count, 1)
            self.assertEqual(models.reserved, first)
            self.assertEqual(collector.api_snapshot(), {'openai': 1})
            usage = models.ledger.snapshot()
            self.assertEqual(usage['reported_input_tokens'], 100)
            self.assertEqual(usage['reported_output_tokens'], 20)
            self.assertEqual(usage['reported_cached_input_tokens'], 10)
            self.assertIsNone(usage['billing_cost_usd'])

    def test_recovery_runs_after_all_protected_subjects_and_reuses_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            collector = Collector(root / 'private', {})
            models = Models(collector, Decimal('1'))
            phases = []
            identities = {code: {'cvm_code': code, 'name': code} for code in ['a', 'b']}
            def prepare(identity, collector, scoped, documents, financial, week, **kwargs):
                code = identity['cvm_code']
                phases.append('protected' if scoped.protected else 'recovery')
                write(collector.directory / ('source-selection-' + code + '.json'),
                      {'selected_sources': [], 'issues': [], 'collection_start': '2026-06-16', 'collection_end': '2026-09-20'})
                entries = []
                try:
                    if not scoped.protected:
                        self.assertIsNotNone(kwargs['saved_sources'])
                    models.ledger.reserve(Decimal('.41') if code in identities else Decimal('.03'), code, scoped.protected)
                    status = 'dated_company_context'
                except BudgetExceeded:
                    entries.append({'reason': 'local_budget_exhausted'})
                    status = 'financial_antecedent_only'
                kwargs['diagnostics'].append({'subject': code, 'entries': entries})
                return {'coverage_status': status, 'events': []}, []
            with patch('context_pipeline.generate.prepare_issuer', side_effect=prepare):
                results = process_subjects(identities, collector, models, [], {}, {}, [], root / 'diagnostics')
            self.assertEqual(results['a'][0]['coverage_status'], 'dated_company_context')
            self.assertEqual(results['b'][0]['coverage_status'], 'dated_company_context')
            self.assertGreater(phases.index('recovery'), max(i for i, phase in enumerate(phases) if phase == 'protected'))
            self.assertLessEqual(models.reserved, Decimal('1'))

    def test_historical_name_requires_matching_cvm_and_cnpj(self):
        identity = {'cvm_code': '123', 'cnpj': '12345678000190', 'name': 'Empresa Nova', 'search_name': 'NOVA', 'tickers': ['NOVA3']}
        financial = {'filing': {'CD_CVM': '000123', 'CNPJ_CIA': '12.345.678/0001-90', 'DENOM_CIA': 'Empresa Antiga'}}
        enriched = disclosed_identity(identity, financial)
        self.assertTrue(identity_present('Empresa Antiga divulga comunicado', enriched))
        for field, value in [('CD_CVM', '999'), ('CNPJ_CIA', '98.765.432/0001-00')]:
            wrong = {'filing': {**financial['filing'], field: value}}
            self.assertNotIn('historical_names', disclosed_identity(identity, wrong))
        self.assertNotIn('historical_names', identity)

    def test_optional_deepening_is_bounded_and_preserves_financial_context(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            collector = Collector(root / 'private', {})
            models = Models(collector, Decimal('1'))
            identities = {str(i): {'cvm_code': str(i), 'name': str(i)} for i in range(6)}
            records = []
            def prepare(identity, _collector, _scoped, _documents, _financial, _week, **kwargs):
                code = identity['cvm_code']
                kwargs['diagnostics'].append({'subject': code, 'entries': []})
                replacement = kwargs.get('saved_sources') is not None
                return {'coverage_status': 'financial_antecedent_only' if code in identities else 'insufficient_evidence',
                        'events': [{'context_role': 'institutional_document'}] if replacement else [],
                        'interpretation': {'text': 'irrelevant replacement' if replacement else 'verified finance'}}, []
            with patch('context_pipeline.generate.prepare_issuer', side_effect=prepare), patch(
                    'context_pipeline.generate.deepen_sources', return_value={'selected_sources': [], 'issues': []}) as deeper:
                results = process_subjects(identities, collector, models, [], {}, {}, records, root / 'diagnostics')
            self.assertEqual(deeper.call_count, 4)
            self.assertTrue(all(results[code][0]['interpretation']['text'] == 'verified finance' for code in identities))
            self.assertEqual(sum(e['reason'] == 'deepening_subject_limit' for r in records for e in r['entries']), 2)
