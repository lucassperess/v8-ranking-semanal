import copy
import unittest

from scripts.build_case_context import financial_reading, money, price_reading, validate_context


class ContextCompilationTests(unittest.TestCase):
    def source(self):
        return {'id': 'source', 'cvm_code': '1', 'identity_confirmed': True,
                'body_reviewed': True, 'date_verified': True,
                'publication_date': '2026-09-15', 'after_price_end': False,
                'date_basis': 'official_delivery', 'date_evidence': '2026-09-15'}

    def context(self):
        return {'sources': [self.source()], 'assets': [{'ticker': 'TEST3'}],
                'issuers': [{'cvm_code': '1', 'events': [], 'financial_context': None,
                             'interpretation': {'text': 'Fato conferido.',
                                                'source_ids': ['source']}}]}

    def test_source_cannot_be_reused_for_another_company(self):
        context = self.context()
        context['sources'][0]['cvm_code'] = '2'
        with self.assertRaises(ValueError):
            validate_context(context, ['TEST3'])

    def test_sunday_disclosure_requires_explicit_later_block(self):
        context = self.context()
        context['sources'][0].update(publication_date='2026-09-20', after_price_end=True)
        with self.assertRaises(ValueError):
            validate_context(context, ['TEST3'])
        context['issuers'][0]['interpretation']['after_price_end'] = True
        validate_context(context, ['TEST3'])

    def test_duplicate_or_missing_ticker_cannot_pass_coverage(self):
        context = self.context()
        context['assets'].append(copy.deepcopy(context['assets'][0]))
        with self.assertRaises(ValueError):
            validate_context(context, ['TEST3'])
        with self.assertRaises(ValueError):
            validate_context(self.context(), ['TEST3', 'OTHER4'])

    def test_future_or_unreviewed_source_is_not_published_as_context(self):
        context = self.context()
        context['sources'][0]['publication_date'] = '2026-10-01'
        with self.assertRaises(ValueError):
            validate_context(context, ['TEST3'])
        context = self.context()
        context['sources'][0]['body_reviewed'] = False
        with self.assertRaises(ValueError):
            validate_context(context, ['TEST3'])

    def test_alternative_excludes_monday_comparison_and_retains_gap(self):
        record = {'ticker': 'TEST3',
                  'alternative': {'start_date': '2026-09-14', 'end_date': '2026-09-18',
                                  'start_close': '10', 'end_close': '11', 'return_pct': '10'},
                  'observations': {'daily_comparisons': [
                      {'start_date': '2026-09-11', 'end_date': '2026-09-14', 'return_pct': '-40'},
                      {'start_date': '2026-09-14', 'end_date': '2026-09-15', 'return_pct': '10'},
                      {'start_date': '2026-09-15', 'end_date': '2026-09-16', 'return_pct': None}]}}
        result = price_reading(record, 'alternative')
        self.assertEqual(len(result['daily_comparisons']), 2)
        self.assertEqual(result['missing_comparisons'], 1)
        self.assertNotIn('-40', result['text'])
        self.assertIn('+10,00%', result['text'])

    def test_small_revenue_does_not_get_rounded_to_zero_millions(self):
        self.assertEqual(money('3000'), 'R$ 3,00 mil')
        self.assertIsNone(financial_reading({'accounts': None}))

    def test_missing_first_week_close_explains_unavailable_alternative(self):
        record = {'ticker': 'TEST4', 'alternative': None, 'main': {'return_pct': '10'},
                  'observations': {'daily_comparisons': [
                      {'start_date': '2026-09-11', 'end_date': '2026-09-14',
                       'return_pct': None}]}}
        result = price_reading(record, 'alternative')
        self.assertEqual(result['status'], 'unavailable')
        self.assertIn('14/09/2026', result['text'])
        self.assertIn('semana completa continua', result['text'])


if __name__ == '__main__':
    unittest.main()
