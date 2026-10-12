import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import shutil

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from recipe_format import asset_path, current_recipe, materialize, validate_visual_plan


class IllustratedContractTests(unittest.TestCase):
    def setUp(self):
        self.crop = patch('recipe_format.crop_frame', side_effect=lambda source, target, focus: shutil.copyfile(source, target))
        self.crop.start()
        self.addCleanup(self.crop.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.frames = [self.root / f'source-{i}.jpg' for i in range(3)]
        for i, frame in enumerate(self.frames): frame.write_bytes(b'jpeg-source-' + str(i).encode())
        self.recipe = {'title': '测试菜', 'ingredients': [{'name': '米', 'amount': None, 'unit': '适量（浸泡用）'}],
                       'prep': ['浸泡米。'], 'cook': ['炖牛肉。', '焖米饭。'],
                       'timing': {'prep': [{'min': 30, 'max': 30}], 'cook': [{'min': 30, 'max': 60}, {'min': 10, 'max': 15}]},
                       'notes': ['除原片明确等待时间外，其余为估算。'], 'cover_frame': 3, 'cover_focus': [0.5, 0.8],
                       'illustrated_steps': [{'title': '炖肉', 'frame_index': 1, 'focus': [0.5, 0.8]}, {'title': '焖饭', 'frame_index': 2, 'focus': [0.5, 0.8]}]}

    def tearDown(self): self.temp.cleanup()

    def test_images_and_exact_step_mapping_survive_source_cleanup(self):
        result = materialize(self.recipe, self.frames, 2.5, 'a' * 24, 'b' * 32, self.root)
        for frame in self.frames: frame.unlink()
        self.assertTrue(current_recipe(result, self.root))
        self.assertEqual([s['text'] for s in result['illustrated_steps']], result['cook'])
        self.assertEqual(result['ingredients'][0]['unit'], '适量（浸泡用）')
        self.assertEqual(asset_path(self.root, result['cover']).read_bytes(), b'jpeg-source-2')
        self.assertEqual(json.loads(json.dumps(result, ensure_ascii=False)), result)

    def test_legacy_cache_and_missing_assets_require_regeneration(self):
        self.assertFalse(current_recipe(self.recipe, self.root))
        result = materialize(self.recipe, self.frames, 2.5, 'a' * 24, 'b' * 32, self.root)
        asset_path(self.root, result['cover']).unlink()
        self.assertFalse(current_recipe(result, self.root))

    def test_rejects_out_of_bounds_missing_or_unrelated_illustrations(self):
        for change in [lambda r: r.update(cover_frame=4), lambda r: r.update(illustrated_steps=[]),
                       lambda r: r['illustrated_steps'][0].update(frame_index=0),
                       lambda r: r['illustrated_steps'][0].update(frame_index=2),
                       lambda r: r.update(notes=[]), lambda r: r.update(cover_focus=[0.5, 2])]:
            bad = copy.deepcopy(self.recipe); change(bad)
            with self.assertRaises(ValueError): validate_visual_plan(bad, 3)

    def test_asset_paths_cannot_escape_storage(self):
        for name in ['../jobs.sqlite', 'assets/../../jobs.sqlite', 'https://evil.example/a.jpg',
                     'assets/xhs-' + 'a' * 24 + '/' + 'b' * 32 + '/../../jobs.sqlite']:
            self.assertIsNone(asset_path(self.root, name))
        real = self.root / 'assets'; real.symlink_to(self.root.parent, target_is_directory=True)
        self.assertIsNone(asset_path(self.root, 'assets/xhs-' + 'a' * 24 + '/' + 'b' * 32 + '/frame-001.jpg'))
