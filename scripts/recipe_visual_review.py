"""Render the complete audited catalog for side-by-side human review, no network."""
from pathlib import Path
import html,json
ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'design/recipe-visual-audit/review.html'
def h(s):return html.escape(str(s))
parts=['''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>小厨房 · 全菜谱图片核对</title><style>body{margin:24px;background:#f5f5f2;color:#22382c;font:16px/1.7 system-ui}article{margin:30px 0;border-top:1px solid #ccd4c8}section{display:flex;gap:16px;overflow:auto;padding:12px 0}figure{flex:0 0 270px;margin:0;background:white;padding:12px;border-radius:12px}img{width:100%;height:245px;object-fit:contain;background:#edf0e8}small{color:#6b7767}.missing{height:245px;display:grid;place-items:center;background:#edf0e8}h2{margin-bottom:0}</style><h1>42 道菜 · 封面、备菜与烹饪图逐项核对</h1><p>图片来自原笔记。没有可靠过程图时明确留空，不使用成品图替代。</p>''']
for p in sorted((ROOT/'web/recipes').glob('*/recipe.json')):
 r=json.loads(p.read_text());parts.append('<article><h2>'+h(r['title'])+'</h2><section>')
 items=[{'title':'成品封面','text':'','image':r['cover']}]+[dict(s,title='备菜 · '+s['title']) for s in r.get('preparation_steps',[])]+r['illustrated_steps']
 for s in items:
  picture=f'<img loading="lazy" src="../../web/recipes/{h(p.parent.name)}/{h(s["image"])}">' if s.get('image') else '<div class="missing">'+h(s.get('image_note','缺少过程图'))+'</div>'
  parts.append('<figure>'+picture+'<b>'+h(s['title'])+'</b><figcaption>'+h(s['text'])+'</figcaption><small>'+h(s.get('source_time',''))+'</small></figure>')
 parts.append('</section></article>')
parts.append('</html>');TARGET.write_text(''.join(parts))
print(TARGET)
