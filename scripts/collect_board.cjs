// Collect only notes exposed by normal browser navigation; save resumable results.
const fs=require('node:fs');const path=require('node:path');const {chromium}=require('playwright');
(async()=>{
 const url=new URL(process.argv[2]);if(url.protocol!=='https:'||url.hostname!=='www.xiaohongshu.com'||!/^\/board\/[a-f0-9]{24}$/.test(url.pathname))throw Error('Expected a Xiaohongshu board URL');
 const out=path.resolve(process.argv[3]||'imports/board');fs.mkdirSync(out,{recursive:true});
 const existing=new Set();const recipeRoot=path.resolve('web/recipes');
 function scan(dir){for(const entry of fs.readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,entry.name);if(entry.isDirectory())scan(p);else if(entry.name==='recipe.json'){const r=JSON.parse(fs.readFileSync(p,'utf8'));const id=r.source?.match(/\/(?:explore|discovery\/item)\/([a-f0-9]{24})/i)?.[1];if(id)existing.add(id)}}}
 if(fs.existsSync(recipeRoot))scan(recipeRoot);
 const b=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',...(process.env.HTTPS_PROXY?{proxy:{server:process.env.HTTPS_PROXY}}:{})});
 const notes=new Map(),failed=new Set(),apiFailures=[];let total=null,hasMore=true,stable=0,restriction=null;
 try{const p=await b.newPage();p.on('requestfailed',r=>{if(r.failure()?.errorText.includes('TUNNEL'))failed.add(new URL(r.url()).hostname)});
 p.on('response',r=>{const u=new URL(r.url());if(u.pathname.includes('/api/')&&r.status()>=400)apiFailures.push({host:u.hostname,path:u.pathname,status:r.status()})});
 await p.goto(url.href,{waitUntil:'domcontentloaded',timeout:45000});
 for(let page=0;page<100;page++){
  await p.waitForTimeout(1500);
  const body=await p.locator('body').innerText();
  if(/IP at risk|300012/.test(body)){restriction={type:'site_ip_restriction',code:'300012',message:'小红书限制当前出口 IP；不是空专辑，也不是 JSON 解析错误。'};break;}
  if(apiFailures.some(x=>x.status===461))restriction={type:'site_session_rejected',status:461,message:'网站拒绝访客会话，列表尚未正常加载。'};
  const data=await p.evaluate(()=>{const unref=v=>v?.__v_isRef?v.value:v;const board=window.__INITIAL_STATE__?.board;if(!board)return null;const details=unref(board.boardDetails),map=unref(board.boardFeedsMap);const feed=map?.[details?.id];return {total:details?.total,hasMore:feed?.hasMore,notes:(feed?.notes||[]).map(n=>({id:n.id||n.noteId,title:n.noteCard?.displayTitle||n.displayTitle||n.title||'',token:n.xsecToken||n.noteCard?.xsecToken||''}))}});
  if(!data)break;total=data.total??null;hasMore=data.hasMore!==false;const before=notes.size;
  for(const n of data.notes){if(!/^[a-f0-9]{24}$/i.test(n.id||''))continue;const u=new URL('https://www.xiaohongshu.com/explore/'+n.id);if(n.token){u.searchParams.set('xsec_token',n.token);u.searchParams.set('xsec_source','pc_collection')};notes.set(n.id,{id:n.id,title:n.title,url:u.href,status:existing.has(n.id)?'already_imported':'pending'});}
  if(!hasMore)break;stable=notes.size===before?stable+1:0;if(stable>=3)break;
  await p.locator('body').press('End');await p.mouse.wheel(0,1800);
 }
 const complete=!restriction&&!hasMore&&total!==null&&notes.size===total;
 const report={board:url.origin+url.pathname,total,found:notes.size,complete,hasMore,restriction,apiFailures,blockedHosts:[...failed],existingRecipeIds:[...existing],notes:[...notes.values()]};
 fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({total,found:notes.size,complete,restriction,apiFailures,blockedHosts:[...failed],skipped:[...notes.values()].filter(n=>n.status==='already_imported').length}));
 if(!complete)process.exitCode=2;
 }finally{await b.close()}
})().catch(e=>{console.error(e.name+': 专辑采集未完成，请检查网络及浏览器依赖。');process.exit(1)});
