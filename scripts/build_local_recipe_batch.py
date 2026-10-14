"""Build reviewed local imports without calling a model or link-import API.

Source notes, videos and the reviewed intermediate JSON stay in ignored imports/.
Generated recipes contain only curated content, source attribution and recipe images.
"""
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'imports/local-batch'
items=json.loads((BATCH/'curated.json').read_text())
report=[]
for item in items:
    source=BATCH/item['slug']
    note=json.loads((source/'note.json').read_text())
    for ingredient in item['ingredients']:
        if ingredient['amount'] is None and '适量' not in ingredient['unit'] and '未注明' not in ingredient['unit']:
            ingredient['unit']='适量（原文：'+ingredient['unit']+'）'
    out=ROOT/'web/recipes'/('local-'+item['slug'])
    out.mkdir(parents=True,exist_ok=True)
    illustrations=[]
    times=[]
    for i,(title,frame,text,lo,hi,wait) in enumerate(item['steps'],1):
        path=source/'frames'/f'{frame:04d}.jpg' if isinstance(frame,int) else source/frame
        image_name=f'step-{i:02}.jpg'
        with Image.open(path) as im:
            im=im.convert('RGB');im.thumbnail((900,1200));im.save(out/image_name,quality=86)
        stamp=f'约 {(frame-1)*2//60:02d}:{(frame-1)*2%60:02d}' if isinstance(frame,int) else f'原笔记图 {int(frame[6:8])+1}'
        illustrations.append(dict(title=title,text=text,source_time=stamp,image=image_name))
        times.append(dict(min=int(lo),max=int(hi),wait=wait))
    recipe=dict(id='xhs-'+note['noteId'],title=item['title'],servings=None,
        source='https://www.xiaohongshu.com/explore/'+note['noteId'],ingredients=item['ingredients'],
        prep=item['prep'],cook=[s['text'] for s in illustrations],
        timing=dict(prep=[dict(min=5,max=10,wait=False) for _ in item['prep']],cook=times),
        illustrated_steps=illustrations,cover=illustrations[-1]['image'],format_version=3,
        notes=['依据本机保存的原笔记正文、图片及视频可见字幕整理，未调用云端导入或模型 API，未独立转写音频。',
            '来源：'+note.get('user',{}).get('nickname','原作者')+'《'+(note.get('title') or item['title'])+'》。',
            '原文未写明的食材用量保留适量；时间范围及未明确标出的备菜时间是整理估算，实际以食材熟度为准。']+([item['notes']] if item['notes'] else []))
    if note['type']=='normal':
        with Image.open(source/'image-00.webp') as im:
            im=im.convert('RGB');im.thumbnail((900,1200));im.save(out/'cover.jpg',quality=86)
        recipe['cover']='cover.jpg'
    (out/'recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n')
    report.append(dict(url='https://xhslink.cn/o/'+item['slug'],title=recipe['title'],id=recipe['id'],path=str(out.relative_to(ROOT)/'recipe.json'),status='saved',recipe_generated=True))
(ROOT/'imports/local-batch/result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
pending=ROOT/'imports/pending-recipes.json'
old=json.loads(pending.read_text());byurl={r['url']:r for r in report}
for entry in old:
    if entry['url'] in byurl:entry.update(byurl[entry['url']]);entry['source_method']='local_browser_and_local_ocr_review'
pending.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
print(f'Saved {len(report)} reviewed recipes with source images')

# Reapply reviewed frame/step mappings so rebuilding cannot restore known wrong images.
from apply_recipe_visual_audit import apply
apply()
