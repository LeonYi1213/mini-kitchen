"""Create a self-contained native recipe catalog; no video or private metadata."""
import json, shutil
from pathlib import Path
root = Path(__file__).resolve().parents[1]
out = root / 'ios/MiniKitchen/Resources'
out.mkdir(parents=True, exist_ok=True)
recipes=[]
for path in sorted((root/'web/recipes').glob('*/recipe.json')):
    recipe=json.loads(path.read_text())
    slug=path.parent.name
    images=recipe.get('illustrated_steps',[])
    for step in images:
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
