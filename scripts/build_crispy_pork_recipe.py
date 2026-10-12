from pathlib import Path
import json,base64,re,html,subprocess
root=Path(__file__).resolve().parents[1]/'web/recipes/pepper-crispy-pork'
root.mkdir(parents=True,exist_ok=True)
note='69638d85000000000903a44c'
steps=[('cut',32,'去皮擦干，切肉条','选梅花肉或偏瘦五花肉，处理干净后擦干，去皮切条。原片给出的比例为 400 克肉配 150 克红薯淀粉。','00:18–00:44'),('marinate',58,'抓入葱姜水，腌 10 分钟','肉中加半勺盐、1 勺生抽、半勺白胡椒粉及三分之一碗葱姜水，抓至水分被吸收，腌 10 分钟。勺、碗容量未注明。','00:46–01:03'),('pepper',76,'花椒干炒香，碾成细末','趁腌肉时把花椒放入无油锅炒香，盛出碾碎；原片未注明克数和炒制分钟数，避免炒焦。','01:04–01:19'),('coat',94,'挑葱姜，加红薯粉挂糊','挑出葱姜，加入红薯淀粉和花椒碎，少量加水抓拌，调至肉条能挂住糊。原片称加小半碗水，按淀粉吸水性调整，不加鸡蛋。','01:20–01:35'),('fry',114,'逐条下锅，分批初炸','原片用中高火，肉条逐条下油锅，定型后轻轻拨散，分批炸约 5–6 分钟后捞出。肉条粗细、油量不同，以内部熟透为准。','01:36–01:59'),('refry',132,'升温复炸 1 分钟，沥油','第一遍炸好后升高油温，分批复炸约 1 分钟，表面金黄酥脆即捞出，放网架沥油。复炸时间采用画面纠正的 1 分钟；不要将油烧至冒烟。','02:04–02:16')]
for n,t,*_ in steps:
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(root.parents[2]/f'imports/{note}.mp4'),'-vf','scale=480:-1','-frames:v','1',str(root/(n+'.jpg'))],check=True)
items=[('梅花肉或偏瘦五花肉',400,'克'),('红薯淀粉',150,'克'),('盐',0.5,'勺'),('生抽',1,'勺'),('白胡椒粉',0.5,'勺'),('葱姜水',1/3,'碗（容量未注明）')]+[(n,None,'适量') for n in ['花椒','清水（调糊）','食用油']]
r={'id':'xhs-'+note,'title':'花椒小酥肉','servings':None,'source':'https://www.xiaohongshu.com/explore/'+note,'ingredients':[{'name':n,'amount':a,'unit':u} for n,a,u in items],'prep':['肉处理干净擦干，去皮切条；葱姜用水抓出味后取汁备用。','加盐、生抽、白胡椒粉及葱姜水抓匀，腌 10 分钟；期间可炒花椒。'],'cook':[s[3] for s in steps[2:]],'timing':{'prep':[{'min':6,'max':10},{'min':12,'max':13,'wait':True}],'cook':[{'min':3,'max':5},{'min':3,'max':5},{'min':8,'max':15},{'min':2,'max':4}]},'notes':['来源：野生土豆。依据全片抽帧及烧录字幕整理，未独立转写音频。','字幕明确 400 克肉配 150 克地瓜粉（红薯淀粉），菜谱按此比例整理；演示实际总肉量、份数未注明。','盐半勺、生抽 1 勺、白胡椒粉半勺、葱姜水三分之一碗为原片腌料；勺碗大小不明，不换算克数或毫升。','葱姜水由适量葱、姜和水抓揉取得，三分之一碗是取用量，原片未给配制比例。调糊清水原片小半碗，需按挂糊状态调整。','腌制 10 分钟、初炸约 5–6 分钟、复炸 1 分钟为原片信息，复炸采用画面更正值。','预计累计 34–52 分钟为补充估算，含分批下锅及捞取；炒花椒可与腌制重叠。批次数影响总耗时。','原片没有加鸡蛋；不把其他酥肉配方中的鸡蛋加入此菜谱。','充分熟透、避免油冒烟与复炸分批为补充建议；原片未提供数值油温。'],'illustrated_steps':[{'title':s[2],'text':s[3],'source_time':s[4],'image':s[0]+'.jpg'} for s in steps]}
(root/'recipe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
css=re.search(r'<style>(.*?)</style>',(root.parent/'pepper-ribs/index.html').read_text(),re.S)[1]+'.step img,.step:nth-child(4) img{object-position:50% 55%}'
def img(n):return 'data:image/jpeg;base64,'+base64.b64encode((root/(n+'.jpg')).read_bytes()).decode()
rows=''.join('<li>'+html.escape(n)+'：'+(('1/3' if n=='葱姜水' else str(a))+' '+html.escape(u) if a is not None else '适量')+'</li>' for n,a,u in items)
prep=''.join('<li>'+html.escape(x)+'</li>' for x in r['prep'])
cards=''.join(f'<article class="step"><img src="{img(n)}" alt="{title}，原视频截图"><div><small>STEP {i:02} · 原片 {time}</small><h2>{title}</h2><p>{text}</p></div></article>' for i,(n,t,title,text,time) in enumerate(steps,1))
download='data:application/json;base64,'+base64.b64encode(json.dumps(r,ensure_ascii=False).encode()).decode()
s=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>花椒小酥肉 · 小厨房</title><style>{css}</style></head><body><main><div class="label">小厨房 / 视频提炼菜谱</div><h1>花椒小酥肉<small>预计 34–52 分钟 · 含备菜和腌制，按步骤累计，补充估算</small></h1><p class="lead">现炒花椒提香，红薯淀粉挂糊，初炸熟透再复炸酥脆。</p><p class="note">按 400 克肉、150 克红薯淀粉比例整理。腌制时可同步炒花椒，批次数影响总耗时。手机可左右滑动步骤卡。</p><div class="info"><b>一次备齐 · 一项一行</b><ul class="prep-list">{rows}</ul><p class="note">葱姜水：取适量葱、姜加水抓揉，再取三分之一碗。调糊清水原片为小半碗，按挂糊状态调整。勺、碗容量未注明。</p><b>备菜顺序</b><ol>{prep}</ol><b>搭配其他菜的顺序建议</b><p>先腌肉，等待时炒花椒、准备其他菜的配料。炸制需持续看守，避免同时安排另一道需要不停翻炒的菜。接近开饭完成复炸、沥油上桌。</p></div><div class="actions"><a href="{download}" download="花椒小酥肉.json">下载小厨房导入 JSON</a></div><section class="grid">{cards}</section><footer>来源：小红书「野生土豆」 · <a href="{r['source']}">原笔记</a><br>图片为原视频截图，文字依据画面及烧录字幕整理，未独立转写音频。总耗时为估算；初炸约 5–6 分钟，复炸按画面纠正为 1 分钟。熟透、分批复炸和避免油冒烟为补充建议。</footer></main></body></html>'''
(root/'index.html').write_text(s)
print('Built crispy pork recipe')
