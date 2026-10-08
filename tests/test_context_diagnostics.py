"""Distinguish unavailable evidence from blocked processing without API calls."""

import json
import tempfile
import unittest
import urllib.error
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

from context_pipeline.diagnostics import BudgetExceeded, Trace
from context_pipeline.generate import Models, prepare_issuer


class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.identity = {'cvm_code': '123', 'name': 'Empresa Alfa', 'search_name': 'ALFA', 'tickers': ['ALFA3']}
        self.week = {'week_start': '2026-09-14', 'week_end': '2026-09-20', 'last_week_close': '2026-09-18'}
        self.source = {'id': 'doc-1', 'url': 'https://example.org/doc', 'title': 'Comunicado',
                       'body': 'A Empresa Alfa aprovou uma proposta de aquisição.',
                       'publication_date': '2026-09-15', 'cvm_code': '123',
                       'date_basis': 'cvm_delivery_catalog', 'date_evidence': '2026-09-15'}
        self.event = {'source_id': 'doc-1', 'title': 'Proposta', 'text': self.source['body'],
                      'evidence_quote': self.source['body'], 'publication_date': '2026-09-15',
                      'event_date': None, 'identity_quote': '', 'date_quote': ''}
        self.collector = Mock(directory=self.root)
        self.collector.search.return_value = []
        self.collector.extract.return_value = [self.source.copy()]
        self.models = Mock()
        self.records = []

    def prepare(self):
        return prepare_issuer(self.identity, self.collector, self.models, [], None, self.week,
                              diagnostics=self.records, diagnostic_dir=self.root / 'diagnostics')

    def entries(self):
        saved = json.loads((self.root / 'diagnostics/123.json').read_text())
        self.assertEqual(saved, self.records[0])
        return saved['entries']

    def test_review_budget_block_is_not_reported_as_empty_generation(self):
        self.models.call.side_effect = [
            {'events': [self.event], 'interpretation': 'Proposta', 'unresolved_question': ''},
            BudgetExceeded('local limit')]
        issuer, _ = self.prepare()
        entries = self.entries()
        self.assertIn({'stage': 'review', 'outcome': 'blocked', 'reason': 'local_budget_exhausted',
                       'error_type': 'BudgetExceeded'}, entries)
        self.assertTrue(any(r['reason'] == 'event_verified' for r in entries))
        self.assertFalse(any(r['reason'] == 'model_proposed_no_events' for r in entries))
        self.assertEqual(issuer['events'], [])

    def test_quote_rejection_and_model_review_rejection_are_separate(self):
        bad = {**self.event, 'evidence_quote': 'Trecho que não existe no documento original.'}
        self.models.call.side_effect = [
            {'events': [bad, self.event], 'interpretation': '', 'unresolved_question': ''},
            {'events': [self.event], 'interpretation': '', 'unresolved_question': ''},
            {'accepted_event_indices': [], 'interpretation_supported': False, 'reason': 'unsupported'}]
        self.prepare()
        reasons = {r['reason'] for r in self.entries()}
        self.assertIn('quote_not_found', reasons)
        self.assertIn('model_review_rejected', reasons)

    def test_missing_event_source_is_identified(self):
        bad = {**self.event, 'source_id': 'unknown'}
        self.models.call.side_effect = [
            {'events': [bad], 'interpretation': '', 'unresolved_question': ''},
            {'events': [], 'interpretation': '', 'unresolved_question': ''},
            {'accepted_event_indices': [], 'interpretation_supported': False, 'reason': ''}]
        self.prepare()
        self.assertTrue(any(r['reason'] == 'unknown_source_id' for r in self.entries()))

    def test_empty_collection_does_not_call_model(self):
        self.collector.extract.return_value = []
        self.prepare()
        self.models.call.assert_not_called()
        self.assertTrue(any(r['reason'] == 'no_selected_sources' for r in self.entries()))

    def test_financial_source_in_event_is_not_an_unknown_news_source(self):
        financial = {'source_ids': ['itr-123'], 'period_start': '2026-04-01',
                     'period_end': '2026-06-30', 'accounts': {'net_result': {'value_brl': '1000'}}}
        self.models.call.side_effect = [
            {'events': [{**self.event, 'source_id': 'itr-123'}], 'interpretation': '', 'unresolved_question': ''},
            {'events': [], 'interpretation': '', 'unresolved_question': ''},
            {'accepted_event_indices': [], 'interpretation_supported': False, 'reason': ''}]
        prepare_issuer(self.identity, self.collector, self.models, [], financial, self.week,
                       diagnostics=self.records, diagnostic_dir=self.root / 'diagnostics')
        self.assertTrue(any(r['reason'] == 'financial_source_used_as_event' for r in self.entries()))

    def test_http_failure_preserves_status_without_leaking_exception(self):
        self.collector.search.side_effect = urllib.error.HTTPError(
            'https://example.org?api_key=SECRET', 429, 'SECRET', {}, None)
        self.prepare()
        saved = json.dumps(self.records)
        self.assertNotIn('SECRET', saved)
        self.assertNotIn('api_key', saved)
        self.assertTrue(any(r.get('http_status') == 429 for r in self.entries()))

    def test_budget_blocks_before_provider_call(self):
        collector = Mock(directory=self.root)
        models = Models(collector, budget=Decimal('0'))
        with self.assertRaises(BudgetExceeded):
            models.call('generate-123', 'instructions', {}, {})
        collector.json.assert_not_called()

    def test_incremental_trace_survives_without_final_result(self):
        trace = Trace('123', self.root / 'trace.json')
        trace.record('generation', 'started', 'stage_started')
        saved = json.loads((self.root / 'trace.json').read_text())
        self.assertEqual(saved['entries'][0]['outcome'], 'started')

    def test_literal_quote_repair_is_verified_before_review(self):
        bad = {**self.event, 'evidence_quote': 'A Empresa Alfa [...] uma proposta de aquisição.'}
        self.models.call.side_effect = [
            {'events': [bad], 'interpretation': '', 'unresolved_question': ''},
            {'events': [self.event], 'interpretation': '', 'unresolved_question': ''},
            {'accepted_event_indices': [0], 'interpretation_supported': False, 'reason': ''}]
        issuer, _ = self.prepare()
        self.assertEqual(len(issuer['events']), 1)
        review_input = self.models.call.call_args_list[-1].args[2]
        self.assertEqual(review_input['proposal']['events'][0]['evidence_quote'], self.source['body'])
        self.assertTrue(any(r['reason'] == 'quote_not_found' for r in self.entries()))

    def test_repair_cannot_make_an_unsupported_quote_valid(self):
        bad = {**self.event, 'evidence_quote': 'A empresa concluiu a aquisição e recebeu dinheiro.'}
        self.models.call.side_effect = [
            {'events': [bad], 'interpretation': '', 'unresolved_question': ''},
            {'events': [bad], 'interpretation': '', 'unresolved_question': ''},
            {'accepted_event_indices': [], 'interpretation_supported': False, 'reason': ''}]
        issuer, _ = self.prepare()
        self.assertEqual(issuer['events'], [])
        self.assertEqual(self.models.call.call_args_list[-1].args[2]['proposal']['events'], [])

    def test_cvm_metadata_date_is_explicit_and_does_not_require_pdf_date(self):
        self.models.call.side_effect = [
            {'events': [], 'interpretation': '', 'unresolved_question': 'No date in body'},
            {'events': [self.event], 'interpretation': '', 'unresolved_question': ''},
            {'accepted_event_indices': [0], 'interpretation_supported': False, 'reason': ''}]
        issuer, _ = self.prepare()
        request = self.models.call.call_args_list[0].args[2]
        self.assertEqual(request['source_publication_rules']['doc-1'],
                         {'kind': 'official_cvm', 'publication_date': '2026-09-15',
                          'requires_date_quote_in_body': False})
        self.assertEqual(issuer['events'][0]['publication_date'], '2026-09-15')

    def test_repair_preserves_original_valid_event(self):
        bad = {**self.event, 'source_id': 'unknown'}
        self.models.call.side_effect = [
            {'events': [self.event, bad], 'interpretation': '', 'unresolved_question': ''},
            {'events': [], 'interpretation': '', 'unresolved_question': ''},
            {'accepted_event_indices': [0], 'interpretation_supported': False, 'reason': ''}]
        issuer, _ = self.prepare()
        self.assertEqual(len(issuer['events']), 1)
