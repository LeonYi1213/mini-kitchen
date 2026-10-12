from pathlib import Path
import json,base64,re,html,subprocess
root=Path(__file__).resolve().parents[1]/'web/recipes/home-seafood-rice'
root.mkdir(parents=True,exist_ok=True)
note='6a7db830000000002c0012e0'
steps=[('aromatics',24,'蒜末、洋葱炒香','少量油烧热，中火炒蒜末至微微上色，再加洋葱丁炒香。','00:12–00:30'),('vegetables',65,'加入蔬菜炒出香气','依次加入彩椒条、芹菜梗丁、胡萝卜片和番茄，炒至蔬菜变软、略有焦香，避免炒糊。','00:30–01:18'),('broth',97,'加水调成鲜香汤底','加入黑胡椒、酒、香叶和盐；喜欢辣可加干辣椒。加水煮出蔬菜味，十三香按喜好加。取出香叶，尝味后加少量酱油，酌情补盐和黑胡椒。','01:18–02:35'),('rice',192,'生米拌入汤底','将生大米倒入汤底拌匀，按米种和锅具调整水量。原片没有固定米水比例，不要照搬画面水位作为通用配比。','02:59–03:18'),('seafood',222,'铺上海鲜，小火加盖焖','放上剖开去虾线的虾、鱿鱼和蛤蜊，让海鲜接触汤汁，加盖小火焖。原片选择米与海鲜同煮，以便米饭吸收鲜味。','03:18–03:59'),('finish',268,'检查收水与熟度，撒葱花','焖约 10 分钟时开盖检查，仍有水则继续小火焖。米饭无硬芯、海鲜熟透后撒葱花；若水干而米未熟，补少量热水续焖。','04:00–04:42')]
for n,t,*_ in steps:
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(root.parents[2]/f'imports/{note}.mp4'),'-vf','scale=480:-1','-frames:v','1',str(root/(n+'.jpg'))],check=True)
names=['大米','虾','鱿鱼','蛤蜊','蒜','洋葱','彩椒','芹菜梗','胡萝卜','番茄','葱花','食用油','黑胡椒','盐','酱油','酒（品种未限定）','香叶','干辣椒（可选）','十三香（可选）','水']
r={'id':'xhs-'+note,'title':'家常海鲜饭','servings':'2–3','source':'https://www.xiaohongshu.com/explore/'+note,'ingredients':[{'name':n,'amount':None,'unit':'适量'} for n in names],'prep':['蒜切末、洋葱和芹菜梗切丁。','彩椒切条，胡萝卜切片，番茄切块，葱切葱花。','虾剖开去虾线；鱿鱼清理切圈，蛤蜊处理干净。','备好大米、水和各项调味料，十三香与干辣椒按喜好准备。'],'cook':[s[3] for s in steps],'timing':{'prep':[{'min':3,'max':4},{'min':4,'max':5},{'min':6,'max':9},{'min':2,'max':2}],'cook':[{'min':2,'max':3},{'min':5,'max':7},{'min':3,'max':5},{'min':1,'max':2},{'min':15,'max':20,'wait':True},{'min':2,'max':3}]},'notes':['依据原视频画面和烧录字幕整理，未独立转写音频。作者：张曦福。','原片称一锅可供 2–3 人食用，没有固定用量与米水比例，未标注用量显示适量。','总耗时约 43–60 分钟为含备菜的补充估算，不含蛤蜊额外吐沙时间；焖制时间随米种、锅具和火力变化。','原片 10 分钟仅为开盖检查时点，当时仍有水，不代表已煮熟。','原片讨论过先煮米、最后加海鲜的另一种方式，本菜谱保留实际演示的米与海鲜同煮方式。','补充建议：检查米饭无硬芯、虾肉不透明且海鲜充分熟透；未开口蛤蜊弃用，水干米未熟时补热水续焖。','标题减脂不能作为营养结论；原片用量不足以计算热量或承诺减脂效果。'],'illustrated_steps':[{'title':s[2],'text':s[3],'source_time':s[4],'image':s[0]+'.jpg'} for s in steps]}
(root/'recipe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
css=re.search(r'<style>(.*?)</style>',(root.parent/'pepper-ribs/index.html').read_text(),re.S)[1]+'.step img,.step:nth-child(4) img{object-position:50% 85%}'
def img(n):return 'data:image/jpeg;base64,'+base64.b64encode((root/(n+'.jpg')).read_bytes()).decode()
rows=''.join('<li>'+html.escape(n)+'：适量</li>' for n in names)
prep=''.join('<li>'+html.escape(x)+'</li>' for x in r['prep'])
cards=''.join(f'<article class="step"><img src="{img(n)}" alt="{title}，原视频截图"><div><small>STEP {i:02} · 原片 {time}</small><h2>{title}</h2><p>{text}</p></div></article>' for i,(n,t,title,text,time) in enumerate(steps,1))
download='data:application/json;base64,'+base64.b64encode(json.dumps(r,ensure_ascii=False).encode()).decode()
s=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>家常海鲜饭 · 小厨房</title><style>{css}</style></head><body><main><div class="label">小厨房 / 视频提炼菜谱</div><h1>家常海鲜饭<small>预计 43–60 分钟 · 含备菜，补充估算</small></h1><p class="lead">先炒蔬菜汤底，再让米饭吸饱虾、鱿鱼和蛤蜊的鲜味。</p><p class="note">原片称可供 2–3 人食用。用量、米水比例未限定；不含额外吐沙时间。手机可左右滑动步骤卡。</p><div class="info"><b>一次备齐 · 一项一行</b><ul class="prep-list">{rows}</ul><b>备菜顺序</b><ol>{prep}</ol><b>今晚多道菜怎么安排？</b><p>有炖肉时先把炖肉做上，再处理海鲜饭。饭开始小火焖后，利用等待时间给其他菜洗切、调汁；快手丝瓜等临近开饭再炒。同一口锅须依次操作，焖饭时仍需留意水量与火候。</p><p class="note">以上是搭配安排建议；导入小厨房并选中多道菜后，可按各菜当前阶段查看优先级。</p></div><div class="actions"><a href="{download}" download="家常海鲜饭.json">下载小厨房导入 JSON</a></div><section class="grid">{cards}</section><footer>来源：小红书「张曦福」 · <a href="{r['source']}">原笔记</a><br>图片为原视频截图，文字依据画面与烧录字幕整理，未独立转写音频。10 分钟为检查时点；总耗时为估算。检查熟度、未开口蛤蜊弃用及补热水续焖为补充建议。原片未提供足够用量信息，无法据此计算热量或确认减脂效果。</footer></main></body></html>'''
(root/'index.html').write_text(s)
print('Built seafood rice recipe')
