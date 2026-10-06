import csv
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path

from verify_b3 import verify


class CotaHistVerificationTests(unittest.TestCase):
    def test_reports_mismatch_without_changing_input(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            normalized = root / "normalized.csv"
            with normalized.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["ticker", "instrument_type"])
                writer.writeheader()
                writer.writerow({"ticker": "TEST3", "instrument_type": "acao_on"})
            line = "01" + "20260918" + "02" + "TEST3".ljust(12) + "010" + "EMPRESA".ljust(12) + "PN".ljust(10)
            archive = root / "COTAHIST.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("COTAHIST.TXT", line + "\n")
            report = verify(normalized, archive, date(2026, 9, 18))
            self.assertEqual(report["traded_tickers_compared"], 1)
            self.assertEqual(report["mismatches"], [{"ticker": "TEST3", "b3_xml_type": "acao_on", "cotahist_spec": "PN"}])
            with self.assertRaisesRegex(ValueError, "Data COTAHIST divergente"):
                verify(normalized, archive, date(2026, 9, 17))


if __name__ == "__main__":
    unittest.main()
