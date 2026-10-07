import unittest

from scripts.build_context_evidence import account_record, price_observation, select_filing


class ContextEvidenceTests(unittest.TestCase):
    def test_filing_version_received_after_cutoff_is_excluded(self):
        rows = [{'CD_CVM': '008192', 'DT_REFER': '2026-06-30', 'VERSAO': '1',
                 'DT_RECEB': '2026-08-14'},
                {'CD_CVM': '008192', 'DT_REFER': '2026-06-30', 'VERSAO': '2',
                 'DT_RECEB': '2026-09-24'}]
        self.assertEqual(select_filing(rows, '8192', '2026-09-18')['VERSAO'], '1')

    def test_quarter_is_not_confused_with_half_year_and_units_are_converted(self):
        common = {'CD_CVM': '008192', 'DT_REFER': '2026-06-30', 'VERSAO': '1',
                  'CD_CONTA': '3.11', 'ORDEM_EXERC': 'ÚLTIMO', 'MOEDA': 'REAL',
                  'ESCALA_MOEDA': 'MIL', 'DS_CONTA': 'Lucro consolidado',
                  'DT_FIM_EXERC': '2026-06-30'}
        rows = [common | {'DT_INI_EXERC': '2026-01-01', 'VL_CONTA': '4826'},
                common | {'DT_INI_EXERC': '2026-04-01', 'VL_CONTA': '3183'}]
        result = account_record(rows, common, '3.11', '2026-04-01')
        self.assertEqual(result['value_brl'], '3183000')

    def test_duplicate_account_does_not_silently_choose_a_number(self):
        row = {'CD_CVM': '8192', 'DT_REFER': '2026-06-30', 'VERSAO': '1',
               'CD_CONTA': '3.11', 'ORDEM_EXERC': 'ÚLTIMO'}
        with self.assertRaises(ValueError):
            account_record([row, row], row, '3.11')

    def test_missing_close_does_not_create_a_return_across_the_gap(self):
        rows = [{'date': '2026-09-14', 'close': '10'},
                {'date': '2026-09-15', 'close': None},
                {'date': '2026-09-16', 'close': '12'}]
        result = price_observation(rows)
        self.assertEqual(result['missing_comparisons'], 2)
        self.assertIsNone(result['strongest_up_day'])

    def test_all_negative_days_do_not_get_called_an_up_day(self):
        rows = [{'date': '2026-09-14', 'close': '10'},
                {'date': '2026-09-15', 'close': '9'}]
        self.assertIsNone(price_observation(rows)['strongest_up_day'])


if __name__ == '__main__':
    unittest.main()
