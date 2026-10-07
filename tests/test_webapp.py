"""Contrato público: números do case, lacunas, fila e validação de upload."""

import io
import json
import re
import shutil
import tempfile
import unittest
from copy import deepcopy
from decimal import Decimal
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import etl
from webapp import store
from webapp.presentation import DOWNLOADS, audit_details, build_presentation, daily_context, enrich_daily_windows, enrich_interpretation, output_path
from webapp.server import app


ROOT = Path(__file__).resolve().parents[1]


class PresentationTests(unittest.TestCase):
    def test_audit_scope_and_type_decisions(self):
        result = audit_details(ROOT / "resultados" / "2026-09-22", featured=True)
        self.assertTrue(result["available"])
        self.assertEqual(result["summary"]["rows_input"], result["summary"]["rows_output"])
        main = result["windows"]["primary"]
        self.assertEqual(len(main["type_exclusions"]), 12)
        self.assertEqual(sum(row["official_types"] == "unit" for row in main["type_exclusions"]), 9)
        counts = {row["code"]: row for row in main["issue_counts"]}
        self.assertEqual(counts["OUTSIDE_DAILY_RANGE"]["file_occurrences"], 11)
        self.assertEqual(counts["OUTSIDE_DAILY_RANGE"]["endpoint_occurrences"], 3)
        self.assertEqual(counts["OUTSIDE_DAILY_RANGE"]["top20_occurrences"], 1)
        bied = next(row for row in main["eligible_issues"] if row["ticker"] == "BIED3")
        self.assertEqual(bied["field"], "average")
        self.assertIn("não este campo", bied["impact"])
        self.assertNotEqual(main["dates"], result["windows"]["alternative"]["dates"])

    def test_audit_rejects_changed_evidence_and_reports_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = ROOT / "resultados" / "2026-09-22"
            for name in DOWNLOADS:
                if (source / name).is_file():
                    shutil.copyfile(source / name, root / name)
            (root / "b3_evidence.csv").write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Hash divergente"):
                audit_details(root, featured=True)
            (root / "b3_evidence.csv").unlink()
            audit = audit_details(root, featured=True)
            self.assertFalse(audit["available"])
            self.assertIn("b3_evidence.csv", audit["missing_files"])

    def test_featured_agrees_with_pipeline(self):
        result = build_presentation(ROOT / "resultados" / "2026-09-22", featured=True)
        self.assertEqual(result["windows"]["primary"]["mean_pct"], "17.78")
        self.assertEqual(result["windows"]["primary"]["top20"][0]["ticker"], "ECOM3")
        self.assertEqual(result["windows"]["primary"]["top20"][-1]["ticker"], "DASA3")
        self.assertEqual(result["windows"]["primary"]["breadth"]["denominator"], 308)
        self.assertEqual(result["windows"]["primary"]["breadth"]["up"] + result["windows"]["primary"]["breadth"]["down"] + result["windows"]["primary"]["breadth"]["flat"], 308)
        self.assertGreaterEqual(len(result["daily"]["dates"]), 4)
        alt = result['windows']['alternative']
        self.assertEqual(alt['mean_pct'], '15.93')
        self.assertEqual(alt['daily']['dates'][0], '2026-09-14')
        for window in result['windows'].values():
            for row in window['top20']:
                prices = window['daily']['series'][row['ticker']]
                self.assertEqual(prices[0]['close'], row['start_close'])
                self.assertEqual(prices[-1]['close'], row['end_close'])
        self.assertIsNone(alt['daily']['heatmap']['ECOM3'][0]['return_pct'])
        self.assertEqual(alt['daily']['heatmap']['ECOM3'][0]['reason'], 'window_start')
        self.assertEqual(alt['daily']['heatmap']['ECOM3'][1]['previous_date'], '2026-09-14')

    def test_window_series_with_other_year_holiday_and_short_week(self):
        # First date is Tuesday; end is Thursday. No dates from the case.
        dates = ['2025-04-17', '2025-04-22', '2025-04-23', '2025-04-24']
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'normalized.csv'
            lines = ['ticker,trade_date,close,parse_status']
            for ticker, prices in {'TEST3': ['10', '11', '11.5', '12'],
                                   'GAPS4': ['10', '11', '', '12']}.items():
                lines += [f'{ticker},{day},{price},ok' for day, price in zip(dates, prices)]
            source.write_text('\n'.join(lines), encoding='utf-8')
            daily = daily_context(source, {'TEST3', 'GAPS4'}, dates[0], dates[-1])
        original = deepcopy(daily)
        payload = {'daily': daily, 'windows': {
            key: {'start_date': start, 'end_date': dates[-1],
                  'top20': [{'ticker': 'TEST3'}, {'ticker': 'GAPS4'}]}
            for key, start in [('primary', dates[0]), ('alternative', dates[1])]}}
        enrich_daily_windows(payload)
        self.assertEqual(daily, original)
        main = payload['windows']['primary']['daily']
        alt = payload['windows']['alternative']['daily']
        self.assertEqual(main['return_dates'], dates[1:])
        self.assertEqual(alt['dates'], dates[1:])
        self.assertEqual(alt['return_dates'], dates[1:])
        self.assertEqual(Decimal(main['heatmap']['TEST3'][0]['return_pct']), Decimal('10'))
        self.assertIsNone(alt['heatmap']['TEST3'][0]['return_pct'])
        self.assertIsNone(alt['heatmap']['TEST3'][0]['previous_date'])
        self.assertEqual(alt['heatmap']['TEST3'][0]['reason'], 'window_start')
        for point in alt['heatmap']['GAPS4'][1:]:
            self.assertIsNone(point['return_pct'])
            self.assertEqual(point['reason'], 'missing_comparison')
        for context, start in [(main, Decimal('10')), (alt, Decimal('11'))]:
            compound = Decimal('1')
            for point in context['heatmap']['TEST3']:
                if point['return_pct'] is not None:
                    compound *= 1 + Decimal(point['return_pct']) / 100
            self.assertAlmostEqual(compound, Decimal('12') / start, places=25)
        before = deepcopy(payload)
        enrich_daily_windows(payload)
        self.assertEqual(payload, before)

    def test_unavailable_daily_series_is_not_fabricated(self):
        payload = {'daily': {'dates': [], 'series': {}, 'heatmap': {}}, 'windows': {
            'alternative': {'start_date': '2025-04-22', 'end_date': '2025-04-24',
                            'top20': [{'ticker': 'TEST3'}]}}}
        enrich_daily_windows(payload)
        self.assertEqual(payload['windows']['alternative']['daily']['dates'], [])
        self.assertEqual(payload['windows']['alternative']['daily']['heatmap']['TEST3'], [])

    def test_missing_daily_price_stays_empty(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "normalized.csv"
            source.write_text("ticker,trade_date,close,parse_status\nABCD3,2026-09-11,10,ok\nABCD3,2026-09-14,,ok\nABCD3,2026-09-15,12,ok\n", encoding="utf-8")
            result = daily_context(source, {"ABCD3"}, "2026-09-11", "2026-09-15")
            self.assertIsNone(result["series"]["ABCD3"][1]["close"])
            self.assertIsNone(result["heatmap"]["ABCD3"][0]["return_pct"])
            self.assertIsNone(result["heatmap"]["ABCD3"][1]["return_pct"])

    def test_interpretation_decimal_and_window_isolation(self):
        def window(ticker, start, end, change, issues):
            return {'top20': [{'ticker': ticker, 'start_close': start, 'end_close': end,
                              'return_pct': change}], 'quality': {'top20_issues': issues}}
        issue = {'ticker': 'TEST3', 'field': 'average', 'trade_date': '2026-09-11',
                 'code': 'OUTSIDE_DAILY_RANGE', 'reason': 'Valor fora do intervalo mínimo–máximo'}
        payload = {'windows': {
            'primary': window('TEST3', '0.10000001', '0.10000002', '0.00001', [issue]),
            'alternative': window('TEST3', '1.1', '1.0', '-9.0909', []),
        }}
        result = enrich_interpretation(payload)
        main = result['windows']['primary']
        alt = result['windows']['alternative']
        self.assertEqual(main['top20'][0]['change_brl'], '1E-8')
        self.assertEqual(alt['top20'][0]['change_brl'], '-0.1')
        self.assertEqual(main['interpretation']['low_initial_price_count'], 1)
        self.assertEqual(alt['interpretation']['low_initial_price_count'], 0)
        self.assertEqual(main['interpretation']['alerted_tickers'], ['TEST3'])
        self.assertEqual(alt['top20'][0]['issues'], [])
        self.assertEqual(main['top20'][0]['return_pct'], '0.00001')


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.data = Path(self.temporary.name)
        self.patches = [patch.object(store, "DATA_DIR", self.data), patch.object(store, "DB_PATH", self.data / "jobs.sqlite3")]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        self.client = TestClient(app)

    def test_featured_and_private_raw(self):
        result = self.client.get("/api/featured")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["windows"]["primary"]["mean_pct"], "17.78")
        self.assertTrue(result.json()['documentation']['available'])
        self.assertEqual(result.json()['documentation']['mode'], 'reviewed_after_execution')
        archived = self.client.get('/documentacao/referencia/metodologia')
        self.assertEqual(archived.status_code, 200)
        self.assertIn('Cópia arquivada', archived.text)
        self.assertEqual(self.client.get("/api/featured/files/economatica_original.csv").status_code, 404)
        self.assertEqual(self.client.get("/api/featured/files/top20.csv").status_code, 200)
        for name in result.json()["downloads"]:
            self.assertEqual(self.client.get(f"/api/featured/files/{name}").status_code, 200, name)
        for name in ("normalized.csv", "IN260918.zip", "presentation.json", "../etl/normalized.csv"):
            self.assertEqual(self.client.get(f"/api/featured/files/{name}").status_code, 404, name)

    def test_completed_job_exposes_its_own_audit_and_legacy_payload(self):
        job_id = "d" * 32
        store.create_job(job_id, "2026-09-22", "b" * 64, "test-client")
        root = self.data / "runs" / job_id
        source = ROOT / "resultados" / "2026-09-22"
        for name in DOWNLOADS:
            if not (source / name).is_file():
                continue
            target = output_path(root, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, target)
        payload = build_presentation(source, featured=True)
        payload.pop("audit")  # Execuções concluídas antes desta ampliação.
        for window in payload['windows'].values():
            window.pop('daily')  # Séries antigas não eram separadas por janela.
            window.pop('interpretation')
            window.pop('quality')
            for row in window['top20']:
                row.pop('change_brl')
                row.pop('issues')
        saved = json.dumps(payload)
        (root / "presentation.json").write_text(saved, encoding="utf-8")
        store.update_job(job_id, status="completed", stage="Concluída")
        response = self.client.get(f"/api/analyses/{job_id}/result")
        self.assertTrue(response.json()["audit"]["available"])
        self.assertEqual(self.client.get(f'/analise/{job_id}/documentacao/como-usar').status_code, 200)
        self.assertEqual(response.json()['windows']['primary']['top20'][0]['change_brl'], '0.50')
        self.assertIn('interpretation', response.json()['windows']['alternative'])
        alt_daily = response.json()['windows']['alternative']['daily']
        self.assertEqual(alt_daily['dates'][0], '2026-09-14')
        self.assertIsNone(alt_daily['heatmap']['ECOM3'][0]['return_pct'])
        self.assertEqual((root / 'presentation.json').read_text(encoding='utf-8'), saved)
        for name in response.json()["downloads"]:
            self.assertEqual(self.client.get(f"/api/analyses/{job_id}/files/{name}").status_code, 200)
        self.assertEqual(self.client.get(f"/api/analyses/{job_id}/files/normalized.csv").status_code, 404)

    def test_retention_removes_both_raw_copies_and_keeps_audit(self):
        job_id = "e" * 32
        store.create_job(job_id, "2026-09-22", "b" * 64, "test-client")
        store.update_job(job_id, status="completed", stage="Concluída")
        paths = [self.data / "uploads" / f"{job_id}.csv",
                 self.data / "runs" / job_id / "etl" / "economatica_original.csv"]
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("private input", encoding="utf-8")
        evidence = paths[1].parent / "quality_issues.csv"
        evidence.write_text("derived audit", encoding="utf-8")
        with store.db() as con:
            con.execute("UPDATE jobs SET created_at=? WHERE id=?", (store.stamp(store.now() - timedelta(hours=25)), job_id))
        store.cleanup()
        self.assertTrue(all(not path.exists() for path in paths))
        self.assertTrue(evidence.exists())

    def test_dedicated_pages_and_execution_methodology(self):
        ranking = self.client.get("/")
        self.assertNotIn('id="upload-form"', ranking.text)
        self.assertNotIn('id="method-list"', ranking.text)
        self.assertEqual(self.client.get("/metodologia").status_code, 200)
        upload = self.client.get("/nova-analise")
        self.assertEqual(upload.status_code, 200)
        self.assertIn('id="upload-form"', upload.text)
        store.create_job("a" * 32, "2026-09-22", "b" * 64, "test-client")
        self.assertEqual(self.client.get(f"/analise/{'a' * 32}/metodologia").status_code, 200)
        self.assertEqual(self.client.get(f"/analise/{'c' * 32}/metodologia").status_code, 404)
        self.assertEqual(self.client.get("/analise/invalid/metodologia").status_code, 404)

    def test_shared_header_has_one_active_link_and_no_template_markers(self):
        from html.parser import HTMLParser

        class HeaderParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.header = False
                self.active = []
                self.buttons = 0

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "header":
                    self.header = True
                if self.header and tag == "a" and attrs.get("aria-current") == "page":
                    self.active.append(attrs["href"])
                if attrs.get("id") == "fullscreen-button":
                    self.buttons += 1

            def handle_endtag(self, tag):
                if tag == "header":
                    self.header = False

        for route, expected in (("/", "/"), ("/metodologia", "/documentacao"),
                                ("/documentacao/metodologia", "/documentacao"),
                                ("/nova-analise", "/nova-analise"), (f"/analise/{'a' * 32}", "/")):
            response = self.client.get(route)
            parser = HeaderParser()
            parser.feed(response.text)
            self.assertEqual(parser.active, [expected], route)
            self.assertEqual(parser.buttons, 1, route)
            self.assertNotIn("{{", response.text, route)

    def test_documentation_links_sections_and_original_audit(self):
        from webapp.documentation import PAGES
        for slug in PAGES:
            response = self.client.get(f"/documentacao/{slug}")
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("{{", response.text)
            ids = set(re.findall(r'id="([^"]+)"', response.text))
            for fragment in re.findall(r'href="#([^"]+)"', response.text):
                self.assertIn(fragment, ids, (slug, fragment))
            for route in re.findall(r'href="(/documentacao[^"?#]*)', response.text):
                self.assertEqual(self.client.get(route).status_code, 200, route)
        method = self.client.get('/documentacao/metodologia').text
        self.assertIn('class="docs-flow"', method)
        self.assertNotIn('class="language-mermaid"', method)
        self.assertIn('47,17%', method)
        self.assertEqual(self.client.get('/documentacao/desconhecida').status_code, 404)
        self.assertEqual(self.client.get('/documentacao').status_code, 200)
        home = self.client.get('/documentacao').text
        self.assertIn('id="docs-context" class="docs-context" hidden', home)
        self.assertNotIn('Regras e guias da ferramenta', home)
        self.assertNotIn('Antes de interpretar', home)
        self.assertIn('Como funciona uma nova análise', home)
        self.assertIn('9,09%', home)
        archived = self.client.get('/documentacao/referencia/comece-aqui').text
        self.assertIn('data-archived="true"', archived)
        self.assertIn('Cópia arquivada desta execução', archived)
        self.assertIn('associada após revisão', archived)
        index = self.client.get('/api/documentation').json()
        self.assertEqual(len(index), len(PAGES))
        self.assertTrue(any('células vazias' in article['text'] for article in index))
        ranking = self.client.get('/').text
        self.assertNotIn('<footer>', ranking)
        self.assertIn('id="execution-audit"', ranking)
        self.assertIn('href="/documentacao"', ranking)

    def test_bad_upload_rejected_with_clear_message(self):
        response = self.client.post("/api/analyses", data={"reference_date": "2026-09-22"},
                                    files={"file": ("wrong.csv", b"ticker,date\nAAA3,2026-09-18\n", "text/csv")})
        self.assertEqual(response.status_code, 422)
        self.assertIn("Esquema inesperado", response.json()["detail"])
        self.assertEqual(list((self.data / "uploads").glob("*.csv")), [])

    def test_valid_upload_is_queued_and_isolated(self):
        original = Path(tempfile.gettempdir()) / "does-not-exist.csv"
        header = ",".join(etl.SOURCE_COLUMNS)
        sample = (header + "\n" + "\n".join(f"ABCD3<XBSP>,{day},1,1,1,1,1,1,1" for day in ("2026-09-11", "2026-09-14", "2026-09-18")) + "\n").encode("cp1252")
        first = self.client.post("/api/analyses", data={"reference_date": "2026-09-22"},
                                 files={"file": ("other.csv", sample, "text/csv")})
        self.assertEqual(first.status_code, 202, first.text)
        job_id = first.json()["id"]
        self.assertEqual(len(job_id), 32)
        self.assertEqual(self.client.get(f"/api/analyses/{job_id}").json()["status"], "queued")
        self.assertEqual(self.client.get(f"/api/analyses/{job_id}/result").status_code, 409)
        self.assertEqual(self.client.get(f"/api/analyses/{job_id}/files/economatica_original.csv").status_code, 409)
        self.assertTrue((self.data / "uploads" / f"{job_id}.csv").exists())
        self.assertFalse(original.exists())

    def test_global_queue_limit(self):
        store.initialize()
        for index in range(3):
            store.create_job(f"{index:032x}", "2026-09-22", "a" * 64, f"client-{index}")
        with self.assertRaises(store.LimitError):
            store.create_job("f" * 32, "2026-09-22", "b" * 64, "another")

    def test_origin_limit_expires_after_one_hour(self):
        for index in range(3):
            job_id = f"{index:032x}"
            store.create_job(job_id, "2026-09-22", "a" * 64, "same-origin")
            store.update_job(job_id, status="completed")
        with self.assertRaisesRegex(store.LimitError, "por hora"):
            store.check_limits("same-origin")
        with self.assertRaisesRegex(store.LimitError, "por hora"):
            store.create_job("f" * 32, "2026-09-22", "a" * 64, "same-origin")
        store.check_limits("different-origin")
        with store.db() as con:
            con.execute("UPDATE jobs SET created_at=? WHERE id=?",
                        (store.stamp(store.now() - timedelta(minutes=61)), "0" * 32))
        store.create_job("f" * 32, "2026-09-22", "a" * 64, "same-origin")

    def test_results_expire_after_seven_days_without_removing_recent_runs(self):
        for job_id, age in (("a" * 32, 8), ("b" * 32, 6)):
            store.create_job(job_id, "2026-09-22", "a" * 64, "origin")
            store.update_job(job_id, status="completed")
            root = self.data / "runs" / job_id
            root.mkdir(parents=True)
            (root / "top20.csv").write_text("derived", encoding="utf-8")
            with store.db() as con:
                con.execute("UPDATE jobs SET created_at=? WHERE id=?",
                            (store.stamp(store.now() - timedelta(days=age)), job_id))
        store.cleanup()
        self.assertFalse((self.data / "runs" / ("a" * 32)).exists())
        self.assertTrue((self.data / "runs" / ("b" * 32) / "top20.csv").exists())
        response = self.client.get(f"/api/analyses/{'a' * 32}/result")
        self.assertEqual(response.status_code, 410)
        self.assertIn("expirou", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
