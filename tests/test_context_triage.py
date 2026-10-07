import unittest

from scripts.context_triage import check_approved_source, group_events, issuer_status


class ContextTriageTests(unittest.TestCase):
    def source(self, **changes):
        row = {'id': 'primary', 'cvm_code': '1', 'identity_confirmed': True,
               'body_reviewed': True, 'date_verified': True, 'publication_date': '2026-09-18',
               'date_basis': 'issuer_disclosure', 'date_evidence': '18/09/2026',
               'event_group': 'clarification', 'disposition': 'approved',
               'after_price_end': False, 'causal_effect_on_return': 'not_established'}
        return row | changes

    def test_wrong_company_and_snippet_cannot_be_approved(self):
        for changes in ({'identity_confirmed': False}, {'body_reviewed': False},
                        {'date_verified': False}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                check_approved_source(self.source(**changes), '2026-09-14', '2026-09-20')

    def test_missing_and_later_publication_are_not_eligible(self):
        for publication in (None, '2026-09-24'):
            with self.subTest(publication=publication), self.assertRaises(ValueError):
                check_approved_source(self.source(publication_date=publication),
                                      '2026-09-14', '2026-09-20')

    def test_no_result_does_not_hide_unresolved_research(self):
        self.assertEqual(issuer_status([{'disposition': 'pending'}]), 'insufficient_evidence')
        self.assertEqual(issuer_status([{'disposition': 'screened_out'}]),
                         'no_specific_event_in_reviewed_candidates')

    def test_sunday_revision_preserves_disclosure_timeline(self):
        sources = [self.source(), self.source(id='revision', publication_date='2026-09-20',
                                             after_price_end=True),
                   self.source(id='other-company', cvm_code='2')]
        groups = group_events(sources)
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0]['disclosure_dates'], ['2026-09-18', '2026-09-20'])
        self.assertTrue(groups[0]['has_post_price_end_disclosure'])


if __name__ == '__main__':
    unittest.main()
