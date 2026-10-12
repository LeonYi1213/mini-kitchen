// Normal browser fallback for public notes; no login or challenge bypass.
const fs = require('node:fs');
const {chromium} = require('playwright');
(async () => {
  const input = fs.readFileSync(0, 'utf8').trim();
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.CHROMIUM_PATH ? {executablePath: process.env.CHROMIUM_PATH} : process.platform === 'linux' ? {executablePath: '/usr/bin/chromium'} : {}),
    ...(process.env.HTTPS_PROXY ? {proxy: {server: process.env.HTTPS_PROXY}} : {})
  });
  try {
    const page = await browser.newPage();
    await page.goto(input, {waitUntil: 'domcontentloaded', timeout: 30000});
    try { await page.waitForFunction(() => {
      const map = window.__INITIAL_STATE__?.note?.noteDetailMap;
      return map && Object.values(map).some(v => v.note?.video?.media?.stream);
    }, null, {timeout: 15000}); } catch (error) {
      const visible = await page.locator('body').innerText().catch(() => '');
      if (visible.includes('IP存在风险') || (visible.includes('安全限制') && visible.includes('300012'))) {
        throw Error('XHS_NETWORK_RESTRICTED');
      }
      throw error;
    }
    const notes = await page.evaluate(() => JSON.parse(JSON.stringify(window.__INITIAL_STATE__.note.noteDetailMap)));
    const path = new URL(page.url()).pathname;
    const id = path.match(/\/(?:explore|discovery\/item)\/([a-f\d]+)/i)?.[1];
    if (!id || !notes[id]?.note?.video?.media?.stream) throw Error('No matching public video');
    process.stdout.write(JSON.stringify({id, note: notes[id].note}));
  } finally { await browser.close(); }
})().catch(error => { if (error.message === 'XHS_NETWORK_RESTRICTED') { console.error('XHS_NETWORK_RESTRICTED'); process.exit(1); } console.error('浏览器未取得公开视频；可能需要登录、笔记不可用或浏览器依赖缺失。'); process.exit(1); });
