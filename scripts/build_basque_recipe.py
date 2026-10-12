from pathlib import Path
import json,base64,re,html,subprocess
root=Path(__file__).resolve().parents[1]/'web/recipes/milk-basque-cheesecake'
root.mkdir(parents=True,exist_ok=True)
note='695cfb00000000001a02bcad'
steps=[('soften',14,'奶酪软化，拌入面粉和黄油','奶油奶酪提前软化至能轻松按压；黄油软化至牙膏状。奶酪加入低筋面粉和黄油，搅拌均匀。','00:12–00:17'),('sugar',20,'加入蜂蜜和白糖','加入蜂蜜 15 克、白糖 50 克，拌匀至细腻。','00:18–00:25'),('egg',28,'全蛋液分三次加','130 克常温全蛋液分 3 次加入，每次充分拌匀再加下一次；按重量称，不直接替换为固定鸡蛋个数。','00:26–00:31'),('milk',36,'加柠檬汁、温牛奶，过滤','加入柠檬汁 5 克和温牛奶 200 克拌匀；过筛 3 遍，筛出的颗粒弃去。倒入铺好烘焙纸的模具，原片未注明模具尺寸。','00:32–00:39'),('bake',44,'参考 230℃烤 21 分钟','作者用美的 P40pro 平炉模式，未预热，230℃烤 21 分钟；正文提示其他烤箱需预热。此温时仅作参考，须结合模具尺寸、糊深及自家烤箱调整。','00:40–00:47'),('chill',50,'放凉冷藏后脱模','出炉时中心晃动明显。先放凉再冷藏、定型后脱模切块；作者冷藏了 3.5 小时，放凉操作为补充建议。','00:46–00:54')]
for n,t,*_ in steps:
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(root.parents[2]/f'imports/{note}.mp4'),'-vf','scale=480:-1','-frames:v','1',str(root/(n+'.jpg'))],check=True)
items=[('奶油奶酪',350,'克'),('低筋面粉',8,'克'),('黄油',50,'克'),('蜂蜜',15,'克'),('白糖',50,'克'),('全蛋液',130,'克'),('柠檬汁',5,'克'),('牛奶',200,'克')]
r={'id':'xhs-'+note,'title':'无淡奶油巴斯克','servings':None,'source':'https://www.xiaohongshu.com/explore/'+note,'ingredients':[{'name':n,'amount':a,'unit':u} for n,a,u in items],'prep':['称量全部原料，奶油奶酪与黄油提前软化，蛋液回温，牛奶温热。','准备烘焙纸、滤网及模具；原片未注明模具尺寸，其他烤箱按说明预热。'],'cook':[s[3] for s in steps],'timing':{'prep':[{'min':5,'max':8},{'min':3,'max':5}],'cook':[{'min':3,'max':5},{'min':2,'max':3},{'min':3,'max':5},{'min':4,'max':6},{'min':21,'max':21,'wait':True},{'min':240,'max':270,'wait':True}]},'notes':['来源：小欢欢的厨房。依据全片抽帧、烧录字幕和笔记正文整理，未独立转写音频。','原料克数均为原片配方；无淡奶油不等于无乳制品，含奶油奶酪、黄油、牛奶。','模具直径、高度与份数未注明，不推断为六寸或其他尺寸。','230℃、21 分钟对应作者美的 P40pro 平炉模式不预热演示；其他烤箱正文要求预热，不能保证同时间同效果。','原片冷藏 3.5 小时；预计累计 281–323 分钟（约 4 小时 41 分至 5 小时 23 分），含补充估计放凉 30–60 分钟。未另计原料软化与烤箱预热等待。','放凉后冷藏为补充建议；预计实际操作约 20–32 分钟，其余主要为烘烤和冷却冷藏。','低糖、名师配方和零失败为笔记标题或作者表述，未独立核实名师出处、营养比较或成功率。'],'illustrated_steps':[{'title':s[2],'text':s[3],'source_time':s[4],'image':s[0]+'.jpg'} for s in steps]}
(root/'recipe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
css=re.search(r'<style>(.*?)</style>',(root.parent/'pepper-ribs/index.html').read_text(),re.S)[1]+'.step img,.step:nth-child(4) img{object-position:50% 55%}'
def img(n):return 'data:image/jpeg;base64,'+base64.b64encode((root/(n+'.jpg')).read_bytes()).decode()
rows=''.join('<li>'+html.escape(n)+'：'+(str(a)+' '+html.escape(u) if a is not None else '适量')+'</li>' for n,a,u in items)
prep=''.join('<li>'+html.escape(x)+'</li>' for x in r['prep'])
cards=''.join(f'<article class="step"><img src="{img(n)}" alt="{title}，原视频截图"><div><small>STEP {i:02} · 原片 {time}</small><h2>{title}</h2><p>{text}</p></div></article>' for i,(n,t,title,text,time) in enumerate(steps,1))
download='data:application/json;base64,'+base64.b64encode(json.dumps(r,ensure_ascii=False).encode()).decode()
s=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>无淡奶油巴斯克 · 小厨房</title><style>{css}</style></head><body><main><div class="label">小厨房 / 视频提炼菜谱</div><h1>无淡奶油巴斯克<small>预计 281–323 分钟 · 含烘烤、放凉与冷藏，补充估算</small></h1><p class="lead">蜂蜜与柠檬添香，以牛奶制作，不额外加淡奶油。</p><p class="note">约 4 小时 41 分至 5 小时 23 分，实际操作约 20–32 分钟。软化与预热等待另计。手机可左右滑动步骤卡。</p><div class="info"><b>一次备齐 · 一项一行</b><ul class="prep-list">{rows}</ul><p class="note">模具尺寸与份数未注明。原片配方克数完整，蛋液需称重；仍含乳制品。</p><b>备菜顺序</b><ol>{prep}</ol><b>搭配其他菜的顺序建议</b><p>这道甜点需要较长冷藏时间，建议上午或前一天先做好，再安排晚餐热菜。烘烤、冷藏阶段可处理其他菜，烘烤时注意上色情况；临吃前再脱模切块。</p></div><div class="actions"><a href="{download}" download="无淡奶油巴斯克.json">下载小厨房导入 JSON</a></div><section class="grid">{cards}</section><footer>来源：小红书「小欢欢的厨房」 · <a href="{r['source']}">原笔记</a><br>图片为原视频截图，文字依据画面及烧录字幕整理，未独立转写音频。温时、冷藏时长为作者演示参考，模具尺寸未注明；总耗时与放凉时间为补充估算，不保证不同设备一次成功。</footer></main></body></html>'''
(root/'index.html').write_text(s)
print('Built basque recipe')
