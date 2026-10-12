from pathlib import Path
import json,base64,re,html,subprocess
root=Path(__file__).resolve().parents[1]/'web/recipes/milk-pudding'
root.mkdir(parents=True,exist_ok=True)
note='6940681d000000001e009bdf'
steps=[('mix',10,'称料混合，吉利丁冷水泡软','吉利丁片 2 克用冷水泡软。锅中加入奶粉 10 克、全脂牛奶 160 克、淡奶油 70 克、炼乳 30 克、木薯淀粉 2 克，充分拌匀。','00:08–00:20'),('heat',22,'中火加热至约 70℃','一边搅拌一边中火加热，原片加热至约 70℃，不要把标题的 10 分钟当作固定加热时长。','00:21–00:22'),('gelatin',25,'加入泡软吉利丁，调味','加入泡软的吉利丁片，搅至溶解；盐一小撮、黑朗姆酒 2 克用于提味。泡片的冷水不倒入奶液，沥去多余水分为补充建议。','00:23–00:28'),('strain',31,'过滤倒入容器','将奶液过筛倒入耐热碗或布丁杯，滤去未化开的粉类颗粒。原片未注明杯容量及份数。','00:29–00:32'),('chill',34,'撇去气泡，冷藏至少 6 小时','用勺子撇去表面气泡，盖保鲜膜，放冰箱冷藏 6 小时以上至凝固。原片是非常嫩的匙食口感。','00:33–00:35'),('serve',39,'凝固后用勺享用','冷藏至整体凝固后直接用勺食用。此配方吉利丁用量低，不将原片碗装成品理解成可稳固脱模的布丁。','00:36–00:43')]
for n,t,*_ in steps:
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(root.parents[2]/f'imports/{note}.mp4'),'-vf','scale=480:-1','-frames:v','1',str(root/(n+'.jpg'))],check=True)
items=[('奶粉',10,'克'),('全脂牛奶',160,'克'),('淡奶油',70,'克'),('炼乳',30,'克'),('木薯淀粉',2,'克'),('吉利丁片',2,'克'),('盐',1,'小撮'),('黑朗姆酒',2,'克'),('冷水（泡吉利丁用）',None,'适量')]
r={'id':'xhs-'+note,'title':'嫩滑牛乳布丁','servings':None,'source':'https://www.xiaohongshu.com/explore/'+note,'ingredients':[{'name':n,'amount':a,'unit':u} for n,a,u in items],'prep':['称量各项食材，吉利丁片用冷水泡软；准备滤网和耐热容器。'],'cook':[s[3] for s in steps],'timing':{'prep':[{'min':3,'max':5}],'cook':[{'min':1,'max':2},{'min':3,'max':5},{'min':1,'max':2},{'min':1,'max':2},{'min':361,'max':361,'wait':True},{'min':1,'max':1}]},'notes':['来源：小面包^s kitchen🍞。依据全片逐秒抽帧与烧录字幕整理，未独立转写音频。','全部明确克数来自画面配方；盐一小撮，泡吉利丁用水量未注明显示适量。','原片中火加热至约 70℃，再加泡软吉利丁；未给吉利丁片凝胶强度，不保证不同品牌口感完全相同。','原片要求冷藏 6 小时以上；标题 10 分钟不包括冷藏。预计操作约 11–18 分钟，加最低冷藏后累计 371–378 分钟，可能需更久才凝固。','泡片用水不倒入奶液、沥去多余水分为补充建议。','原片为碗装、非常嫩的匙食布丁，未演示脱模，份数和容器容量未注明。','与市售产品相似程度是作者主观表述，未独立验证。'],'illustrated_steps':[{'title':s[2],'text':s[3],'source_time':s[4],'image':s[0]+'.jpg'} for s in steps]}
(root/'recipe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
css=re.search(r'<style>(.*?)</style>',(root.parent/'pepper-ribs/index.html').read_text(),re.S)[1]+'.step img,.step:nth-child(4) img{object-position:50% 55%}'
def img(n):return 'data:image/jpeg;base64,'+base64.b64encode((root/(n+'.jpg')).read_bytes()).decode()
rows=''.join('<li>'+html.escape(n)+'：'+(str(a)+' '+html.escape(u) if a is not None else '适量')+'</li>' for n,a,u in items)
prep=''.join('<li>'+html.escape(x)+'</li>' for x in r['prep'])
cards=''.join(f'<article class="step"><img src="{img(n)}" alt="{title}，原视频截图"><div><small>STEP {i:02} · 原片 {time}</small><h2>{title}</h2><p>{text}</p></div></article>' for i,(n,t,title,text,time) in enumerate(steps,1))
download='data:application/json;base64,'+base64.b64encode(json.dumps(r,ensure_ascii=False).encode()).decode()
s=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>嫩滑牛乳布丁 · 小厨房</title><style>{css}</style></head><body><main><div class="label">小厨房 / 视频提炼菜谱</div><h1>嫩滑牛乳布丁<small>预计 371–378 分钟 · 按最低冷藏 6 小时估算，补充估算</small></h1><p class="lead">牛奶、奶油与炼乳叠出奶香，吉利丁做出柔嫩匙食口感。</p><p class="note">操作约 11–18 分钟，另需冷藏 6 小时以上；未凝固时继续冷藏，不能 10 分钟直接开吃。手机可左右滑动步骤卡。</p><div class="info"><b>一次备齐 · 一项一行</b><ul class="prep-list">{rows}</ul><p class="note">吉利丁片先用冷水泡软；泡片用水不计入奶液。原片容器容量和份数未注明。</p><b>备菜顺序</b><ol>{prep}</ol><b>搭配其他菜的顺序建议</b><p>这道甜点至少提前 6 小时制作，建议上午或前一天做好冷藏。之后再安排晚餐热菜，开饭前确认布丁凝固，继续冷藏至享用。</p></div><div class="actions"><a href="{download}" download="嫩滑牛乳布丁.json">下载小厨房导入 JSON</a></div><section class="grid">{cards}</section><footer>来源：小红书「小面包^s kitchen🍞」 · <a href="{r['source']}">原笔记</a><br>图片为原视频截图，文字依据画面及烧录字幕整理，未独立转写音频。约 70℃加热、冷藏 6 小时以上为原片说明。操作及累计耗时为估算，泡片水的处理为补充建议。</footer></main></body></html>'''
(root/'index.html').write_text(s)
print('Built milk pudding recipe')
