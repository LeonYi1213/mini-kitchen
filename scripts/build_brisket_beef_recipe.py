from pathlib import Path
import json,base64,re,html,subprocess
root=Path(__file__).resolve().parents[1]/'web/recipes/shacha-brisket-beef'
root.mkdir(parents=True,exist_ok=True)
note='69c4dc80000000001b020081'
steps=[('slice',12,'稍冻后切薄片','胸口油和牛肉稍微冷冻至便于下刀，分别尽量切薄片；原片未给冷冻时间。','00:05–00:15'),('season',24,'两种肉分别调味','牛肉加酱油、蚝油、沙茶酱、淀粉和食用油拌匀；胸口油只加酱油、水、淀粉拌匀。原片未要求固定腌制时间。','00:16–00:26'),('sauce',36,'切好配菜，提前调汁','洋葱、红黄彩椒切条，小葱切段、葱白葱绿分开，姜蒜切好。酱油、蚝油、沙茶酱、黑胡椒粉、水和淀粉调成酱汁。','00:27–00:38'),('render',46,'中火煸胸口油，盛出','胸口油下锅，中火慢慢煸出油脂，煎至表面焦黄、口感焦脆后盛出，锅中留油继续炒。','00:39–00:48'),('beef',51,'牛肉快速煎炒，盛出','牛肉下锅快速煎炒至变色后暂时盛出，后续还需回锅炒熟；避免久炒变老。','00:49–00:55'),('finish',69,'炒香配菜，回锅合炒','姜、蒜、葱白与洋葱、彩椒下锅炒香，再倒回牛肉和胸口油。翻炒时加入调好的酱汁，大火快炒至肉熟、酱汁裹匀，撒葱绿出锅。','00:56–01:10')]
for n,t,*_ in steps:
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(root.parents[2]/f'imports/{note}.mp4'),'-vf','scale=480:-1','-frames:v','1',str(root/(n+'.jpg'))],check=True)
items=[(n,None,'适量') for n in ['胸口油','牛肉','洋葱','红彩椒','黄彩椒','小葱','姜','蒜','酱油','蚝油','沙茶酱','淀粉','食用油','黑胡椒粉','水']]
r={'id':'xhs-'+note,'title':'沙茶胸口油炒牛肉','servings':None,'source':'https://www.xiaohongshu.com/explore/'+note,'ingredients':[{'name':n,'amount':a,'unit':u} for n,a,u in items],'prep':[s[3] for s in steps[:3]],'cook':[s[3] for s in steps[3:]],'timing':{'prep':[{'min':4,'max':6},{'min':2,'max':3},{'min':5,'max':7}],'cook':[{'min':5,'max':8},{'min':1,'max':2},{'min':3,'max':4}]},'notes':['来源：开饭啦小志。依据全片抽帧与关键段加密画面、烧录字幕整理，未独立转写音频。','全部食材用量和人数未注明，未知用量显示适量。','预计 20–30 分钟为补充估算，不含将肉稍冻变硬的等待时间；原片未注明烹饪分钟数。','原片胸口油用酱油、水、淀粉拌匀，牛肉另加蚝油、沙茶酱和食用油；酱汁需提前调好。','原片配菜允许按喜好搭配，菜谱保留演示的洋葱、红黄彩椒、姜蒜和小葱。','牛肉第一次盛出只是中间步骤，最后仍需回锅炒熟；熟度提醒为补充建议。'],'illustrated_steps':[{'title':s[2],'text':s[3],'source_time':s[4],'image':s[0]+'.jpg'} for s in steps]}
(root/'recipe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
css=re.search(r'<style>(.*?)</style>',(root.parent/'pepper-ribs/index.html').read_text(),re.S)[1]+'.step img,.step:nth-child(4) img{object-position:50% 55%}'
def img(n):return 'data:image/jpeg;base64,'+base64.b64encode((root/(n+'.jpg')).read_bytes()).decode()
rows=''.join('<li>'+html.escape(n)+'：'+(str(a)+' '+html.escape(u) if a is not None else '适量')+'</li>' for n,a,u in items)
prep=''.join('<li>'+html.escape(x)+'</li>' for x in r['prep'])
cards=''.join(f'<article class="step"><img src="{img(n)}" alt="{title}，原视频截图"><div><small>STEP {i:02} · 原片 {time}</small><h2>{title}</h2><p>{text}</p></div></article>' for i,(n,t,title,text,time) in enumerate(steps,1))
download='data:application/json;base64,'+base64.b64encode(json.dumps(r,ensure_ascii=False).encode()).decode()
s=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>沙茶胸口油炒牛肉 · 小厨房</title><style>{css}</style></head><body><main><div class="label">小厨房 / 视频提炼菜谱</div><h1>沙茶胸口油炒牛肉<small>预计 20–30 分钟 · 含备菜，补充估算</small></h1><p class="lead">胸口油煸到焦脆，牛肉快炒保嫩，沙茶酱汁最后合炒。</p><p class="note">份量未注明；预计耗时不含稍冻肉的等待时间。手机可左右滑动步骤卡。</p><div class="info"><b>一次备齐 · 一项一行</b><ul class="prep-list">{rows}</ul><p class="note">酱油、水、淀粉分用于两种肉的处理及酱汁；按各步骤分别取用。未标注用量统一显示适量。</p><b>备菜顺序</b><ol>{prep}</ol><b>搭配其他菜的顺序建议</b><p>有炖菜时先炖上，利用等待时间切薄肉片、切配菜、调酱汁。这道快炒菜接近开饭再下锅；胸口油先煸，牛肉后炒，保持各自口感。单锅做多菜时，提前备齐各菜再依次炒制。</p></div><div class="actions"><a href="{download}" download="沙茶胸口油炒牛肉.json">下载小厨房导入 JSON</a></div><section class="grid">{cards}</section><footer>来源：小红书「开饭啦小志」 · <a href="{r['source']}">原笔记</a><br>图片为原视频截图，文字依据画面及烧录字幕整理，未独立转写音频。总耗时为估算，原片未给具体烹饪分钟数。牛肉最终炒熟的提醒为补充建议。</footer></main></body></html>'''
(root/'index.html').write_text(s)
print('Built brisket beef recipe')
