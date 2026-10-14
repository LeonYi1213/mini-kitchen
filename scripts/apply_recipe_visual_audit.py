"""Reproduce reviewed images from local originals; never invent an action image.

Run with a Python interpreter containing Pillow. Source videos/notes remain ignored.
Selections are relative source paths and normalized bounds reviewed by a person/agent,
not automatically inferred crops. Run after rebuilding the local recipe batch.
"""
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'design/recipe-visual-audit/selections.json'
MISSING = '原素材未提供可清楚对应这一步的过程图，请按文字操作。'

def apply():
    report = []
    for slug, plan in json.loads(PLAN.read_text()).items():
        folder = ROOT / 'web/recipes' / slug
        recipe = json.loads((folder / 'recipe.json').read_text())
        original = recipe['illustrated_steps']
        source = ROOT / 'imports/local-batch' / slug.removeprefix('local-')
        def render(selection, filename):
            if not isinstance(selection, dict): selection = {'frame': selection}
            frame = selection.get('frame')
            if 'file' in selection:
                path = folder / selection['file']
            elif isinstance(frame, int): path = source / 'frames' / f'{frame:04d}.jpg'
            else: path = source / frame
            bounds = selection.get('bounds', plan['default_bounds'])
            x0,y0,x1,y1 = bounds
            assert 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1
            with Image.open(path) as image:
                image = ImageOps.exif_transpose(image).convert('RGB')
                image = image.crop((round(x0*image.width),round(y0*image.height),round(x1*image.width),round(y1*image.height)))
                image.thumbnail((1200,1200))
                image.save(folder / filename, quality=90)
            return filename, (f'视频约 {(frame-1)*2//60:02}:{(frame-1)*2%60:02}' if isinstance(frame,int) else selection.get('source_time'))
        recipe['cover'], _ = render(plan['cover'], 'review-cover.jpg')
        illustrations = []
        assert len(plan['cook']) == len(recipe['cook'])
        for i, (text, selection) in enumerate(zip(recipe['cook'], plan['cook'])):
            step = {'title': (selection.get('title') if isinstance(selection,dict) else None) or original[len(original)-len(recipe['cook'])+i]['title'], 'text': text}
            if selection is None: step.update(image=None, image_note=MISSING)
            else:
                step['image'], stamp = render(selection, f'review-step-{i+1:02}.jpg')
                if stamp: step['source_time'] = stamp
            illustrations.append(step)
        recipe['illustrated_steps'] = illustrations
        recipe['preparation_steps'] = []
        for i,text in enumerate(recipe['prep']):
            selection = plan['prep'].get(str(i))
            step = {'title': (selection.get('title') if isinstance(selection,dict) else None) or '备菜', 'text':text}
            if selection is None: step.update(image=None, image_note=MISSING)
            elif isinstance(selection,dict) and 'cook_index' in selection:
                ref=illustrations[selection['cook_index']]
                step.update({k:v for k,v in ref.items() if k not in ('text','title')})
                step['title']=ref['title']
            else:
                step['image'], stamp = render(selection, f'review-prep-{i+1:02}.jpg')
                if stamp: step['source_time']=stamp
            recipe['preparation_steps'].append(step)
        recipe['format_version'] = 4
        (folder/'recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n')
        report.append({'slug':slug,'title':recipe['title'],'cover':'reviewed_finished_dish',
                       'cook_reviewed':len(illustrations),
                       'cook_without_source_image':sum(not s.get('image') for s in illustrations),
                       'prep_with_source_image':sum(bool(s.get('image')) for s in recipe['preparation_steps'])})
    (PLAN.parent/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f'Reviewed {len(report)} recipes; {sum(r["cook_without_source_image"] for r in report)} cooking steps explicitly lack reliable source images')
if __name__ == '__main__': apply()
