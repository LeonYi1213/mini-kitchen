from pathlib import Path
import json,html,base64,re
root=Path(__file__).resolve().parents[1]/'web/recipes/squid-rice-cakes'
items=[('小管鱿鱼',None,'适量'),('年糕',None,'适量'),('葱段',20,'克'),('姜粒或姜片',20,'克'),('蒜瓣',20,'克'),('红葱头',15,'克'),('干辣椒',2,'段'),('五花肉薄片',30,'克'),('鸡高汤',100,'克'),('盐',2.5,'克'),('糖',7,'克'),('鸡汁',4,'克'),('花雕酒',20,'克'),('鸡油',None,'适量'),('鸡饭老抽或老抽',None,'适量')]
steps=[
('prep','备好鱿鱼与酱汁','鱿鱼去内脏、透明软骨及嘴部硬喙，剪开眼部后清洗、沥水。高汤 100 克、盐 2.5 克、糖 7 克、鸡汁 4 克混匀备用。','00:20–00:35'),
('aromatics','炒香姜粒、肉片和蒜瓣','锅中下鸡油，姜粒先炒至金黄，再下五花肉薄片煸出油脂，加入蒜瓣、红葱头和干辣椒炒香；葱段留后放。','00:46–00:59'),
('sauce','烹花雕，倒酱汁','转大火，沿锅边烹入约 20 克花雕酒，倒入提前调好的高汤酱汁。','01:00–01:05'),
('rice','先把年糕煮软','放入年糕，煮至汤汁沸腾、年糕熟软，让淀粉自然增稠；具体煮制时间按年糕厚薄调整。','01:06–01:12'),
('squid','最后下鱿鱼，大火快煮','加入葱段和处理好的鱿鱼，大火翻煮至鱿鱼熟透，少量鸡饭老抽调色；没有鸡饭老抽可用普通老抽。','01:12–01:20'),
('finish','装盘，留住鲜味汤汁','食材盛盘并浇上汤汁。作者提到餐厅会过滤酱汁去掉姜粒等，家常做法可直接装盘。','01:21–01:39')]
r={'id':'xhs-6abadd69000000000b007bc4','title':'小管鱿鱼烧年糕','servings':None,'source':'https://www.xiaohongshu.com/explore/6abadd69000000000b007bc4','ingredients':[{'name':n,'amount':a,'unit':u} for n,a,u in items], 'prep':['鱿鱼去内脏、透明软骨、嘴部硬喙，剪开眼部并清洗沥水。','准备年糕，葱切段，姜切粒或片，红葱头切好，蒜瓣保留整粒；五花肉切薄片。','将高汤 100 克、盐 2.5 克、糖 7 克、鸡汁 4 克混匀。'],'cook':[s[2] for s in steps[1:]],'timing':{'prep':[{'min':8,'max':12},{'min':3,'max':5},{'min':2,'max':3}],'cook':[{'min':3,'max':5},{'min':2,'max':3},{'min':3,'max':5},{'min':2,'max':3},{'min':2,'max':4}]},'notes':['依据视频画面与烧录字幕整理，未独立转写音频。','鱿鱼、年糕和鸡油用量未注明，显示为适量；多数调料克数来自字幕，花雕和五花肉为约数。','作者实际用鸡油；字幕另给餐厅版猪油 30 克＋植物油 20 克，作为替代用油方案，不需再叠加鸡油。','红葱头可用普通洋葱替代，五花肉可用梅花肉片，高汤可用鱼高汤。','视频中的鱼块盐腌 10 分钟是做鱼时的分支，不适用于本版鱿鱼。','总耗时 25–40 分钟为补充估算，不是原视频宣称时间；年糕厚薄和鱿鱼大小会影响实际时间。'],'illustrated_steps':[{'title':s[1],'text':s[2],'source_time':s[3],'image':s[0]+'.jpg'} for s in steps]}
(root/'recipe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
def image(n):return 'data:image/jpeg;base64,'+base64.b64encode((root/(n+'.jpg')).read_bytes()).decode()
css=re.search(r'<style>(.*?)</style>',(root.parent/'pepper-ribs/index.html').read_text(),re.S)[1]
css+=' .step:nth-child(4) img{object-position:50% 65%}'
rows=''.join('<li>'+html.escape(n)+'：'+(str(a)+' '+u if a is not None else '适量')+'</li>' for n,a,u in items)
cards=''.join(f'<article class="step"><img src="{image(n)}" alt="{title}，原片截图"><div><small>STEP {i:02} · 原片 {time}</small><h2>{title}</h2><p>{text}</p></div></article>' for i,(n,title,text,time) in enumerate(steps,1))
json_url='data:application/json;base64,'+base64.b64encode(json.dumps(r,ensure_ascii=False).encode()).decode()
s=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>小管鱿鱼烧年糕 · 小厨房</title><style>{css}</style></head><body><main><div class="label">小厨房 / 视频提炼菜谱</div><h1>小管鱿鱼烧年糕 <small>预计 25–40 分钟 · 含备菜，补充估算</small></h1><p class="lead">姜蒜肉香打底，年糕吸饱鲜汁。鱿鱼最后下锅，鲜嫩出锅。</p><p class="note">作者称“复刻米其林同款”，本菜谱按视频实际操作整理，非餐厅官方配方。份量未注明。</p><div class="info"><b>一次备齐 · 一项一行</b><ul class="prep-list">{rows}</ul><p class="note">五花肉、花雕酒为约数；未注明的用量显示适量。上述调味比例对应作者这锅食材，鱿鱼与年糕总重量未知。</p><b>用油与替代</b><p>视频实用鸡油。餐厅版用猪油 30 克＋植物油 20 克，可作为另一方案，二选一。红葱头可换洋葱，五花肉可换梅花肉，高汤可换鱼高汤。</p><b>和青椒排骨一起做</b><ol><li>先把排骨焯水、煎香、炖上。</li><li>利用炖煮时间处理鱿鱼、切配、调汁；暂不用的海鲜冷藏。</li><li>临近上桌再做这道菜，年糕先熟，鱿鱼最后下锅。</li></ol><p class="note">以上为多菜安排建议。鱿鱼、年糕的成熟时间未在原片明确，按实际状态判断。</p></div><div class="actions"><a href="{json_url}" download="小管鱿鱼烧年糕.json">下载小厨房导入 JSON</a></div><section class="grid">{cards}</section><footer>来源：小红书「小面包^s kitchen🍞」《复刻米其林同款海鲜料理》 · <a href="{r['source']}">原笔记</a><br>图片为原片截图，文字依据画面与烧录字幕提炼，未独立转写音频。视频提到的“鱼块撒盐腌 10 分钟”属于鱼的替代做法，不是鱿鱼步骤。</footer></main></body></html>'''
(root/'index.html').write_text(s)
print('Built squid recipe HTML and JSON')
