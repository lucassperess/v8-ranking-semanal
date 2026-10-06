import csv
import tempfile
import unittest
from pathlib import Path

from ranking_universe import code_class, run


class RankingUniverseTests(unittest.TestCase):
    def test_complete_code_rules(self):
        cases = {"VALE3": "acao_on", "B3SA3": "acao_on", "PETR4": "acao_pn", "USIM5": "acao_pn",
                 "ELET6": "acao_pn", "ABCD7": "acao_pn", "ABCD8": "acao_pn",
                 "AAPL34": "bdr", "B1CS34": "bdr", "ABCD31": "bdr", "ABCD40": "bdr",
                 "SANB11": "outro", "BOVA11": "outro", "VALE3F": "outro",
                 "ABCD13": "outro", "X3": "outro"}
        for ticker, expected in cases.items():
            with self.subTest(ticker=ticker):
                self.assertEqual(code_class(ticker), expected)

    def test_shares_need_official_confirmation_and_conflicts_block(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "period_classification.csv"
            with source.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["ticker", "price_date", "status", "instrument_type"])
                writer.writeheader()
                for ticker, statuses, kind in (
                    ("VALE3", ("confirmed", "confirmed"), "acao_on"),
                    ("PETR4", ("confirmed", "unresolved"), "acao_pn"),
                    ("AAPL34", ("unresolved", "unresolved"), ""),
                    ("SANB11", ("unresolved", "unresolved"), ""),
                    ("TEST3", ("confirmed", "confirmed"), "bdr"),
                ):
                    for day, status in zip(("2026-09-11", "2026-09-18"), statuses):
                        writer.writerow({"ticker": ticker, "price_date": day, "status": status,
                                         "instrument_type": kind if status == "confirmed" else ""})
            summary = run(source, root)
            self.assertFalse(summary["ranking_gate_passed"])
            self.assertEqual(summary["review_tickers"], ["PETR4", "TEST3"])
            with (root / "ranking_universe.csv").open(encoding="utf-8", newline="") as stream:
                rows = {row["ticker"]: row for row in csv.DictReader(stream)}
            self.assertEqual(rows["VALE3"]["decision"], "incluir")
            self.assertEqual(rows["AAPL34"]["decision"], "excluir")
            self.assertEqual(rows["SANB11"]["decision"], "excluir")
            self.assertEqual(rows["TEST3"]["decision"], "revisar")


if __name__ == "__main__":
    unittest.main()
