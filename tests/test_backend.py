import copy
import io
import shutil
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
        self.assertEqual(len(paths), 42)
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

    def test_network_restriction_is_explained_without_leaking_reader_output(self):
        server.write({'id': 'a', 'status': 'queued', 'completedStages': 0})
        error = server.subprocess.CalledProcessError(1, ['reader'], stderr=b'XHS_NETWORK_RESTRICTED secret-token')
        with patch.object(server.subprocess, 'run', side_effect=error), patch.object(server.urllib.request, 'urlopen') as model:
            server.run('a', 'https://xhslink.cn/o/test')
        self.assertIn('300012', server.read('a')['message'])
        self.assertNotIn('secret', server.read('a')['message'])
        model.assert_not_called()

    def test_cancelled_upload_deletes_file_without_model_call(self):
        video = server.STORAGE/'uploads/test.video'; video.write_bytes(b'video')
        server.write({'id':'cancelled-upload','status':'cancelled','completedStages':0})
        with patch.object(server.urllib.request, 'urlopen') as model:
            server.run('cancelled-upload', uploaded=video, digest='a'*64)
        self.assertFalse(video.exists())
        model.assert_not_called()

    def test_invalid_uploaded_media_never_calls_model(self):
        video = server.STORAGE/'uploads/test.video'; video.write_bytes(b'not-video')
        server.write({'id':'bad-upload','status':'queued','completedStages':0})
        with patch.object(server.subprocess, 'check_output', side_effect=ValueError('invalid')), patch.object(server.urllib.request, 'urlopen') as model:
            server.run('bad-upload', uploaded=video, digest='a'*64)
        self.assertEqual(server.read('bad-upload')['status'], 'failed')
        self.assertFalse(video.exists())
        self.assertEqual(list(server.STORAGE.glob('recipe-*')), [])
        model.assert_not_called()

    def test_real_worker_replaces_legacy_cache_and_persists_illustrations(self):
        note_id = 'a' * 24
        legacy = {'id': 'xhs-' + note_id, 'title': '旧版', 'cook': ['旧步骤']}
        server.write({'id': 'old', 'status': 'completed', 'recipe': legacy})
        server.write({'id': 'new', 'status': 'queued', 'completedStages': 0})
        plan = {'title': '图文菜', 'ingredients': [{'name': '米', 'amount': None, 'unit': '适量'}],
                'prep': ['泡米。'], 'cook': ['炖肉。', '焖饭。'],
                'timing': {'prep': [{'min': 30, 'max': 30}], 'cook': [{'min': 30, 'max': 60}, {'min': 10, 'max': 15}]},
                'notes': ['操作耗时为估算。'], 'cover_frame': 3, 'cover_focus': [0.5, 0.8],
                'illustrated_steps': [{'title': '炖肉', 'frame_index': 1, 'focus': [0.5, 0.8]}, {'title': '焖饭', 'frame_index': 2, 'focus': [0.5, 0.8]}]}
        bad = copy.deepcopy(plan); bad['cover_frame'] = 999
        def response(value):
            return io.BytesIO(json.dumps({'choices': [{'message': {'content': json.dumps(value)}}]}).encode())
        def command(args, **kwargs):
            if 'import_video.py' in args[1]:
                folder = Path(args[-1])
                (folder / (note_id + '.info.json')).write_text(json.dumps({'id': note_id, 'note': {}}))
                (folder / (note_id + '.mp4')).write_bytes(b'video')
            elif args[0] == 'ffmpeg':
                folder = Path(args[-1]).parent
                for i in range(1, 4): (folder / f'frame-{i:03}.jpg').write_bytes(b'frame')
        with patch('recipe_format.crop_frame', side_effect=lambda source, target, focus: shutil.copyfile(source, target)), \
             patch.object(server.subprocess, 'run', side_effect=command), \
             patch.object(server.subprocess, 'check_output', return_value=b'6'), \
             patch.object(server, 'model_config', return_value=('test', 'https://example.invalid/v1', 'test')), \
             patch.object(server.urllib.request, 'urlopen', side_effect=[response(bad), response(plan)]) as model:
            server.run('new', 'https://xhslink.cn/o/test')
        job = server.read('new')
        self.assertEqual(job['status'], 'completed')
        self.assertFalse(job['cacheHit'])
        self.assertEqual(model.call_count, 2)  # Invalid frame reference is corrected, not silently accepted.
        self.assertTrue(server.current_recipe(job['recipe'], server.STORAGE))
        self.assertEqual([s['text'] for s in job['recipe']['illustrated_steps']], plan['cook'])
        self.assertEqual(list(server.STORAGE.glob('recipe-*')), [])
