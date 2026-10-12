from pathlib import Path
import json,base64,re,html,subprocess
root=Path(__file__).resolve().parents[1]/'web/recipes/braised-pork-rice'
root.mkdir(parents=True,exist_ok=True)
note='69c90f84000000002800abcd'
steps=[('cut',42,'五花肉切小条，肥瘦分开','猪皮刮净，五花肉切成约小拇指粗细的小条，肥肉、瘦肉分开放；紫洋葱切小粒，姜蒜葱白切碎。','00:18–01:09'),('render',90,'肥肉先煸，再下瘦肉','热锅少量油润锅，先下肥肉中火煸出油脂；油太多可倒出一部分，再下瘦肉翻炒，淋花雕酒。','01:21–01:37'),('season',115,'炒香洋葱与香料，调色','放入干辣椒、桂皮、八角、姜蒜葱白，再下紫洋葱炒至半熟。加两颗黄冰糖、生抽、老抽，炒出酱香。','01:38–01:58'),('pressure',126,'加开水和鸡蛋，炖软','加开水，转入高压锅，放入煮熟去壳的鸡蛋。原片上汽后压 7 分钟；按自家锅说明完成泄压再开盖，检查肉是否软烂。普通锅原片建议至少炖 1 小时，需留意水量。','01:59–02:07'),('reduce',210,'挑出香料，收浓卤汁','泄压开盖后倒回炒锅，挑出桂皮、八角、干辣椒等香料，收至汤汁浓稠但仍有汁可拌饭。','03:21–03:32'),('serve',223,'米饭铺底，浇肉配菜','米饭装盘，浇上卤肉和卤汁，搭配鸡蛋与熟青菜。青菜焯熟为补充操作，原片仅展示成品配菜。','03:36–03:49')]
for n,t,*_ in steps:
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(root.parents[2]/f'imports/{note}.mp4'),'-vf','scale=480:-1','-frames:v','1',str(root/(n+'.jpg'))],check=True)
items=[('黄冰糖',2,'颗（大小未注明）')]+[(n,None,'适量') for n in ['带皮五花肉','紫洋葱','干辣椒','桂皮','八角','姜','蒜','葱白','花雕酒','生抽','老抽','食用油','水','鸡蛋','青菜','米饭']]
r={'id':'xhs-'+note,'title':'洋葱卤肉饭','servings':None,'source':'https://www.xiaohongshu.com/explore/'+note,'ingredients':[{'name':n,'amount':a,'unit':u} for n,a,u in items],'prep':['五花肉刮净猪皮，切小条，肥瘦分开。','紫洋葱切粒，姜蒜葱白切碎，备好干辣椒、桂皮、八角。','鸡蛋煮熟、过冷水后剥壳；青菜洗净，米饭提前煮好。'],'cook':[s[3] for s in steps[1:]],'timing':{'prep':[{'min':8,'max':12},{'min':4,'max':6},{'min':10,'max':15}],'cook':[{'min':8,'max':12},{'min':5,'max':8},{'min':22,'max':32,'wait':True},{'min':5,'max':10},{'min':3,'max':5}]},'notes':['来源：我的李老板。依据全片抽帧及关键片段加密画面、烧录字幕整理，未独立转写音频。','黄冰糖原片两颗，大小未注明；其他食材用量与人数未注明，显示适量。','高压锅上汽后 7 分钟为原片时间，不包含升压、泄压；按锅具说明操作并以肉软烂为准。普通锅原片建议至少炖 1 小时。','预计 65–100 分钟为高压锅版本步骤累计估算，含煮蛋和升压泄压；米饭需提前或另锅同步煮，未另累计电饭煲耗时。','青菜焯熟及安全泄压、检查肉软烂为补充操作建议。','片中另做的黄瓜拌皮蛋、汤不属于本菜谱，不混入其食材与调味。','未见卤肉步骤加盐或蚝油，不因另一个凉菜使用蚝油而添加到卤肉配方。'],'illustrated_steps':[{'title':s[2],'text':s[3],'source_time':s[4],'image':s[0]+'.jpg'} for s in steps]}
(root/'recipe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
css=re.search(r'<style>(.*?)</style>',(root.parent/'pepper-ribs/index.html').read_text(),re.S)[1]+'.step img,.step:nth-child(4) img{object-position:50% 55%}'
def img(n):return 'data:image/jpeg;base64,'+base64.b64encode((root/(n+'.jpg')).read_bytes()).decode()
rows=''.join('<li>'+html.escape(n)+'：'+(str(a)+' '+html.escape(u) if a is not None else '适量')+'</li>' for n,a,u in items)
prep=''.join('<li>'+html.escape(x)+'</li>' for x in r['prep'])
cards=''.join(f'<article class="step"><img src="{img(n)}" alt="{title}，原视频截图"><div><small>STEP {i:02} · 原片 {time}</small><h2>{title}</h2><p>{text}</p></div></article>' for i,(n,t,title,text,time) in enumerate(steps,1))
download='data:application/json;base64,'+base64.b64encode(json.dumps(r,ensure_ascii=False).encode()).decode()
s=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>洋葱卤肉饭 · 小厨房</title><style>{css}</style></head><body><main><div class="label">小厨房 / 视频提炼菜谱</div><h1>洋葱卤肉饭<small>预计 65–100 分钟 · 高压锅版本，含备菜与升压泄压，补充估算</small></h1><p class="lead">紫洋葱与黄冰糖炒出香甜，肥肉先煸，卤汁收浓再浇饭。</p><p class="note">人数未注明。米饭提前或另锅同步煮，煮饭时间未另累计。手机可左右滑动步骤卡。</p><div class="info"><b>一次备齐 · 一项一行</b><ul class="prep-list">{rows}</ul><p class="note">黄冰糖两颗为原片用量，颗粒大小未注明；其他用量显示适量。此版使用紫洋葱直接炒制。</p><b>备菜顺序</b><ol>{prep}</ol><b>搭配其他菜的顺序建议</b><p>先启动煮饭，再将卤肉炒好入高压锅。炖煮等待时切配其他菜或拌凉菜；卤肉收汁时准备青菜，快手热菜临近开饭再炒。高压锅必须按说明泄压后开盖。</p></div><div class="actions"><a href="{download}" download="洋葱卤肉饭.json">下载小厨房导入 JSON</a></div><section class="grid">{cards}</section><footer>来源：小红书「我的李老板」 · <a href="{r['source']}">原笔记</a><br>图片为原视频截图，文字依据画面及烧录字幕整理，未独立转写音频。总耗时为高压锅版估算。原片上汽后压 7 分钟；普通锅至少炖 1 小时。泄压和熟度检查、焯青菜为补充建议。</footer></main></body></html>'''
(root/'index.html').write_text(s)
print('Built braised pork rice recipe')
