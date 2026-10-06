"""Contrato público: números do case, lacunas, fila e validação de upload."""

import io
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import etl
from webapp import store
from webapp.presentation import build_presentation, daily_context
from webapp.server import app


ROOT = Path(__file__).resolve().parents[1]


class PresentationTests(unittest.TestCase):
    def test_featured_agrees_with_pipeline(self):
        result = build_presentation(ROOT / "resultados" / "2026-09-22", featured=True)
        self.assertEqual(result["windows"]["primary"]["mean_pct"], "17.78")
        self.assertEqual(result["windows"]["primary"]["top20"][0]["ticker"], "ECOM3")
        self.assertEqual(result["windows"]["primary"]["top20"][-1]["ticker"], "DASA3")
        self.assertEqual(result["windows"]["primary"]["breadth"]["denominator"], 308)
        self.assertEqual(result["windows"]["primary"]["breadth"]["up"] + result["windows"]["primary"]["breadth"]["down"] + result["windows"]["primary"]["breadth"]["flat"], 308)
        self.assertGreaterEqual(len(result["daily"]["dates"]), 4)

    def test_missing_daily_price_stays_empty(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "normalized.csv"
            source.write_text("ticker,trade_date,close,parse_status\nABCD3,2026-09-11,10,ok\nABCD3,2026-09-14,,ok\nABCD3,2026-09-15,12,ok\n", encoding="utf-8")
            result = daily_context(source, {"ABCD3"}, "2026-09-11", "2026-09-15")
            self.assertIsNone(result["series"]["ABCD3"][1]["close"])
            self.assertIsNone(result["heatmap"]["ABCD3"][0]["return_pct"])
            self.assertIsNone(result["heatmap"]["ABCD3"][1]["return_pct"])


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
        self.assertEqual(self.client.get("/api/featured/files/economatica_original.csv").status_code, 404)
        self.assertEqual(self.client.get("/api/featured/files/top20.csv").status_code, 200)

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
        sample = (header + "\nABCD3<XBSP>,18/09/2026,1,1,1,1,1,1,1\n").encode("cp1252")
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


if __name__ == "__main__":
    unittest.main()
