import csv
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path

from classify_period import ClassificationError, read_bvbg, run
from resolve_period import run as resolve_with_sources


def cota(path: Path, day: str, ticker: str, spec: str, isin: str):
    line = list(" " * 245)
    for start, stop, content in [(0, 2, "01"), (2, 10, day), (12, 24, ticker.ljust(12)),
                                 (24, 27, "010"), (39, 49, spec.ljust(10)), (230, 242, isin.ljust(12))]:
        line[start:stop] = content
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("COTAHIST.TXT", "".join(line) + "\n")


def registry(path: Path, day: str, ticker: str, category: str, spec: str, isin: str):
    xml = ("<Document><BizGrp><Document><Instrm>"
           f"<RptParams><RptDtAndTm><Dt>{day}</Dt></RptDtAndTm></RptParams>"
           f"<FinInstrmAttrCmon><Sgmt>1</Sgmt><Mkt>10</Mkt><Desc>TESTE {spec}</Desc></FinInstrmAttrCmon>"
           f"<InstrmInf><EqtyInf><TckrSymb>{ticker}</TckrSymb><SctyCtgy>{category}</SctyCtgy>"
           f"<CFICd>ESVUFR</CFICd><ISIN>{isin}</ISIN></EqtyInf></InstrmInf>"
           "</Instrm></Document></BizGrp></Document>")
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(f"BVBG.028.02_{day.replace('-', '')}.xml", xml)


class PeriodClassificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.normalized = self.root / "normalized.csv"
        with self.normalized.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["ticker", "trade_date", "close", "parse_status"])
            writer.writeheader()
            for day in ("2026-09-11", "2026-09-18"):
                writer.writerow({"ticker": "TEST3", "trade_date": day, "close": "10", "parse_status": "ok"})
        self.start, self.end = date(2026, 9, 11), date(2026, 9, 18)

    def execute(self, name, b3=None, cota_files=None):
        return run(self.normalized, self.start, self.end, self.root / name,
                   b3 or [], cota_files or [], cache_dir=self.root / "cache")

    def test_cotahist_only_resolves_historical_ticker_missing_from_registry(self):
        first, last = self.root / "first.zip", self.root / "last.zip"
        cota(first, "20260911", "TEST3", "ON NM", "BRTESTACNOR1")
        cota(last, "20260918", "TEST3", "ON NM", "BRTESTACNOR1")
        summary = self.execute("output", cota_files=[first, last])
        self.assertTrue(summary["classification_gate_passed"])
        self.assertEqual(summary["confirmed_tickers"], 1)

    def test_missing_evidence_blocks_and_keeps_report(self):
        first = self.root / "first.zip"
        cota(first, "20260911", "TEST3", "ON NM", "BRTESTACNOR1")
        summary = self.execute("output", cota_files=[first])
        self.assertFalse(summary["classification_gate_passed"])
        self.assertEqual(summary["blocked_tickers"], ["TEST3"])
        self.assertTrue((self.root / "output" / "period_classification.csv").exists())

    def test_prior_registry_is_not_treated_as_exact_date_evidence(self):
        b3 = self.root / "registry.zip"
        registry(b3, "2026-09-11", "TEST3", "11", "ON NM", "BRTESTACNOR1")
        summary = self.execute("output", b3=[b3])
        self.assertFalse(summary["classification_gate_passed"])
        with (self.root / "output" / "period_classification.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(rows[0]["status"], "confirmed")
        self.assertEqual(rows[1]["status"], "unresolved")

    def test_isin_disagreement_blocks(self):
        first, last, b3 = (self.root / name for name in ("first.zip", "last.zip", "registry.zip"))
        cota(first, "20260911", "TEST3", "ON NM", "BRTESTACNOR1")
        cota(last, "20260918", "TEST3", "ON NM", "BRTESTACNOR2")
        registry(b3, "2026-09-18", "TEST3", "11", "ON NM", "BRTESTACNOR1")
        summary = self.execute("output", b3=[b3], cota_files=[first, last])
        self.assertFalse(summary["classification_gate_passed"])
        self.assertIn("conflict", summary["status_counts"])

    def test_cache_reuse_is_deterministic(self):
        b3 = self.root / "registry.zip"
        registry(b3, "2026-09-11", "TEST3", "11", "ON NM", "BRTESTACNOR1")
        first, last = self.root / "first.zip", self.root / "last.zip"
        cota(first, "20260911", "TEST3", "ON NM", "BRTESTACNOR1")
        cota(last, "20260918", "TEST3", "ON NM", "BRTESTACNOR1")
        self.execute("a", b3=[b3], cota_files=[first, last])
        self.execute("b", b3=[b3], cota_files=[first, last])
        for name in ("period_classification.csv", "b3_evidence.csv", "candidate_exclusions.csv", "classification_summary.json", "classification_manifest.json"):
            self.assertEqual((self.root / "a" / name).read_bytes(), (self.root / "b" / name).read_bytes(), name)

    def test_future_registry_rejected(self):
        b3 = self.root / "registry.zip"
        registry(b3, "2026-09-19", "TEST3", "11", "ON NM", "BRTESTACNOR1")
        with self.assertRaisesRegex(ClassificationError, "posterior"):
            self.execute("output", b3=[b3])

    def test_outer_zip_repackaging_reuses_payload_cache(self):
        direct = self.root / "direct.zip"
        registry(direct, "2026-09-11", "TEST3", "11", "ON NM", "BRTESTACNOR1")
        inner = direct.read_bytes()
        wrappers = [self.root / "outer1.zip", self.root / "outer2.zip"]
        for path, compression in zip(wrappers, (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
            with zipfile.ZipFile(path, "w", compression=compression) as outer:
                outer.writestr("IN260911.zip", inner)
        first, first_info = read_bvbg(wrappers[0], {"TEST3"}, self.root / "cache")
        second, second_info = read_bvbg(wrappers[1], {"TEST3"}, self.root / "cache")
        self.assertNotEqual(first_info["sha256"], second_info["sha256"])
        self.assertEqual(first_info["payload_sha256"], second_info["payload_sha256"])
        self.assertEqual(first[0]["instrument_type"], second[0]["instrument_type"])
        self.assertEqual(len(list((self.root / "cache").glob("*.json"))), 1)

    def test_offline_acquisition_uses_start_registry_only_when_needed(self):
        references = self.root / "references"
        references.mkdir()
        registry(references / "IN260911.zip", "2026-09-11", "TEST3", "11", "ON NM", "BRTESTACNOR1")
        registry(references / "IN260918.zip", "2026-09-18", "TEST3", "11", "ON NM", "BRTESTACNOR1")
        summary = resolve_with_sources(self.normalized, self.start, self.end,
                                       self.root / "output", references, offline=True)
        self.assertTrue(summary["classification_gate_passed"])
        self.assertTrue((self.root / "output" / "source_acquisition.json").exists())

    def test_offline_acquisition_exposes_missing_sources(self):
        references = self.root / "references"
        references.mkdir()
        summary = resolve_with_sources(self.normalized, self.start, self.end,
                                       self.root / "output", references, offline=True)
        self.assertFalse(summary["classification_gate_passed"])
        self.assertEqual(summary["blocked_tickers"], ["TEST3"])


if __name__ == "__main__":
    unittest.main()
