import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('kitchen_backend', ROOT/'backend/server.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.storage = patch.object(server, 'STORAGE', Path(self.temp.name))
        self.storage.start()
        server.initialize()

    def tearDown(self):
        self.storage.stop()
        self.temp.cleanup()

    def test_all_bundled_recipes_validate(self):
        paths = list((ROOT/'web/recipes').glob('*/recipe.json'))
        self.assertEqual(len(paths), 18)
        for path in paths:
            self.assertTrue(server.valid_recipe(json.loads(path.read_text())), path.parent.name)

    def test_bad_model_response_never_becomes_recipe(self):
        recipe = json.loads((ROOT/'web/recipes/pepper-ribs/recipe.json').read_text())
        for key, value in [('cook', []), ('ingredients', []), ('timing', []), ('title', ''), ('timing', {'prep': [], 'cook': []})]:
            bad = copy.deepcopy(recipe)
            bad[key] = value
            self.assertFalse(server.valid_recipe(bad))
        self.assertFalse(server.valid_recipe({'error': 'unreadable'}))
        recipe['ingredients'][0]['amount'] = -1
        self.assertFalse(server.valid_recipe(recipe))

    def test_cancel_prevents_late_completion(self):
        server.write({'id': 'a', 'status': 'cancelled', 'completedStages': 1})
        with self.assertRaises(InterruptedError):
            server.stage('a', 4, status='completed', recipe={})
        self.assertEqual(server.read('a')['status'], 'cancelled')

    def test_restart_marks_inflight_failed_and_preserves_completed(self):
        server.write({'id': 'a', 'status': 'running', 'completedStages': 2})
        server.write({'id': 'b', 'status': 'completed', 'completedStages': 4})
        server.initialize()
        self.assertEqual(server.read('a')['status'], 'failed')
        self.assertEqual(server.read('b')['status'], 'completed')

    def test_read_failure_never_calls_model(self):
        server.write({'id': 'a', 'status': 'queued', 'completedStages': 0})
        with patch.object(server.subprocess, 'run', side_effect=RuntimeError('blocked')), patch.object(server.urllib.request, 'urlopen') as model:
            server.run('a', 'https://xhslink.cn/o/test')
        self.assertEqual(server.read('a')['status'], 'failed')
        self.assertNotIn('recipe', server.read('a'))
        model.assert_not_called()
