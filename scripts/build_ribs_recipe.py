from pathlib import Path
import json,base64,html
root=Path(__file__).resolve().parents[1] / 'web/recipes/pepper-ribs'
steps=[
('blanch','冷水焯排骨','排骨冷水下锅，加料酒。煮出浮沫后撇净，捞出沥水。','00:15–00:56','备菜'),
('sear','煎出肉香','锅中放油，排骨煎至表面微黄；不要煎得太焦。加入葱段和 1 个八角。','00:57–01:38','烹饪'),
('simmer','加水炖 40–50 分钟','加温热水，放盐、整根青椒和白胡椒粉，加盖炖约 40–50 分钟。水量按锅具调整，注意别烧干。','01:39–02:22','炖煮'),
('pepper','另锅炒青椒','趁炖排骨时，将剩余青椒去蒂、分段、拍扁，另锅加少许盐翻炒，用铲子压一压，炒软备用。','02:23–02:48','可并行'),
('season','挑椒、调味、收汤','排骨炖熟软后，挑出炖过的整椒和葱段。加入生抽、蚝油、鸡精，煮至汤汁略收浓。','02:49–03:12','烹饪'),
('finish','合锅，留一点汤汁','倒入炒软的青椒，翻拌并短暂煮至味道融合。保留一些汤汁即可出锅，不必把青椒久炖变黄。','03:13–03:48','完成')]
ingredients=[{'name':n,'amount':a,'unit':u} for n,a,u in [('排骨',None,'适量'),('青椒',None,'适量'),('葱',None,'适量'),('八角',1,'个'),('料酒',None,'适量'),('食用油',None,'适量'),('盐',None,'适量'),('白胡椒粉',None,'适量'),('生抽',None,'适量'),('蚝油',None,'适量'),('鸡精',None,'适量'),('水',None,'适量')]]
recipe={'id':'xhs-6ac37366000000001b0222a8','title':'青椒炖排骨','servings':None,'source':'https://www.xiaohongshu.com/explore/6ac37366000000001b0222a8','ingredients':ingredients,'prep':['青椒洗净分两份：一份留整根炖汤，另一份去蒂、分段、拍扁，最后合锅。','准备葱段、1 个八角及调味料；排骨沥干后再下油锅。',steps[0][2]],'cook':[s[2] for s in steps[1:]],'notes':['依据原视频画面与烧录字幕提炼，未进行独立音频转写。','视频未注明人数、排骨重量、青椒总量及多数调味料用量。','作者提到姜，但明确说忘了买；本版按实际操作，不将姜列为必需食材。','炖排骨期间可处理另外两道菜的洗切；多锅同时工作时注意火候。'],'illustrated_steps':[{'title':s[1],'text':s[2],'source_time':s[3],'image':s[0]+'.jpg'} for s in steps]}
recipe['timing']={'prep':[{'min':2,'max':3},{'min':2,'max':4},{'min':6,'max':8}],'cook':[{'min':5,'max':8},{'min':40,'max':50,'wait':True},{'min':5,'max':7},{'min':3,'max':5},{'min':2,'max':5}]}
(root/'recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2))
def img(name):return 'data:image/jpeg;base64,'+base64.b64encode((root/(name+'.jpg')).read_bytes()).decode()
parts=[]
for idx,(name,title,text,time,stage) in enumerate(steps,1):
 parts.append(f'<article class="step"><img src="{img(name)}" alt="{title}，原视频截图"><div><small>STEP {idx:02} · {stage} · 原片 {time}</small><h2>{title}</h2><p>{text}</p></div></article>')
body=''.join(parts)
ing=' · '.join(i['name']+(' 1 个' if i['name']=='八角' else '') for i in ingredients)
json_url='data:application/json;charset=utf-8;base64,'+base64.b64encode(json.dumps(recipe,ensure_ascii=False,indent=2).encode()).decode()
doc=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>青椒炖排骨 · 小厨房图文菜谱</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f5f3eb;color:#293e2e;font-family:Arial,"Noto Sans CJK SC",sans-serif}}main{{max-width:1050px;padding:34px;margin:auto}}.label{{letter-spacing:3px;font-size:12px;color:#6f7d62}}h1{{font-size:44px;margin:14px 0}}.lead{{font-size:18px;line-height:1.8}}.info{{background:#e7eddb;border-radius:14px;padding:18px 22px;line-height:1.85;margin:22px 0}}.info p{{margin:5px 0}}.note{{font-size:13px;color:#687363;line-height:1.7}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}.step{{background:white;border-radius:14px;overflow:hidden;break-inside:avoid}}.step img{{width:100%;height:260px;object-fit:cover;object-position:50% 65%;display:block}}.step:nth-child(4) img{{object-position:50% 18%}}.prep-list{{list-style:none;padding:0;columns:2;column-gap:28px}}.prep-list li{{padding:4px 0;break-inside:avoid;border-bottom:1px solid #d5dec6}}h1 small{{display:block;margin-top:12px;font-size:17px}}.step div{{padding:19px 22px}}small{{font-size:11px;color:#71806a}}h2{{font-size:21px;margin:10px 0}}.step p{{font-size:15px;line-height:1.8;margin:0}}a{{color:#395935}}.actions{{display:flex;gap:12px;margin:20px 0}}.actions a{{padding:10px 15px;background:#38573b;color:white;border-radius:8px;text-decoration:none}}footer{{font-size:12px;line-height:1.8;margin-top:22px;color:#697261}}@media(max-width:650px){{main{{padding:20px}}.prep-list{{columns:1}}h1{{font-size:34px}}.grid{{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;gap:14px}}.step{{flex:0 0 88%;scroll-snap-align:start}}.step img{{height:270px}}}}@media print{{@page{{size:A4;margin:12mm}}body{{background:white}}main{{padding:0}}h1{{font-size:30px}}.actions{{display:none}}.info{{margin:12px 0;font-size:12px}}.lead{{font-size:13px}}.grid{{display:grid;gap:12px;grid-template-columns:1fr 1fr}}.step{{border:1px solid #ddd}}.step img{{height:175px}}.step div{{padding:10px}}h2{{font-size:16px}}.step p{{font-size:12px}}footer{{font-size:10px}}}}
</style></head><body><main><div class="label">小厨房 / 视频提炼菜谱</div><h1>青椒炖排骨 <small>预计 65–90 分钟</small></h1><p class="lead">先煎香，再慢炖。青椒两次下锅，肉香、椒香都有了。</p><p class="note">含备菜与烹饪，按顺序操作保守估算；其中炖煮 40–50 分钟来自视频 · 份量未注明 · 手机可左右滑动步骤卡</p><div class="info"><b>一次备齐</b><ul class="prep-list">{''.join('<li>'+html.escape(i['name'])+'：'+(str(i['amount'])+' ' if i['amount'] else '')+html.escape(i['unit'])+'</li>' for i in ingredients)}</ul><p class="note">除八角外，用量均未明确标注。青椒分成「整椒炖汤」与「分段炒软」两份。</p><b>今晚做三道菜？</b><ol><li>先给排骨焯水、煎香，再加水炖上。</li><li>炖煮期间，洗切另外两道菜的食材并调汁，留意锅中水量。</li><li>临近排骨炖好时炒青椒，再合锅；叶菜最后炒。</li></ol><p class="note">这是备菜安排建议，非原视频指令。多菜实时优先级请在小厨房主页选菜后查看。</p></div><div class="actions"><a href="{json_url}" download="青椒炖排骨.json">下载小厨房导入 JSON</a></div><section class="grid">{body}</section><footer>来源：小红书「暴躁的王小仙」《跟湖南网友学的菜，简直仙品！》 · <a href="{recipe['source']}">查看原笔记</a><br>图片为原视频截图；文字依据画面与烧录字幕整理，未独立转写音频。视频未注明精确克数；作者说姜忘了买，本版不将姜列为必需食材。炖煮火力以保持稳定微沸为操作建议，熟度以实际排骨为准。</footer></main></body></html>'''
(root/'index.html').write_text(doc)
md='# 青椒炖排骨\n\n炖煮约 40–50 分钟；份量与多数食材用量未注明。\n\n**食材：** '+ing+'。\n\n'
for name,title,text,time,stage in steps:md+=f'## {title}\n\n![{title}]({name}.jpg)\n\n{text}\n\n原片：{time}\n\n'
md+='来源：暴躁的王小仙，小红书笔记 6ac37366000000001b0222a8。依据画面与烧录字幕提炼，未独立转写音频。姜在原片未实际使用。\n'
(root/'recipe.md').write_text(md)
print('Created illustrated HTML, Markdown and import JSON')
