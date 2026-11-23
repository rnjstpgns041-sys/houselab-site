// 실제 사이트(psb-7.com)를 휴대폰 크기로 찍어 shots/ 에 저장합니다.
const { chromium, devices } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ ...devices['Galaxy S9+'], colorScheme: 'light', reducedMotion: 'reduce' });
  const p = await ctx.newPage();
  const url = 'https://psb-7.com/?v=' + Date.now();
  await p.goto(url, { waitUntil: 'networkidle' }); await p.waitForTimeout(1500);
  const ba = await p.$('#beforeafter');
  await ba.scrollIntoViewIfNeeded(); await p.waitForTimeout(800);
  await p.evaluate(() => { const d = document.querySelector('.dock'); if (d) d.style.display = 'none'; });
  await ba.screenshot({ path: 'shots/beforeafter.png' });
  const info = await p.evaluate(() => [...document.querySelectorAll('#bapGrid .bap')].slice(0, 4).map(a => a.querySelector('b').textContent + ' | ' + [...a.querySelectorAll('img')].map(i => i.naturalWidth).join(',')));
  console.log(url); console.log(info.join('\n'));
  require('fs').writeFileSync('shots/info.txt', url + '\n' + info.join('\n'));
  await b.close();
})();
