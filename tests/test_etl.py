import csv
import hashlib
import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

from etl import InputError, SOURCE_COLUMNS, run


CASE_FILE = Path(os.environ["ECONOMATICA_CASE_CSV"]) if os.environ.get("ECONOMATICA_CASE_CSV") else None


def make_csv(path: Path, rows: list[list[str]], encoding: str = "utf-8", header=None) -> None:
    with path.open("w", newline="", encoding=encoding) as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(SOURCE_COLUMNS if header is None else header)
        writer.writerows(rows)


def codes(path: Path) -> list[str]:
    with path.open(encoding="utf-8", newline="") as stream:
        return [row["code"] for row in csv.DictReader(stream)]


class ETLTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.csv"
        self.reference = date(2026, 9, 22)

    def execute(self, name="output", **kwargs):
        target = self.root / name
        run(self.source, self.reference, target, **kwargs)
        return target

    def test_utf8_and_cp1252(self):
        row = ["ABCD3<XBSP>", "2026-09-21", "10.25", "100", "10", "11", "9", "10.25", "1025"]
        for encoding in ("utf-8", "cp1252"):
            make_csv(self.source, [row], encoding=encoding)
            output = self.execute(encoding)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["input_encoding"], "utf-8-sig" if encoding == "utf-8" else "cp1252")
            with (output / "normalized.csv").open(encoding="utf-8", newline="") as stream:
                record = next(csv.DictReader(stream))
            self.assertEqual(record["ticker"], "ABCD3")
            self.assertEqual(record["close"], "10.25")
            self.assertEqual(record["instrument_type"], "acao_provisoria")

    def test_schema_failure_leaves_no_output(self):
        make_csv(self.source, [], header=SOURCE_COLUMNS[:-1])
        with self.assertRaisesRegex(InputError, "Esquema inesperado"):
            self.execute()
        self.assertFalse((self.root / "output").exists())

    def test_malformed_duplicate_future_negative_and_range(self):
        row = ["ABCD3<XBSP>", "2026-09-21", "10", "100", "10", "11", "9", "12", "1000"]
        future = ["EFGH11<XBSP>", "2026-09-23", "1", "2", "1", "1", "1", "1", "2"]
        make_csv(self.source, [row, row, [*row[:2], "-5", *row[3:]], future])
        with self.source.open("a", encoding="utf-8") as stream:
            stream.write('"IJKL3<XBSP>","2026-09-21",1,2,3\n')
        output = self.execute()
        found = codes(output / "quality_issues.csv")
        for code in ("DUPLICATE_CONFLICT", "MALFORMED_ROW", "OUTSIDE_DAILY_RANGE", "NONPOSITIVE_PRICE", "FUTURE_DATE", "INSTRUMENT_AMBIGUOUS"):
            self.assertIn(code, found)
        self.assertEqual(json.loads((output / "quality_summary.json").read_text(encoding="utf-8"))["rows_output"], 5)

    def test_holiday_missing_quotes_and_coverage(self):
        rows = []
        for index in range(60):
            rows.append([f"A{index:03d}3<XBSP>", "2026-09-04", "10", "1", "10", "10", "10", "10", "10"])
            rows.append([f"A{index:03d}3<XBSP>", "2026-09-07", "-", "-", "-", "-", "-", "-", "-"])
        make_csv(self.source, rows)
        found = codes(self.execute() / "quality_issues.csv")
        self.assertIn("COVERAGE_DROP", found)
        self.assertEqual(found.count("MISSING_VALUE"), 60 * 7)

    def test_b3_registry_and_temporal_guard(self):
        make_csv(self.source, [["ABCD11<XBSP>", "2026-09-21", "10", "1", "10", "10", "10", "10", "10"]])
        b3 = self.root / "b3.csv"
        b3.write_text("RptDt;TckrSymb;SctyCtgyNm\n2026-09-21;ABCD11;UNIT\n", encoding="utf-8")
        output = self.execute("with_b3", b3_path=b3)
        with (output / "normalized.csv").open(encoding="utf-8", newline="") as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual((row["instrument_type"], row["classification_source"]), ("unit", "b3"))
        b3.write_text("RptDt;TckrSymb;SctyCtgyNm\n2026-09-23;ABCD11;UNIT\n", encoding="utf-8")
        with self.assertRaisesRegex(InputError, "posterior"):
            self.execute("future_b3", b3_path=b3)

    def test_official_unknown_category_is_not_replaced_by_ticker_heuristic(self):
        make_csv(self.source, [["ABCD3<XBSP>", "2026-09-21", "10", "1", "10", "10", "10", "10", "10"]])
        b3 = self.root / "b3.csv"
        b3.write_text("RptDt;TckrSymb;SctyCtgyNm\n2026-09-01;ABCD3;Categoria nova\n", encoding="utf-8")
        output = self.execute(b3_path=b3)
        with (output / "normalized.csv").open(encoding="utf-8", newline="") as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual((row["instrument_type"], row["classification_source"]), ("categoria_oficial_nao_mapeada", "b3"))
        self.assertIn("B3_CATEGORY_UNRESOLVED", codes(output / "quality_issues.csv"))
        self.assertIn("B3_STALE_SNAPSHOT", codes(output / "quality_issues.csv"))

    def test_empty_b3_still_marks_unmatched(self):
        make_csv(self.source, [["ABCD3<XBSP>", "2026-09-21", "10", "1", "10", "10", "10", "10", "10"]])
        b3 = self.root / "b3.csv"
        b3.write_text("ticker,category\n", encoding="utf-8")
        output = self.execute(b3_path=b3, b3_snapshot_date=date(2026, 9, 21))
        self.assertIn("B3_TICKER_UNMATCHED", codes(output / "quality_issues.csv"))

    def test_later_snapshot_does_not_classify_historical_row(self):
        make_csv(self.source, [["ABCD3<XBSP>", "2026-09-11", "10", "1", "10", "10", "10", "10", "10"]])
        b3 = self.root / "b3.csv"
        b3.write_text("RptDt;TckrSymb;SctyCtgyNm\n2026-09-18;ABCD3;SHARES\n", encoding="utf-8")
        output = self.execute(b3_path=b3)
        with (output / "normalized.csv").open(encoding="utf-8", newline="") as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual((row["instrument_type"], row["classification_source"]), ("nao_resolvido", "snapshot_posterior"))
        self.assertIn("B3_SNAPSHOT_AFTER_TRADE_DATE", codes(output / "quality_issues.csv"))

    def test_approved_override_only_for_unresolved_asset(self):
        make_csv(self.source, [["ABCD11<XBSP>", "2026-09-21", "10", "1", "10", "10", "10", "10", "10"]])
        override = self.root / "overrides.csv"
        override.write_text(
            "ticker,category,source_url,approved_by,approved_at,reason\n"
            "ABCD11,unit,https://www.b3.com.br/exemplo,Analista,2026-09-22,Documento oficial\n",
            encoding="utf-8",
        )
        output = self.execute(overrides_path=override)
        with (output / "normalized.csv").open(encoding="utf-8", newline="") as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual((row["instrument_type"], row["classification_source"]), ("unit", "manual_approved"))

    def test_previous_extraction_coverage_drop(self):
        rows = [[f"AB{i:02d}3<XBSP>", "2026-09-18", "10", "1", "10", "10", "10", "10", "10"] for i in range(60)]
        make_csv(self.source, rows)
        baseline = self.execute("baseline") / "quality_summary.json"
        make_csv(self.source, rows[:30])
        current = self.execute("current", baseline_summary=baseline)
        self.assertIn("EXTRACTION_COVERAGE_DROP", codes(current / "quality_issues.csv"))
        manifest = json.loads((current / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["baseline_summary"]["baseline_latest_positive_close"], 60)

    def test_case_is_complete_and_deterministic(self):
        if CASE_FILE is None or not CASE_FILE.exists():
            self.skipTest("Defina ECONOMATICA_CASE_CSV para validar a extração original")
        self.source = CASE_FILE
        first = self.execute("first")
        second = self.execute("second")
        for filename in ("normalized.csv", "quality_issues.csv", "quality_by_date.csv", "quality_summary.json", "manifest.json"):
            self.assertEqual((first / filename).read_bytes(), (second / filename).read_bytes(), filename)
        source_hash = hashlib.sha256(CASE_FILE.read_bytes()).hexdigest()
        self.assertEqual(hashlib.sha256((first / "economatica_original.csv").read_bytes()).hexdigest(), source_hash)
        summary = json.loads((first / "quality_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["rows_input"], 4828)
        self.assertEqual(summary["rows_output"], 4828)
        self.assertEqual(summary["distinct_tickers"], 478)
        self.assertEqual(summary["missing_close"], 1278)
        self.assertEqual(summary["records_on_1920_01_02"], 43)
        self.assertEqual(summary["quantity_and_volume_without_any_price"], 9)
        self.assertNotIn("DUPLICATE_CONFLICT", summary["issue_counts"])


if __name__ == "__main__":
    unittest.main()
