"""Prevent reviewed native recipes from silently reverting to old frame mappings."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]

class VisualCatalogTests(unittest.TestCase):
    def test_every_recipe_has_reviewed_cover_and_exact_stage_mapping(self):
        plans=json.loads((ROOT/'design/recipe-visual-audit/selections.json').read_text())
        paths=list((ROOT/'web/recipes').glob('*/recipe.json'))
        self.assertEqual(set(plans),{p.parent.name for p in paths})
        for path in paths:
            recipe=json.loads(path.read_text())
            self.assertEqual(recipe['format_version'],4,path.parent.name)
            self.assertEqual(recipe['cover'],'review-cover.jpg')
            self.assertTrue((path.parent/recipe['cover']).is_file())
            for kind,key in [('prep','preparation_steps'),('cook','illustrated_steps')]:
                self.assertEqual([s['text'] for s in recipe[key]],recipe[kind],path.parent.name)
                for s in recipe[key]:
                    if s.get('image'):
                        self.assertTrue((path.parent/s['image']).is_file())
                        self.assertNotEqual(s['image'],recipe['cover'])
                    else:self.assertTrue(s.get('image_note'))

    def test_known_wrong_source_images_are_not_reintroduced(self):
        def read(slug):return json.loads((ROOT/'web/recipes'/slug/'recipe.json').read_text())
        claws=read('local-91ugu1m6F9Z')
        self.assertTrue(all(s['image'] is None for s in claws['illustrated_steps']))
        self.assertIsNone(read('curry-beef-ribs')['illustrated_steps'][0]['image'])
        self.assertIsNone(read('steamed-bass')['illustrated_steps'][0]['image'])
        asparagus=read('local-1vvAFCVErIZ')
        self.assertEqual(len({s['image'] for s in asparagus['illustrated_steps']}),3)
