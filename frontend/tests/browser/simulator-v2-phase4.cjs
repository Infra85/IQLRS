/* Production UI + real local API/database/auth; test server fakes ONLY the QPU boundary. */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome-stable', headless: true });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  const base = process.env.BUILDER_URL || 'http://127.0.0.1:13002';
  try {
    if (process.env.HARDWARE_BROWSER_DISABLED === 'true') {
      await page.goto(base + '/builder');
      await page.getByRole('button', { name: 'Continue as guest', exact: true }).click();
      const response = await page.request.get(base + '/api/hardware/providers');
      assert.equal((await response.json()).enabled, false);
      assert.equal(await page.getByRole('combobox', { name: 'Execution Target', exact: true }).count(), 0);
      await page.getByRole('button', { name: 'Run simulation', exact: true }).click();
      await page.getByText('Execution complete', { exact: true }).waitFor();
      console.log('Phase 4 disabled browser passed: no hardware controls, local simulation works.');
      return;
    }
    const [token, other] = JSON.parse(fs.readFileSync('/tmp/iqlrs-hardware-browser-tokens.json'));
    await page.addInitScript(t => localStorage.setItem('access_token', t), token);
    await page.goto(base + '/builder');
    const selector = page.getByRole('combobox', { name: 'Execution Target', exact: true });
    await selector.selectOption('ibm');
    await page.getByRole('combobox', { name: 'Hardware device', exact: true }).selectOption('test-qpu');
    await page.getByRole('spinbutton', { name: 'Shots', exact: true }).fill('16');
    await page.getByRole('button', { name: 'X', exact: true }).click();
    await page.getByRole('button', { name: 'Place selected gate on qubit 0', exact: true }).first().click();
    const submissions = [];
    page.on('request', r => { if (r.method() === 'POST' && new URL(r.url()).pathname === '/api/hardware/jobs') submissions.push(r); });
    await page.getByRole('button', { name: 'Validate for hardware', exact: true }).click();
    await page.getByText('Hardware validation PASSED', { exact: true }).waitFor();
    assert.equal(submissions.length, 0);
    await page.getByRole('button', { name: 'Review QPU submission', exact: true }).click();
    const dialog = page.getByRole('dialog', { name: 'Confirm real QPU execution' });
    await dialog.waitFor();
    assert.equal(submissions.length, 0);
    const pending = page.waitForResponse(r => new URL(r.url()).pathname === '/api/hardware/jobs' && r.request().method() === 'POST');
    await dialog.getByRole('button', { name: 'Submit to QPU', exact: true }).click();
    const response = await pending;
    assert.equal(response.status(), 202);
    const job = await response.json();
    assert.equal(job.status, 'QUEUED');
    const request = submissions[0];
    const duplicate = await page.request.post(base + '/api/hardware/jobs', { headers: { Authorization: `Bearer ${token}`, 'Idempotency-Key': request.headers()['idempotency-key'] }, data: request.postDataJSON() });
    assert.equal((await duplicate.json()).id, job.id);
    for (const suffix of ['', '/result']) {
      const denied = await page.request.get(base + '/api/hardware/jobs/' + job.id + suffix, { headers: { Authorization: `Bearer ${other}` } });
      assert.equal(denied.status(), 404);
    }
    await page.getByText('Hardware Job · RUNNING', { exact: true }).waitFor({ timeout: 20000 });
    await page.getByText('REAL HARDWARE RESULT', { exact: true }).waitFor({ timeout: 30000 });
    assert.equal(await page.getByRole('region', { name: 'Execution trace', exact: true }).count(), 0);
    await page.getByRole('button', { name: 'Compare with local simulation', exact: true }).click();
    await page.getByRole('columnheader', { name: 'Local simulation', exact: true }).waitFor();
    await page.reload();
    await page.getByText('REAL HARDWARE RESULT', { exact: true }).waitFor();
    await selector.selectOption('ibm');
    await page.getByRole('combobox', { name: 'Hardware device', exact: true }).selectOption('failure-qpu');
    await page.getByRole('spinbutton', { name: 'Shots', exact: true }).fill('16');
    await page.getByRole('button', { name: 'Validate for hardware', exact: true }).click();
    await page.getByText('Hardware validation PASSED', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Review QPU submission', exact: true }).click();
    await dialog.getByRole('button', { name: 'Submit to QPU', exact: true }).click();
    await page.getByText('Hardware Job · FAILED', { exact: true }).waitFor({ timeout: 20000 });
    await page.getByText('Hardware provider reported job failure', { exact: true }).waitFor();
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2), false);
    assert.deepEqual(errors, []);
    console.log('Phase 4 browser passed: discovery, validation without submit, confirmation, queued/running/completed, results, comparison, refresh, failure, ownership, idempotency, mobile. QPU boundary is a test fixture.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });
