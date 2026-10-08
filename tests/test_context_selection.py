"""Independent company matching, temporal selection and continuous passages."""

import unittest

from context_pipeline.selection import identity_present, readable_excerpt, select_candidates, select_documents


class SelectionTests(unittest.TestCase):
    identity = {'cvm_code': '123', 'name': 'Empresa Alfa S.A.', 'search_name': 'ALFA', 'tickers': ['ALFA3']}

    def test_social_quotes_wrong_company_and_duplicates_do_not_take_slots(self):
        candidates = [
            {'url': 'https://www.tiktok.com/video/1', 'title': 'ALFA3 aquisição'},
            {'url': 'https://news.example/cotacoes/alfa3', 'title': 'ALFA3'},
            {'url': 'https://news.example/beta', 'title': 'Empresa Beta aquisição'},
            {'url': 'https://news.example/alfa', 'title': 'Empresa Alfa aprova aquisição'},
            {'url': 'https://news.example/alfa', 'title': 'Empresa Alfa aprova aquisição'},
        ]
        selected, rejected = select_candidates(candidates, self.identity)
        self.assertEqual([r['url'] for r in selected], ['https://news.example/alfa'])
        self.assertEqual(len(rejected), 4)

    def test_identity_uses_words_not_substrings(self):
        self.assertFalse(identity_present('Alfabeto e ALFA30 subiram', self.identity))
        self.assertTrue(identity_present('Comunicado da Empresa Alfa S.A.', self.identity))
        self.assertTrue(identity_present('Ação ALFA3', self.identity))

    def test_abbreviated_part_suffix_does_not_hide_company_results(self):
        identity = {'name': 'Plascar Participações Industriais S.A.', 'search_name': 'PLASCAR PART', 'tickers': ['PLAS3']}
        self.assertTrue(identity_present('Plascar divulga comunicado', identity))
        self.assertFalse(identity_present('Plascart divulga comunicado', identity))

    def test_malformed_url_is_rejected_without_losing_valid_candidates(self):
        selected, rejected = select_candidates([
            {'url': 'https://[broken', 'title': 'Alfa contrato'},
            {'url': 'https://news.example/alfa', 'title': 'Alfa contrato', 'content': None},
        ], self.identity)
        self.assertEqual(len(selected), 1)
        self.assertEqual(rejected[0]['reason'], 'invalid_source_url')

    def test_profiles_dividend_agendas_and_result_tables_are_not_news(self):
        rows = [{'url': url, 'title': 'Empresa Alfa ALFA3'} for url in [
            'https://valor.globo.com/empresas/valor-empresas-360/alfa',
            'https://example.org/ultimos-resultados',
            'https://example.org/acoes/dividendos/2026/junho/data-de-pagamento',
            'https://example.org/acoes/alfa3/',
            'https://dadosb3.com/acoes',
            'https://arquivos.b3.com.br/bdi/download/bdi/2026-08-03/BDI_02_20260803.pdf',
            'https://example.org/noticia/alfa-aprova-contrato',
        ]]
        selected, rejected = select_candidates(rows, self.identity)
        self.assertEqual(len(selected), 1)
        self.assertEqual(len(rejected), 6)

    def test_official_search_result_still_requires_identity(self):
        selected, _ = select_candidates([
            {'url': 'https://ri.beta.example/fato', 'title': 'Empresa Beta contrato'},
            {'url': 'https://news.example/alfa', 'title': 'Alfa aquisição'},
            {'url': 'https://ri.alfa.example/fato', 'title': 'Alfa contrato'},
        ], self.identity)
        self.assertEqual(selected[0]['url'], 'https://ri.alfa.example/fato')
        self.assertEqual(len(selected), 2)

    def test_macro_does_not_require_company_but_filters_social(self):
        selected, _ = select_candidates([
            {'url': 'https://news.example/copom', 'title': 'Copom decide juros'},
            {'url': 'https://x.com/copom', 'title': 'Copom decide juros'},
        ], {}, macro=True)
        self.assertEqual(len(selected), 1)

    def row(self, day, category='Fato Relevante', code='123', url=None):
        return {'Codigo_CVM': code, 'Data_Entrega': day + 'T12:00:00',
                'Link_Download': url or 'https://example.org/' + day,
                'Categoria': category, 'Assunto': '', 'Tipo': ''}

    def test_official_selection_has_weekly_and_prior_without_future_or_wrong_issuer(self):
        rows = [self.row('2026-09-15'), self.row('2026-09-10'), self.row('2026-06-01'),
                self.row('2026-09-21'), self.row('2026-09-16', code='999')]
        selected = select_documents(rows, '123', '2026-06-16', '2026-09-14', '2026-09-20')
        self.assertEqual([r['Data_Entrega'][:10] for r in selected], ['2026-09-15', '2026-09-10'])

    def test_business_document_precedes_institutional_and_limit_preserves_prior_slots(self):
        rows = [self.row('2026-09-18', 'Estatuto Social')]
        rows += [self.row(f'2026-09-{day}') for day in (17, 16, 15, 14, 13, 12)]
        selected = select_documents(rows, '123', '2026-06-16', '2026-09-14', '2026-09-20')
        self.assertEqual(len(selected), 5)
        self.assertEqual(sum(r['Data_Entrega'][:10] < '2026-09-14' for r in selected), 2)
        self.assertNotIn('Estatuto Social', [r['Categoria'] for r in selected])

    def test_repeated_catalog_link_is_not_read_twice(self):
        rows = [self.row('2026-09-15', url='https://example.org/same'),
                self.row('2026-09-16', url='https://example.org/same')]
        selected = select_documents(rows, '123', '2026-06-16', '2026-09-14', '2026-09-20')
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['Data_Entrega'][:10], '2026-09-16')

    def test_excerpt_skips_long_menu_and_is_literal_continuous(self):
        menu = ('Buscar fazer login ebook planilha gratis newsletter\n' * 100)
        article = 'Publicado em 15/09/2026. Empresa Alfa informou aquisição, contrato e recuperação judicial. '
        body = menu + article * 35
        excerpt, offset = readable_excerpt(body, self.identity)
        self.assertGreater(offset, 0)
        self.assertEqual(excerpt, body[offset:offset + 3000])
        self.assertIn('15/09/2026', excerpt)
        self.assertIn('Empresa Alfa', excerpt)
        self.assertNotIn('[...]', excerpt)
