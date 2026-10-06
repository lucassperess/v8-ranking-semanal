import io
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path

from b3_registry import RegistryError, load_bvbg


def instrument(ticker, category, description, cfi, report="2026-09-18", market="10"):
    return (
        "<BizGrp><Document><Instrm>"
        f"<RptParams><RptDtAndTm><Dt>{report}</Dt></RptDtAndTm></RptParams>"
        f"<FinInstrmAttrCmon><Sgmt>1</Sgmt><Mkt>{market}</Mkt><Desc>{description}</Desc></FinInstrmAttrCmon>"
        f"<InstrmInf><EqtyInf><TckrSymb>{ticker}</TckrSymb><SctyCtgy>{category}</SctyCtgy>"
        f"<CFICd>{cfi}</CFICd><ISIN>BR123</ISIN></EqtyInf></InstrmInf>"
        "</Instrm></Document></BizGrp>"
    )


def nested_zip(path, morning, evening):
    inner_bytes = io.BytesIO()
    with zipfile.ZipFile(inner_bytes, "w", zipfile.ZIP_DEFLATED) as inner:
        inner.writestr("BVBG.028.02_20260918080000.xml", "<Document>" + morning + "</Document>")
        inner.writestr("BVBG.028.02_20260918180000.xml", "<Document>" + evening + "</Document>")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as outer:
        outer.writestr("IN260918.zip", inner_bytes.getvalue())


class B3RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "IN260918.zip"

    def test_eod_snapshot_types_and_unmatched(self):
        morning = instrument("TEST11", "3", "FUNDO ETF", "CEOGES")
        evening = "".join([
            instrument("TEST11", "13", "TESTE UNT N2", "EMXXXR"),
            instrument("TEST3", "11", "EMPRESAON N2", "ESVUFR"),
            instrument("TEST4", "11", "RANDON PART PN N1", "EPNNPR"),
            instrument("TEST34", "1", "EMPRESA DRN", "EDSXPR"),
            instrument("BANK11", "13", "BANCO UNT", "MCMUXR"),
            instrument("TEST99", "99", "NOVA CATEGORIA", "ZZZZZZ"),
            instrument("FRACF", "11", "EMPRESAON N2", "ESVUFR", market="20"),
        ])
        nested_zip(self.path, morning, evening)
        requested = {"TEST11", "TEST3", "TEST4", "TEST34", "TEST99", "BANK11", "FRACF", "AUSENTE"}
        result, info = load_bvbg(self.path, date(2026, 9, 22), requested)
        self.assertEqual(result["TEST11"][0], "unit")
        self.assertEqual(result["TEST3"][0], "acao_on")
        self.assertEqual(result["TEST4"][0], "acao_pn")
        self.assertEqual(result["TEST34"][0], "bdr")
        self.assertEqual(result["BANK11"][0], "unit")
        self.assertEqual(result["TEST99"][0], "categoria_oficial_nao_mapeada")
        self.assertEqual(info["unmatched_tickers"], ["AUSENTE", "FRACF"])
        self.assertEqual(info["snapshot_date"], "2026-09-18")
        self.assertIn("180000", info["xml_member"])

    def test_future_and_declared_date_guards(self):
        nested_zip(self.path, "", instrument("TEST3", "11", "TESTE ON", "ESVUFR"))
        with self.assertRaisesRegex(RegistryError, "posterior"):
            load_bvbg(self.path, date(2026, 9, 17), {"TEST3"})
        with self.assertRaisesRegex(RegistryError, "diverge"):
            load_bvbg(self.path, date(2026, 9, 22), {"TEST3"}, date(2026, 9, 19))

    def test_conflicting_records_are_unresolved(self):
        evening = instrument("TEST11", "13", "TESTE UNT N2", "EMXXXR") + instrument("TEST11", "3", "TESTE ETF", "CEOGES")
        nested_zip(self.path, "", evening)
        result, info = load_bvbg(self.path, date(2026, 9, 22), {"TEST11"})
        self.assertEqual(result["TEST11"][0], "nao_resolvido")
        self.assertEqual(info["conflicted_tickers"], ["TEST11"])


if __name__ == "__main__":
    unittest.main()
