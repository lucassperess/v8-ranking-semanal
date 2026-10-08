"""Regression: financial processing must not consume the context deadline."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from webapp import worker

class ContextDeadlineTests(unittest.TestCase):
    def test_context_has_its_own_clock_after_long_ranking(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            child = Mock(returncode=0)
            child.poll.side_effect = [None, 0]
            with patch.object(worker.subprocess, 'Popen', return_value=child), patch.object(worker.time, 'monotonic', side_effect=[1000, 1001]), patch.object(worker.time, 'sleep'), patch.object(worker, 'STOP', False):
                worker.prepare_context(root, root / 'run.log')
            child.terminate.assert_not_called()
            child.kill.assert_not_called()

    def test_context_deadline_terminates_child_and_preserves_ranking(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'presentation.json').write_text('unchanged ranking', encoding='utf-8')
            child = Mock(returncode=-15)
            child.poll.return_value = None
            with patch.object(worker.subprocess, 'Popen', return_value=child), patch.object(worker.time, 'monotonic', side_effect=[1000, 1000 + worker.CONTEXT_TIMEOUT_SECONDS + 1]), patch.object(worker, 'STOP', False):
                worker.prepare_context(root, root / 'run.log')
            child.terminate.assert_called_once()
            state = json.loads((root / 'context/state.json').read_text(encoding='utf-8'))
            self.assertEqual(state['reason'], 'processing_deadline_exceeded')
            self.assertEqual((root / 'presentation.json').read_text(encoding='utf-8'), 'unchanged ranking')
