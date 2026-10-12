/* Local, explainable estimates; no remote model or invented source timings. */
(function(root){
function estimateStep(text, stage, provided){
  if(provided && Number.isFinite(provided.min) && Number.isFinite(provided.max) && provided.min>0 && provided.max>=provided.min && provided.max<=1440)
    return {...provided,wait:provided.wait===true};
  const m=text.match(/(?:约)?\s*(\d+(?:\.\d+)?)\s*(?:[–—~-]|至|到)?\s*(\d+(?:\.\d+)?)?\s*(分钟|小时)/);
  const wait=/炖|焖|蒸|腌|烤|浸泡|冷藏|发酵/.test(text) && !/炖过|炖熟|炖排骨时|不必|不要|短暂/.test(text);
  if(m){const scale=m[3]==='小时'?60:1;const min=+m[1]*scale,max=+(m[2]||m[1])*scale;if(min>0&&max>=min&&max<=1440)return {min,max,wait};}
  if(wait)return {min:15,max:25,wait:true};
  if(/焯/.test(text))return {min:5,max:8,wait:false};
  return stage===0?{min:3,max:5,wait:false}:{min:3,max:6,wait:false};
}
function steps(recipe,stage){return (stage===0?recipe.prep:recipe.cook).map((text,index)=>({text,index,stage,key:`${stage}-${index}`,...estimateStep(text,stage,recipe.timing?.[stage===0?'prep':'cook']?.[index])}));}
function total(recipe){return [...steps(recipe,0),...steps(recipe,1)].reduce((a,s)=>({min:a.min+s.min,max:a.max+s.max}),{min:0,max:0});}
function format(t){return t.min===t.max?`约 ${t.min} 分钟`:`约 ${t.min}–${t.max} 分钟`;}
function plan(recipes,menu,now=Date.now()){
 const active=menu.filter(m=>m.stage!==2);const waiting=[],actions=[];
 for(const m of active){const r=recipes.find(r=>r.id===m.id);if(!r)continue;const pending=steps(r,m.stage).find(s=>!m.checked?.[s.key]);
  if(!pending){actions.push({id:m.id,title:r.title,text:m.stage===0?'备菜已完成，切换到烹饪。':'步骤已勾完，确认熟度后标记完成。',score:m.stage===0?total(r).max:2000,reason:'完成当前阶段，再进入下一阶段。'});continue;}
  if(m.wait?.key===pending.key){const remaining=Math.max(0,Math.ceil((m.wait.until-now)/60000));if(remaining>0){waiting.push({id:m.id,title:r.title,remaining});continue;}actions.push({id:m.id,title:r.title,text:`检查熟度：${pending.text}`,score:3000,reason:'预计等待时间已到，请检查实际状态；确认后勾选步骤。'});continue;}
  const slow=steps(r,1).some(s=>s.wait);const quick=/青菜|蒜蓉|生菜|油麦|菠菜/.test(r.title);
  actions.push({id:m.id,title:r.title,text:pending.text,time:format(pending),score:m.stage===1?1000+(slow?100:0):total(r).max+(slow?100:0)-(quick?50:0),reason:m.stage===1?'已进入烹饪，先处理当前锅中的步骤。':slow?'这道菜有较长等待时间，优先备好并炖上。':quick?'叶菜尽量临近上桌再炒；现在可先洗切。':'先完成洗切与调味准备，减少下锅后的忙乱。'});
 }
 actions.sort((a,b)=>b.score-a.score);
 return {actions,waiting};
}
const api={estimateStep,steps,total,format,plan};root.KitchenPlanner=api;if(typeof module!=='undefined')module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
