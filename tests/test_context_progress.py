"""Progress publishes verified companies without waiting for every subject."""
import concurrent.futures
import json
import tempfile
import threading
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from context_pipeline.generate import Models, process_subjects
from context_pipeline.progress import publish
from context_pipeline.sources import Collector, write
from webapp.context import load_run_context

class ProgressTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.week = {'reference_date':'2026-09-22','last_week_close':'2026-09-18',
                     'week_start':'2026-09-14','week_end':'2026-09-20'}
        write(self.root / 'presentation.json', {'week':self.week, 'windows':
              {'primary':{'top20':[{'ticker':'ALFA3'}, {'ticker':'BETA3'}]}}})
        write(self.root / 'context/state.json', {'status':'processing'})
        self.assets = [{'ticker':'ALFA3','cvm_code':'1'},{'ticker':'BETA3','cvm_code':'2'}]

    def prepare_progress(self):
        issuer = {'cvm_code':'1','tickers':['ALFA3'],'coverage_status':'dated_company_context',
                  'interpretation':{'text':'verified information'},'events':[]}
        publish(self.root, self.assets, [], {'1':{},'2':{}},
                {'1':(issuer,[{'id':'accepted','body':'PRIVATE FULL TEXT','url':'https://example.org'}])}, [], self.week)

    def test_ready_company_is_public_while_other_company_is_pending(self):
        self.prepare_progress()
        result = load_run_context(self.root)
        self.assertEqual(result['status'], 'partial')
        self.assertTrue(result['processing'])
        self.assertEqual([row['cvm_code'] for row in result['company']['issuers']], ['1'])
        self.assertEqual(len(result['company']['assets']), 2)
        self.assertEqual((result['completed_companies'],result['total_companies']), (1,2))
        self.assertNotIn('PRIVATE FULL TEXT', json.dumps(result))
        self.assertFalse((self.root/'context/progress.tmp').exists())

    def test_timeout_retains_verified_context_without_claiming_pending_is_ready(self):
        self.prepare_progress()
        write(self.root/'context/state.json', {'status':'unavailable','reason':'processing_deadline_exceeded'})
        result = load_run_context(self.root)
        self.assertEqual(result['status'], 'partial')
        self.assertFalse(result['processing'])
        self.assertEqual(len(result['company']['issuers']), 1)
        self.assertIn('encerrada', result['message'])

    def test_tampering_and_another_ranking_reject_progress(self):
        self.prepare_progress()
        path = self.root/'context/progress.json'
        original = path.read_text()
        value = json.loads(original)
        value['content']['company']['issuers'][0]['interpretation']['text']='changed'
        write(path,value)
        self.assertEqual(load_run_context(self.root)['status'],'unavailable')
        path.write_text(original)
        write(self.root/'presentation.json',{'week':self.week,'windows':{'primary':{'top20':[{'ticker':'OTHER3'}]}}})
        self.assertEqual(load_run_context(self.root)['status'],'unavailable')

    def test_callback_publishes_completed_company_before_slow_company_finishes(self):
        collector=Collector(self.root/'private',{})
        models=Models(collector,Decimal('1'))
        identities={code:{'cvm_code':code,'name':code} for code in ['a','b']}
        slow_release=threading.Event()
        published=threading.Event()
        def prepare(identity, *_args, **_kwargs):
            if identity['cvm_code']=='b':
                slow_release.wait(3)
            return {'cvm_code':identity['cvm_code'],'coverage_status':'dated_company_context'}, []
        def callback(results):
            if 'a' in results and 'b' not in results:
                published.set()
        with patch('context_pipeline.generate.prepare_issuer', side_effect=prepare):
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                task=pool.submit(process_subjects,identities,collector,models,[],{}, {}, [], self.root/'diagnostics',callback)
                try:
                    self.assertTrue(published.wait(2), 'Ready company must publish while slow company is still pending')
                    self.assertFalse(task.done())
                finally:
                    slow_release.set()
                self.assertIn('b',task.result(timeout=3))
