import { chromium } from "playwright";

const BASE = "http://192.168.0.156";

(async () => {
  const browser = await chromium.launch({
    args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'],
  });

  const ctxA = await browser.newContext({ permissions: ['camera', 'microphone'] });
  const ctxB = await browser.newContext({ permissions: ['camera', 'microphone'] });
  const pageA = await ctxA.newPage();
  const pageB = await ctxB.newPage();

  pageA.on('console', (msg) => { if (msg.type() === 'error') console.log('[A error]', msg.text()); });
  pageB.on('console', (msg) => { if (msg.type() === 'error') console.log('[B error]', msg.text()); });

  const stamp = Date.now();
  for (const [page, label] of [[pageA, 'A'], [pageB, 'B']]) {
    await page.goto(`${BASE}/register`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[placeholder="Jane"]', `Tester ${label}`);
    await page.fill('input[type="email"]', `audio3${label}${stamp}@example.com`);
    await page.fill('input[type="password"]', 'TestPass123!');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2500);
    console.log(`[${label}] url after register:`, page.url());
  }

  const meetingId = await pageA.evaluate(async () => {
    const raw = localStorage.getItem('fizx-auth');
    const parsed = JSON.parse(raw);
    const token = parsed.state.accessToken;
    const res = await fetch('/api/v1/meetings/instant/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ title: 'Audio Test Call' }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error('create failed: ' + JSON.stringify(data));
    return data.id;
  });
  console.log('Meeting created:', meetingId);

  await pageA.goto(`${BASE}/call/${meetingId}`);
  await pageB.goto(`${BASE}/call/${meetingId}`);

  await pageA.waitForTimeout(8000);
  await pageB.waitForTimeout(2000);

  await pageA.screenshot({ path: '/tmp/audio_test_A_in_call.png' });
  await pageB.screenshot({ path: '/tmp/audio_test_B_in_call.png' });

  for (const [page, label] of [[pageA, 'A'], [pageB, 'B']]) {
    const info = await page.evaluate(() => {
      const audios = Array.from(document.querySelectorAll('audio')).map((a) => ({
        paused: a.paused, muted: a.muted, currentTime: a.currentTime,
        readyState: a.readyState, srcObjectExists: !!a.srcObject,
      }));
      const overlayVisible = document.body.innerText.includes('Tap to enable audio');
      return { audioCount: audios.length, audios, overlayVisible };
    });
    console.log(`[${label}] audio state:`, JSON.stringify(info, null, 2));
  }

  await pageA.waitForTimeout(3000);
  for (const [page, label] of [[pageA, 'A'], [pageB, 'B']]) {
    const info2 = await page.evaluate(() => Array.from(document.querySelectorAll('audio')).map((a) => a.currentTime));
    console.log(`[${label}] audio currentTime after extra wait:`, info2);
  }

  await browser.close();
})();
