import csv
import json
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from b3_registry import digest
from weekly_ranking import RankingError, choose_week, rank_pair


class WeeklyRankingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_previous_calendar_week_uses_prior_close_and_ignores_current_week(self):
        quality = self.root / "quality_by_date.csv"
        quality.write_text("date,positive_close\n2026-09-04,12\n2026-09-07,0\n"
                           "2026-09-08,348\n2026-09-09,335\n2026-09-10,339\n"
                           "2026-09-11,338\n2026-09-14,336\n2026-09-15,340\n"
                           "2026-09-16,334\n2026-09-17,334\n2026-09-18,329\n"
                           "2026-09-21,343\n", encoding="utf-8")
        chosen = choose_week(quality, date(2026, 9, 22))
        self.assertEqual((chosen["preceding_close"], chosen["first_week_close"], chosen["last_week_close"]),
                         ("2026-09-11", "2026-09-14", "2026-09-18"))
        self.assertGreater(chosen["recent_median_positive_closes"], 300)

    def test_short_or_partial_week_needs_review(self):
        quality = self.root / "quality_by_date.csv"
        quality.write_text("date,positive_close\n2026-09-11,300\n2026-09-14,300\n"
                           "2026-09-15,300\n2026-09-17,1\n", encoding="utf-8")
        with self.assertRaisesRegex(RankingError, "antes de sexta"):
            choose_week(quality, date(2026, 9, 22))
        with self.assertRaisesRegex(RankingError, "Cobertura insuficiente"):
            choose_week(quality, date(2026, 9, 22), allow_nonfriday_end=True)

    def test_return_order_mean_and_quality_context(self):
        classification = self.root / "classification"
        classification.mkdir()
        start, end = date(2026, 9, 11), date(2026, 9, 18)
        with (classification / "period_classification.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["ticker", "price_date", "close", "status", "instrument_type"])
            writer.writeheader()
            for i in range(22):
                ticker = f"T{i:03d}3"
                writer.writerow({"ticker": ticker, "price_date": str(start), "close": "10", "status": "confirmed", "instrument_type": "acao_on"})
                writer.writerow({"ticker": ticker, "price_date": str(end), "close": str(Decimal(10) + Decimal(i) / 10), "status": "confirmed", "instrument_type": "acao_on"})
        with (classification / "ranking_universe.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["ticker", "decision", "code_class"])
            writer.writeheader()
            for i in range(22):
                writer.writerow({"ticker": f"T{i:03d}3", "decision": "incluir", "code_class": "acao_on"})
        (classification / "classification_summary.json").write_text(
            json.dumps({"start_date": str(start), "end_date": str(end), "ranking_gate_passed": True}), encoding="utf-8")
        manifest = {"outputs": {name: digest(classification / name) for name in
                                ("period_classification.csv", "ranking_universe.csv", "classification_summary.json")}}
        (classification / "classification_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        issues = self.root / "quality_issues.csv"
        issues.write_text("ticker,trade_date,field,code,severity,reason\n"
                          "T0213,2026-09-18,average,OUTSIDE_DAILY_RANGE,warning,média fora da faixa\n", encoding="utf-8")
        result = rank_pair(classification, start, end, self.root / "ranked", issues)
        self.assertEqual(result["mean_return_pct_display"], "11.50")
        with (self.root / "ranked" / "top20.csv").open(encoding="utf-8", newline="") as stream:
            top = list(csv.DictReader(stream))
        self.assertEqual((top[0]["ticker"], top[-1]["ticker"]), ("T0213", "T0023"))
        context = json.loads((self.root / "ranked" / "quality_context.json").read_text(encoding="utf-8"))
        self.assertEqual(context["top20_issues"][0]["ticker"], "T0213")


if __name__ == "__main__":
    unittest.main()
