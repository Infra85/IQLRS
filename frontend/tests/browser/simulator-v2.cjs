/* Run against the production frontend and a real local API; see docs/SIMULATOR_V2.md. */
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
    const wire = q => page.getByRole('button', { name: `Place selected gate on qubit ${q}`, exact: true }).first().click();
    const select = type => page.getByRole('button', { name: type, exact: true }).click();
    const clear = () => page.getByRole('button', { name: 'Clear circuit', exact: true }).click();
    const place = async (type, q, control, theta) => {
      const button = page.getByRole('button', { name: type, exact: true });
      if (await button.getAttribute('aria-pressed') !== 'true') await select(type);
      if (theta !== undefined) await page.getByRole('textbox', { name: 'Theta (radians)', exact: true }).fill(theta);
      if (control !== undefined) await wire(control);
      await wire(q);
    };
    const run = async () => {
      const pending = page.waitForResponse(r => r.url().includes('/api/circuits/simulate') && r.request().method() === 'POST');
      await page.getByRole('button', { name: 'Run simulation', exact: true }).click();
      const response = await pending;
      const result = await response.json();
      assert.equal(response.status(), 200, JSON.stringify(result));
      await page.getByText('Execution complete', { exact: true }).waitFor();
      return { payload: response.request().postDataJSON(), result };
    };
    await page.getByRole('spinbutton', { name: 'Shots', exact: true }).fill('128');
    const types = ['I','H','X','Y','Z','S','T','RX','RY','RZ','CNOT','CY','CZ','CH','CRX','CRY','CRZ','SWAP','MEASURE','MEASURE_ALL','RESET'];
    for (const type of types) {
      await clear();
      const linked = ['CNOT','CY','CZ','CH','CRX','CRY','CRZ','SWAP'].includes(type);
      const rotation = /^(C)?R[XYZ]$/.test(type);
      await place(type, 1, linked ? 0 : undefined, rotation ? '-pi/2' : undefined);
      const { payload, result } = await run();
      assert.equal(payload.gates.length, 1);
      const gate = payload.gates[0];
      assert.equal(gate.type, type);
      if (linked) assert.deepEqual([gate.control, gate.target], [0,1]);
      else if (type === 'MEASURE_ALL') assert.equal(gate.qubit, undefined);
      else assert.equal(gate.qubit, 1);
      if (rotation) assert.equal(gate.params.theta, -Math.PI/2);
      assert.equal(Object.values(result.counts).reduce((a,b) => a+b, 0), 128);
    }
    await clear();
    await place('RX', 0, undefined, 'Infinity');
    await page.getByText('Theta must be finite radians, for example 1.5708, pi/2, or -pi.', { exact: true }).waitFor();
    assert.equal(await page.getByRole('button', { name: 'Remove RX from qubit 0', exact: true }).count(), 0);
    await place('RX', 0, undefined, '0');
    const editor = page.getByRole('textbox', { name: 'Operation 1 theta', exact: true });
    await editor.fill('pi');
    await editor.press('Tab');
    let execution = await run();
    assert.equal(execution.payload.gates[0].params.theta, Math.PI);
    assert.deepEqual(execution.result.counts, { '01': 128 });
    await clear();
    await place('H', 0);
    await place('CNOT', 1, 0);
    await place('MEASURE_ALL', 0);
    await place('RESET', 0);
    execution = await run();
    assert.deepEqual(Object.keys(execution.result.counts).sort(), ['00','10']);
    assert.deepEqual(Object.keys(execution.result.measurement_counts['2']).sort(), ['00','11']);
    assert.equal(execution.result.metadata.statevector_scope, 'last_shot');
    await page.getByRole('heading', { name: 'Explicit measurements', exact: true }).waitFor();
    await page.getByText('Conditional state from the last shot, after measurement/reset. Counts aggregate all shots.', { exact: true }).waitFor();
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true, 'mobile horizontal overflow');
    assert.deepEqual(errors, []);
    console.log('Browser passed: all 21 operations, serialization, angle validation/editing, Bell measurement/reset, result labels, mobile layout.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
