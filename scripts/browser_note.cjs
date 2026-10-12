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
    await page.waitForFunction(() => {
      const map = window.__INITIAL_STATE__?.note?.noteDetailMap;
      return map && Object.values(map).some(v => v.note?.video?.media?.stream);
    }, null, {timeout: 15000});
    const notes = await page.evaluate(() => JSON.parse(JSON.stringify(window.__INITIAL_STATE__.note.noteDetailMap)));
    const path = new URL(page.url()).pathname;
    const id = path.match(/\/(?:explore|discovery\/item)\/([a-f\d]+)/i)?.[1];
    if (!id || !notes[id]?.note?.video?.media?.stream) throw Error('No matching public video');
    process.stdout.write(JSON.stringify({id, note: notes[id].note}));
  } finally { await browser.close(); }
})().catch(() => { console.error('浏览器未取得公开视频；可能需要登录、笔记不可用或浏览器依赖缺失。'); process.exit(1); });
