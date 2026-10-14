"""Create a self-contained native recipe catalog; no video or private metadata."""
import json, shutil
from pathlib import Path
root = Path(__file__).resolve().parents[1]
out = root / 'ios/MiniKitchen/Resources'
out.mkdir(parents=True, exist_ok=True)
reviewed=json.loads((root/'design/recipe-visual-audit/selections.json').read_text())
recipes=[]
for path in sorted((root/'web/recipes').glob('*/recipe.json')):
    recipe=json.loads(path.read_text())
    slug=path.parent.name
    if slug in reviewed:
        assert recipe.get('format_version') == 4, f'{slug}: run apply_recipe_visual_audit.py before bundling'
        for kind,key in [('prep','preparation_steps'),('cook','illustrated_steps')]:
            assert [s['text'] for s in recipe.get(key,[])] == recipe[kind], f'{slug}: illustration mapping drift'
    images=recipe.get('illustrated_steps',[])+recipe.get('preparation_steps',[])
    for step in images:
        if not step.get('image'): continue
        original=path.parent/step['image']
        name=f'{slug}-{original.name}'
        shutil.copyfile(original,out/name)
        step['image']=name
    if recipe.get('cover'):
        original=path.parent/recipe['cover']
        name=f'{slug}-{original.name}'
        shutil.copyfile(original,out/name)
        recipe['cover']=name
    else:
        recipe['cover']=images[-1]['image'] if images else None
    recipes.append(recipe)
(out/'recipes.json').write_text(json.dumps(recipes,ensure_ascii=False,indent=2)+'\n')
print(f'Bundled {len(recipes)} recipes')
