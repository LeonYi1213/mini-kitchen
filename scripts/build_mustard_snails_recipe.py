from pathlib import Path
import json,base64,re,html,subprocess
root=Path(__file__).resolve().parents[1]/'web/recipes/mustard-sea-snails'
root.mkdir(parents=True,exist_ok=True)
note='69733675000000001a023c90'
steps=[('sauce',12,'提前调好料汁','生抽 1 勺、清水 2 勺、蚝油 1 勺、白糖半勺、生粉半勺搅匀。原片未说明勺容量和花螺重量，按实际食材量调整。','00:12–00:13'),('snails',3,'花螺直接下锅，烹白酒','花螺清理干净、沥水后下油锅，原片不焯水。烹入适量白酒，翻炒挥发水汽；家庭操作建议先离火加酒再加热。','00:00–00:05'),('mustard',8,'下姜蒜辣椒与芥末','加入姜末、蒜末、干辣椒，挤入大半管芥末，大火炒香。管装规格未注明，芥末强度按个人接受程度调整。','00:06–00:10'),('beer',13,'加啤酒和料汁','倒入小半碗啤酒，再倒入预先调匀的料汁。碗容量未注明，注意锅中保留足够焖制的水分。','00:11–00:13'),('simmer',15,'加盖小火焖约 4 分钟','加盖小火焖约 4 分钟，这是原片时间；花螺大小与锅具不同，仍需确保螺肉充分熟透，未熟继续加热。','00:14–00:15'),('finish',19,'补蒜末和芥末，拌匀出锅','加入预留的生蒜末，再挤适量芥末，翻拌均匀后出锅。两次加芥末，分别炒香与补足辛香。','00:16–00:25')]
for n,t,*_ in steps:
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(root.parents[2]/f'imports/{note}.mp4'),'-vf','scale=480:-1','-frames:v','1',str(root/(n+'.jpg'))],check=True)
items=[('花螺',None,'适量'),('姜',None,'适量'),('蒜（分两次放）',None,'适量'),('干辣椒',None,'适量'),('食用油',None,'适量'),('白酒',None,'适量'),('芥末（首次）',None,'适量'),('芥末（出锅前）',None,'适量'),('啤酒',None,'适量'),('生抽',1,'勺'),('清水（料汁）',2,'勺'),('蚝油',1,'勺'),('白糖',0.5,'勺'),('生粉',0.5,'勺')]
r={'id':'xhs-'+note,'title':'芥辣花螺','servings':None,'source':'https://www.xiaohongshu.com/explore/'+note,'ingredients':[{'name':n,'amount':a,'unit':u} for n,a,u in items],'prep':['花螺清理干净、沥水；姜蒜切末，蒜末分成炒香与出锅前加入两份，准备干辣椒。',steps[0][3]],'cook':[s[3] for s in steps[1:]],'timing':{'prep':[{'min':5,'max':8},{'min':1,'max':2}],'cook':[{'min':2,'max':3},{'min':1,'max':2},{'min':1,'max':1},{'min':4,'max':4,'wait':True},{'min':1,'max':2}]},'notes':['来源：白菜青盐糙米饭。依据完整视频逐秒抽帧与烧录字幕整理，未独立转写音频。','花螺重量、人数和勺容量未注明，不将勺换算成毫升或克。','原片首次芥末用大半管、啤酒小半碗，均未注明容器规格，导入食材表记适量，步骤保留原话。','原片小火加盖焖 4 分钟；预计总耗时 15–22 分钟为补充估算，不含额外吐沙等待。螺肉需充分熟透，不能仅凭 4 分钟保证成熟。','清理沥水、家庭离火加白酒再加热、检查熟度为补充操作建议。','成品可见少量绿色碎末但未明确名称，不据此擅加葱花等食材。'],'illustrated_steps':[{'title':s[2],'text':s[3],'source_time':s[4],'image':s[0]+'.jpg'} for s in steps]}
(root/'recipe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
css=re.search(r'<style>(.*?)</style>',(root.parent/'pepper-ribs/index.html').read_text(),re.S)[1]+'.step img,.step:nth-child(4) img{object-position:50% 55%}'
def img(n):return 'data:image/jpeg;base64,'+base64.b64encode((root/(n+'.jpg')).read_bytes()).decode()
rows=''.join('<li>'+html.escape(n)+'：'+(str(a)+' '+html.escape(u) if a is not None else '适量')+'</li>' for n,a,u in items)
prep=''.join('<li>'+html.escape(x)+'</li>' for x in r['prep'])
cards=''.join(f'<article class="step"><img src="{img(n)}" alt="{title}，原视频截图"><div><small>STEP {i:02} · 原片 {time}</small><h2>{title}</h2><p>{text}</p></div></article>' for i,(n,t,title,text,time) in enumerate(steps,1))
download='data:application/json;base64,'+base64.b64encode(json.dumps(r,ensure_ascii=False).encode()).decode()
s=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>芥辣花螺 · 小厨房</title><style>{css}</style></head><body><main><div class="label">小厨房 / 视频提炼菜谱</div><h1>芥辣花螺<small>预计 15–22 分钟 · 含备菜，补充估算</small></h1><p class="lead">姜蒜辣椒炒香，啤酒焖入味，芥末分两次加入。</p><p class="note">份量未注明；不含额外吐沙等待。焖制以充分熟透为准。手机可左右滑动步骤卡。</p><div class="info"><b>一次备齐 · 一项一行</b><ul class="prep-list">{rows}</ul><p class="note">原片芥末首次用大半管、啤酒小半碗，容器规格未注明；此处显示适量，步骤保留说明。料汁各项用同一把勺。</p><b>备菜顺序</b><ol>{prep}</ol><b>搭配其他菜的顺序建议</b><p>先把炖菜做上，提前清理花螺、切姜蒜并调好料汁。这道菜临近开饭再炒；加盖焖制时可整理餐具，仍需留意锅中水分，最后补蒜末和芥末立即上桌。</p></div><div class="actions"><a href="{download}" download="芥辣花螺.json">下载小厨房导入 JSON</a></div><section class="grid">{cards}</section><footer>来源：小红书「白菜青盐糙米饭」 · <a href="{r['source']}">原笔记</a><br>图片为原视频截图，文字依据画面及烧录字幕整理，未独立转写音频。总耗时为估算；小火焖 4 分钟为原片时间。清理沥水、离火加酒和充分熟透的提醒为补充建议。</footer></main></body></html>'''
(root/'index.html').write_text(s)
print('Built mustard snails recipe')
