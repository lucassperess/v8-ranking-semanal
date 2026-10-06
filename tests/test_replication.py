"""Envio, revisão explícita e execução integral com fontes artificiais locais."""

import csv
import io
import json
import sqlite3
import tempfile
import unittest
import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import etl
from webapp import store, worker
from webapp.review import review_week
from webapp.server import app
from weekly_ranking import select_week


def extraction(end='2026-09-17', *, count=24, last_count=None, bump=0):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(etl.SOURCE_COLUMNS)
    for index, day in enumerate(('2026-09-11', '2026-09-14', end)):
        for number in range((last_count or count) if index == 2 else count):
            price = str(Decimal(10) + Decimal(number + bump) / 10 * index)
            writer.writerow([f'Q{number:03d}3<XBSP>', day, price, '1', price, price, price, price, price])
    return output.getvalue().encode('utf-8')


def local_sources(folder, end='2026-09-17', *, missing=False):
    """Arquivos artificiais nunca são enviados à VPS ou apresentados como B3 real."""
    folder.mkdir(parents=True)
    for day in ('2026-09-11', '2026-09-14', end):
        name = f'COTAHIST_D{date.fromisoformat(day):%d%m%Y}.ZIP'
        lines = []
        for number in range(24):
            line = list(' ' * 245)
            for start, stop, value in ((0, 2, '01'), (2, 10, day.replace('-', '')),
                                       (12, 24, f'Q{number:03d}3'.ljust(12)), (24, 27, '010'),
                                       (39, 49, 'ON NM'.ljust(10)), (230, 242, f'BR{number:010d}')):
                line[start:stop] = value
            lines.append(''.join(line))
        if missing:
            (folder / name).write_text('invalid cache', encoding='utf-8')
        else:
            with zipfile.ZipFile(folder / name, 'w') as archive:
                archive.writestr('COTAHIST.TXT', '\n'.join(lines) + '\n')
    # Cadastro e COTAHIST artificiais confirmam as mesmas ações.
    for day in ('2026-09-11', end):
        name = f'IN{date.fromisoformat(day):%y%m%d}.zip'
        if missing:
            (folder / name).write_text('invalid cache', encoding='utf-8')
        else:
            with zipfile.ZipFile(folder / name, 'w') as archive:
                instruments = ''.join(
                    '<BizGrp><Document><Instrm>'
                    f'<RptParams><RptDtAndTm><Dt>{day}</Dt></RptDtAndTm></RptParams>'
                    '<FinInstrmAttrCmon><Sgmt>1</Sgmt><Mkt>10</Mkt><Desc>TESTE ON NM</Desc></FinInstrmAttrCmon>'
                    f'<InstrmInf><EqtyInf><TckrSymb>Q{number:03d}3</TckrSymb><SctyCtgy>11</SctyCtgy>'
                    f'<CFICd>ESVUFR</CFICd><ISIN>BR{number:010d}</ISIN></EqtyInf></InstrmInf>'
                    '</Instrm></Document></BizGrp>' for number in range(24))
                archive.writestr(f'BVBG.028.02_{day.replace("-", "")}.xml', '<Document>' + instruments + '</Document>')


class ReplicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for name, value in (('DATA_DIR', self.root), ('DB_PATH', self.root / 'jobs.sqlite3')):
            item = patch.object(store, name, value)
            item.start()
            self.addCleanup(item.stop)
        self.client = TestClient(app)

    def send(self, raw, **options):
        return self.client.post('/api/analyses', data={'reference_date': '2026-09-22', **options},
                                files={'file': ('test.csv', raw, 'text/csv')})

    def confirmation(self, response):
        review = response.json()['detail']['review']
        return {'allow_nonfriday_end': 'true', 'reviewed_sha256': review['input_sha256'],
                'reviewed_reference_date': review['reference_date']}

    def test_short_week_requires_review_and_keeps_no_upload_or_job(self):
        response = self.send(extraction())
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['detail']['code'], 'short_week_review')
        self.assertEqual(response.json()['detail']['review']['week']['last_week_close'], '2026-09-17')
        self.assertEqual(list((self.root / 'uploads').glob('*.csv')), [])
        self.assertIsNone(store.next_job())
        self.assertEqual(self.send(extraction(), allow_nonfriday_end='true').status_code, 409)

    def test_changed_input_or_reference_requires_new_review(self):
        raw = extraction()
        confirmation = self.confirmation(self.send(raw))
        self.assertEqual(self.send(extraction(bump=2), **confirmation).status_code, 409)
        confirmation['reviewed_reference_date'] = '2026-09-21'
        self.assertEqual(self.send(raw, **confirmation).status_code, 409)
        self.assertIsNone(store.next_job())

    def test_acceptance_never_bypasses_coverage_and_date_controls(self):
        response = self.send(extraction(last_count=1), allow_nonfriday_end='true')
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['detail']['code'], 'coverage')
        response = self.send(extraction(), reference_date='2026-08-04')
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['detail']['code'], 'dates')
        self.assertIsNone(store.next_job())

    def test_regular_extractions_remain_independent(self):
        first = self.send(extraction('2026-09-18'))
        second = self.send(extraction('2026-09-18', bump=2))
        self.assertEqual((first.status_code, second.status_code), (202, 202))
        self.assertNotEqual(first.json()['id'], second.json()['id'])
        self.assertNotEqual(store.get_job(first.json()['id'])['input_sha256'],
                            store.get_job(second.json()['id'])['input_sha256'])
        self.assertFalse(store.get_job(first.json()['id'])['options']['allow_nonfriday_end'])

    def test_worker_runs_same_pipeline_and_records_short_week_decision(self):
        raw = extraction()
        accepted = self.send(raw, **self.confirmation(self.send(raw)))
        self.assertEqual(accepted.status_code, 202, accepted.text)
        job_id = accepted.json()['id']
        local_sources(self.root / 'reference')
        worker.process(store.next_job())  # Processo Python real, duas janelas, sem rede.
        result = self.client.get(f'/api/analyses/{job_id}/result')
        self.assertEqual(result.status_code, 200, result.text)
        payload = result.json()
        self.assertEqual(len(payload['windows']['primary']['top20']), 20)
        self.assertEqual(payload['windows']['primary']['mean_pct'], '27.00')
        self.assertEqual(payload['windows']['alternative']['mean_pct'], '11.67')
        self.assertTrue(payload['week']['nonfriday_end_accepted'])
        self.assertTrue(payload['submission']['options']['accepted_at'])
        self.assertEqual(payload['submission']['options']['reviewed_week'], payload['week'])
        request = self.client.get(f'/api/analyses/{job_id}/files/analysis_request.json')
        self.assertEqual(request.json(), payload['submission'])
        readme = self.client.get(f'/api/analyses/{job_id}/files/README.md').text
        self.assertIn('--allow-nonfriday-end', readme)
        self.assertEqual(self.client.get(f'/api/analyses/{job_id}/files/economatica_original.csv').status_code, 404)
        # Um registro de outro arquivo não pode ser usado na auditoria.
        path = self.root / 'runs' / job_id / 'analysis_request.json'
        record = json.loads(path.read_text(encoding='utf-8'))
        record['input_sha256'] = '0' * 64
        path.write_text(json.dumps(record), encoding='utf-8')
        self.assertEqual(self.client.get(f'/api/analyses/{job_id}/result').status_code, 503)

    def test_missing_official_sources_fail_with_actionable_message(self):
        raw = extraction('2026-09-18')
        response = self.send(raw)
        job_id = response.json()['id']
        local_sources(self.root / 'reference', '2026-09-18', missing=True)
        with self.assertRaisesRegex(RuntimeError, 'Classificação pendente') as failure:
            worker.process(store.next_job())
        store.update_job(job_id, status='failed', stage='Falhou', error=str(failure.exception))
        state = self.client.get(f'/api/analyses/{job_id}').json()
        self.assertEqual(state['problem']['code'], 'classification')
        self.assertIn('fontes B3', state['problem']['guidance'])
        self.assertEqual(self.client.get(f'/api/analyses/{job_id}/result').status_code, 409)

    def test_existing_database_migration_preserves_old_jobs(self):
        with sqlite3.connect(store.DB_PATH) as con:
            con.execute('CREATE TABLE jobs (id TEXT PRIMARY KEY,reference_date TEXT,input_sha256 TEXT,client_ip TEXT,status TEXT,stage TEXT,error TEXT,created_at TEXT,updated_at TEXT)')
            con.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)',
                        ('a' * 32, '2026-09-22', 'b' * 64, 'old', 'queued', 'Aguardando', None, store.stamp(), store.stamp()))
        con.close()
        store.initialize()
        store.initialize()
        self.assertEqual(store.get_job('a' * 32)['options'], {})
        self.assertEqual(store.next_job()['options'], {})

    def test_batched_review_matches_full_etl_coverage(self):
        path = self.root / 'sample.csv'
        path.write_bytes(extraction(count=900))
        rows, _ = etl.read_economatica(path)
        _records, _issues, summary = etl.transform(rows, date(2026, 9, 22), {}, Decimal('0.25'))
        expected = select_week([(date.fromisoformat(row['date']), row['positive_close']) for row in summary['dates']], date(2026, 9, 22), True)
        self.assertEqual(review_week(rows, date(2026, 9, 22)), expected)
