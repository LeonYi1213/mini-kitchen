from pathlib import Path
import json,base64,re,html,subprocess
root=Path(__file__).resolve().parents[1]/'web/recipes/shrimp-seaweed-wonton'
root.mkdir(parents=True,exist_ok=True)
note='69eb34a5000000001f00515f'
steps=[('oil',18,'虾头熬出红亮虾油','虾头下热油，翻炒时用铲压一压，炒至油色红亮，取出虾油备用。','00:08–00:26'),('seaweed',35,'紫菜干焙，捏碎备用','紫菜放入无油锅中干焙，翻面至酥脆，取出捏碎。原片用了两片，大小未注明。','00:27–00:37'),('water',49,'肉馅分次打入香料水','肉馅绞细，葱姜花椒水过滤后少量多次加入；每次抓拌至水分被吸收，再加下一次，拌至黏稠。','00:38–01:07'),('filling',86,'拌基础馅，分成两种口味','加入虾仁、紫菜碎、盐、胡椒粉、生抽、蚝油、味精和虾油拌匀。基础馅分两份：一份加韭菜碎，另一份加玉米粒。只做一种也可以。','01:08–01:44'),('wrap',110,'包馄饨，多余的冷冻','取馄饨皮放馅，折合捏紧，按自己习惯包好。暂时不吃的分开放在托盘上冷冻，冻硬后密封保存（保存方式为补充建议）。','01:45–02:01'),('soup',143,'煮熟，冲汤底盛出','水开下馄饨，煮至皮熟、肉虾馅充分熟透。碗中放生抽、盐、虾皮、香菜、葱花、紫菜、胡椒粉、芝麻油，冲入热汤，再盛入馄饨。原片未注明煮制分钟数。','02:02–02:33')]
for n,t,*_ in steps:
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(root.parents[2]/f'imports/{note}.mp4'),'-vf','scale=480:-1','-frames:v','1',str(root/(n+'.jpg'))],check=True)
items=[('肉馅',None,'适量'),('虾仁与虾头',None,'适量'),('馄饨皮',None,'适量'),('紫菜（拌馅）',2,'片（大小未注明）'),('胡椒粉（拌馅）',1,'小勺（字幕称约 2 克）')]+[(n,None,'适量') for n in ['葱','姜','花椒','水','食用油','盐','生抽','蚝油','味精（可换鸡精或松鲜鲜）','韭菜（韭菜口味）','玉米粒（玉米口味）','虾皮（汤底）','香菜（汤底）','紫菜（汤底）','胡椒粉（汤底）','芝麻油（汤底）']]
r={'id':'xhs-'+note,'title':'虾仁紫菜鲜肉馄饨','servings':None,'source':'https://www.xiaohongshu.com/explore/'+note,'ingredients':[{'name':n,'amount':a,'unit':u} for n,a,u in items],'prep':['虾去壳去虾线，保留虾头熬油，虾仁切小块；肉馅绞细。','准备葱姜花椒水并过滤；原片未注明浸泡用时与比例。','韭菜洗净沥水切碎，玉米备粒；葱、香菜切碎用于汤底。'],'cook':[s[3] for s in steps],'timing':{'prep':[{'min':8,'max':12},{'min':3,'max':5},{'min':4,'max':6}],'cook':[{'min':4,'max':6},{'min':2,'max':3},{'min':5,'max':8},{'min':3,'max':5},{'min':20,'max':35},{'min':8,'max':12}]},'notes':['来源：糯妈。依据全片抽帧及关键段加密画面、烧录字幕整理，未独立转写音频。','未标注用量显示适量；原片两片紫菜大小未注明，胡椒粉一小勺字幕接约两克。该克数不属于生抽用量。','一批馄饨总份量未注明，视频只取部分煮两人份，不能据此把整批标成两人份。','预计 57–92 分钟为含手工包制的补充估算；包制数量影响很大，未含冷冻保存与额外香料水浸泡等待。','原片给出韭菜、玉米两种口味；提及的小白菜是可替换举例，不是本次演示必需食材。','肉馅肉类未由字幕明确，画面看似猪肉，故主食材保留肉馅名称。','肉虾馅充分熟透、冷冻后密封保存为补充建议；不以浮起作为唯一熟度判断。'],'illustrated_steps':[{'title':s[2],'text':s[3],'source_time':s[4],'image':s[0]+'.jpg'} for s in steps]}
(root/'recipe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
css=re.search(r'<style>(.*?)</style>',(root.parent/'pepper-ribs/index.html').read_text(),re.S)[1]+'.step img,.step:nth-child(4) img{object-position:50% 55%}'
def img(n):return 'data:image/jpeg;base64,'+base64.b64encode((root/(n+'.jpg')).read_bytes()).decode()
rows=''.join('<li>'+html.escape(n)+'：'+(str(a)+' '+html.escape(u) if a is not None else '适量')+'</li>' for n,a,u in items)
prep=''.join('<li>'+html.escape(x)+'</li>' for x in r['prep'])
cards=''.join(f'<article class="step"><img src="{img(n)}" alt="{title}，原视频截图"><div><small>STEP {i:02} · 原片 {time}</small><h2>{title}</h2><p>{text}</p></div></article>' for i,(n,t,title,text,time) in enumerate(steps,1))
download='data:application/json;base64,'+base64.b64encode(json.dumps(r,ensure_ascii=False).encode()).decode()
s=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>虾仁紫菜鲜肉馄饨 · 小厨房</title><style>{css}</style></head><body><main><div class="label">小厨房 / 视频提炼菜谱</div><h1>虾仁紫菜鲜肉馄饨<small>预计 57–92 分钟 · 含备菜与包制，补充估算</small></h1><p class="lead">虾油提香，紫菜添鲜。基础馅分成韭菜、玉米两种口味。</p><p class="note">整批份量未注明；包得越多，耗时越长。手机可左右滑动步骤卡。</p><div class="info"><b>一次备齐 · 一项一行</b><ul class="prep-list">{rows}</ul><p class="note">虾油由虾头和食用油制得。盐、生抽同时用于拌馅与汤底，葱同时用于香料水与汤底；适量不代表固定比例。</p><b>备菜顺序</b><ol>{prep}</ol><b>搭配其他菜的顺序建议</b><p>手工包制最耗时，建议提前包好；有炖菜时先炖上，再利用等待时间拌馅、包馄饨。临近开饭烧水煮馄饨，快手蔬菜最后炒。多余馄饨可分装冷冻，下次省去包制时间。</p></div><div class="actions"><a href="{download}" download="虾仁紫菜鲜肉馄饨.json">下载小厨房导入 JSON</a></div><section class="grid">{cards}</section><footer>来源：小红书「糯妈」 · <a href="{r['source']}">原笔记</a><br>图片为原视频截图，文字依据画面及烧录字幕整理，未独立转写音频。总耗时为估算，原片未给煮制分钟数。熟度检查和冷冻后密封保存为补充建议。</footer></main></body></html>'''
(root/'index.html').write_text(s)
print('Built wonton recipe')
