/* Production browser + real API checks. Uses the same setup as simulator-v2.cjs. */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome-stable', headless: true });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  try {
    await page.goto((process.env.BUILDER_URL || 'http://127.0.0.1:13002') + '/builder');
    await page.getByRole('button', { name: 'Continue as guest', exact: true }).click();
    await page.getByRole('checkbox', { name: 'Enable classical registers', exact: true }).check();
    await page.getByRole('checkbox', { name: 'Include shot history', exact: true }).check();
    await page.getByRole('spinbutton', { name: 'Shot records', exact: true }).fill('128');
    await page.getByRole('spinbutton', { name: 'Shots', exact: true }).fill('128');
    await page.getByRole('textbox', { name: 'Random seed (optional)', exact: true }).fill('42');
    const place = async (type, qubit, control) => {
      const button = page.getByRole('button', { name: type, exact: true });
      if (await button.getAttribute('aria-pressed') !== 'true') await button.click();
      const wire = q => page.getByRole('button', { name: `Place selected gate on qubit ${q}`, exact: true }).first().click();
      if (control !== undefined) await wire(control);
      await wire(qubit);
    };
    const clear = () => page.getByRole('button', { name: 'Clear circuit', exact: true }).click();
    const setCondition = op => page.getByRole('combobox', { name: `Operation ${op} classical condition`, exact: true }).selectOption('c:0');
    const destination = (op, q, ref) => page.getByRole('combobox', { name: `Operation ${op} q${q} destination`, exact: true }).selectOption(ref);
    const run = async () => {
      const pending = page.waitForResponse(r => r.url().includes('/api/circuits/simulate') && r.request().method() === 'POST');
      await page.getByRole('button', { name: 'Run simulation', exact: true }).click();
      const response = await pending;
      const data = await response.json();
      assert.equal(response.status(), 200, JSON.stringify(data));
      await page.getByText('Execution complete', { exact: true }).waitFor();
      assert.equal(data.shot_results.length, 128);
      const counts = {};
      for (const shot of data.shot_results) counts[shot.outcome] = (counts[shot.outcome] || 0) + 1;
      assert.deepEqual(counts, data.counts);
      assert.equal(data.metadata.counts_kind, 'classical');
      return { data, payload: response.request().postDataJSON() };
    };
    // Bell measurement into two explicit classical bits.
    await place('H', 0); await place('CNOT', 1, 0); await place('MEASURE', 0); await place('MEASURE', 1);
    let { data, payload } = await run();
    assert.deepEqual(Object.keys(data.counts).sort(), ['00', '11']);
    assert.ok(data.counts['00'] > 40 && data.counts['00'] < 88);
    assert.deepEqual(payload.classical_registers, [{ name: 'c', size: 2 }]);
    assert.deepEqual(payload.gates[2].destinations, [{ register: 'c', bit: 0 }]);
    await page.getByRole('heading', { name: 'Classical register result', exact: true }).waitFor();
    await page.getByText('Per-shot results (128 recorded)', { exact: true }).click();
    await page.getByText('Shot 1:', { exact: false }).first().waitFor();
    // Classical feed-forward and repeatable seeded history.
    await clear();
    await place('H', 0); await place('MEASURE', 0); await place('X', 1); await setCondition(3); await place('MEASURE', 1);
    ({ data, payload } = await run());
    assert.deepEqual(Object.keys(data.counts).sort(), ['00', '11']);
    assert.deepEqual(payload.gates[2].condition, { register: 'c', bit: 0, operator: 'eq', value: 1 });
    assert.deepEqual((await run()).data.shot_results, data.shot_results);
    // Mid-circuit collapse: every shot's second measurement is the opposite.
    await clear();
    await place('H', 0); await place('MEASURE', 0); await place('X', 0); await place('MEASURE', 0); await destination(4, 0, 'c:1');
    ({ data } = await run());
    assert.deepEqual(Object.keys(data.counts).sort(), ['01', '10']);
    for (const shot of data.shot_results) assert.notEqual(shot.measurements[0].bits, shot.measurements[1].bits);
    // Reset leaves c0 intact, which subsequently controls q1.
    await clear();
    await place('H', 0); await place('MEASURE', 0); await place('RESET', 0); await place('X', 1); await setCondition(4);
    ({ data } = await run());
    assert.deepEqual(Object.keys(data.counts).sort(), ['0', '1']);
    assert.deepEqual(data.statevector[1], [0, 0]); assert.deepEqual(data.statevector[3], [0, 0]);
    assert.equal(data.statevector[2 * Number(data.last_classical.c[1])][0], 1);
    // Named second register and whole-register equality.
    await clear();
    await page.getByRole('button', { name: 'Add classical register', exact: true }).click();
    await page.getByRole('textbox', { name: 'Register 2 name', exact: true }).fill('flag');
    await page.getByRole('textbox', { name: 'Register 2 name', exact: true }).press('Tab');
    await place('X', 0); await place('MEASURE', 0); await destination(2, 0, 'flag:0'); await place('X', 1);
    await page.getByRole('combobox', { name: 'Operation 3 classical condition', exact: true }).selectOption('flag:*');
    await page.getByRole('spinbutton', { name: 'Operation 3 condition value', exact: true }).fill('1');
    await place('MEASURE', 1);
    ({ data } = await run());
    assert.deepEqual(data.counts, { '11': 128 });
    assert.deepEqual(data.last_classical, { c: '10', flag: '1' });
    // Renaming preserves existing measurement and condition references.
    await page.getByRole('textbox', { name: 'Register 2 name', exact: true }).fill('status');
    await page.getByRole('textbox', { name: 'Register 2 name', exact: true }).press('Tab');
    ({ data, payload } = await run());
    assert.deepEqual(data.last_classical, { c: '10', status: '1' });
    assert.equal(payload.gates[1].destinations[0].register, 'status');
    assert.equal(payload.gates[2].condition.register, 'status');
    if (process.env.SIMULATOR_SCREENSHOT) {
      await page.getByRole('heading', { name: 'Classical register result', exact: true }).scrollIntoViewIfNeeded();
      await page.screenshot({ path: process.env.SIMULATOR_SCREENSHOT });
    }
    // Reject invalid comparisons before any API request.
    await page.getByRole('spinbutton', { name: 'Operation 3 condition value', exact: true }).fill('2');
    let requests = 0;
    page.on('request', request => { if (request.url().includes('/api/circuits/simulate')) requests++; });
    await page.getByRole('button', { name: 'Run simulation', exact: true }).click();
    await page.getByText('Operation 3: condition value is outside the selected bit/register range.', { exact: true }).waitFor();
    assert.equal(requests, 0);
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true, 'mobile horizontal overflow');
    assert.deepEqual(errors, []);
    console.log('Phase 2 browser passed: Bell, feed-forward, sequential collapse, reset memory, seeded shots, named registers, register equality, validation, bounded history and mobile layout.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
