import csv
import tempfile
import unittest
from pathlib import Path

from review_exceptions import run


class ReviewTests(unittest.TestCase):
    def test_offline_review_lists_only_unresolved_and_does_not_classify(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output = root / "normalized.csv", root / "review.csv"
            source.write_text(
                "ticker,instrument_type\nABCD11,ambiguo\nABCD11,ambiguo\nEFGH3,acao_provisoria\nIJKL3,nao_resolvido\n",
                encoding="utf-8",
            )
            count = run(source, output, None, None, 25)
            with output.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(count, 2)
            self.assertEqual({row["ticker"] for row in rows}, {"ABCD11", "IJKL3"})
            self.assertTrue(all(not row["suggested_type"] for row in rows))
            self.assertTrue(all(row["review_status"] == "pendente_validacao_humana" for row in rows))


if __name__ == "__main__":
    unittest.main()
