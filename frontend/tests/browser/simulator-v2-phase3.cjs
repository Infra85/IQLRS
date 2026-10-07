/* Real production UI/API verification; no mocked simulation responses. */
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
    assert.equal(await page.getByRole('region', { name: 'Execution trace', exact: true }).count(), 0);
    await page.getByRole('checkbox', { name: 'Enable classical registers', exact: true }).check();
    await page.getByRole('spinbutton', { name: 'Shots', exact: true }).fill('32');
    await page.getByRole('textbox', { name: 'Random seed (optional)', exact: true }).fill('42');
    await page.getByRole('checkbox', { name: 'Debug execution', exact: true }).check();
    await page.getByRole('textbox', { name: 'Debug shots (1-based)', exact: true }).fill('1, 2');
    const place = async (type, qubit) => {
      const button = page.getByRole('button', { name: type, exact: true });
      if (await button.getAttribute('aria-pressed') !== 'true') await button.click();
      await page.getByRole('button', { name: `Place selected gate on qubit ${qubit}`, exact: true }).first().click();
    };
    const clear = () => page.getByRole('button', { name: 'Clear circuit', exact: true }).click();
    const run = async () => {
      const pending = page.waitForResponse(r => r.url().includes('/api/circuits/simulate') && r.request().method() === 'POST');
      await page.getByRole('button', { name: 'Run simulation', exact: true }).click();
      const response = await pending;
      const data = await response.json();
      assert.equal(response.status(), 200, JSON.stringify(data));
      await page.getByText('Execution complete', { exact: true }).waitFor();
      return data;
    };
    const inspector = page.getByRole('region', { name: 'Execution trace', exact: true });
    const details = inspector.getByRole('region', { name: 'Checkpoint details', exact: true });
    const next = () => inspector.getByRole('button', { name: 'Next checkpoint', exact: true }).click();
    const selectOp = n => inspector.getByRole('button', { name: new RegExp(`^Operation ${n}:`) }).click();
    const basisProbability = async (bits, probability) => {
      const row = details.getByRole('region', { name: 'Checkpoint quantum state', exact: true }).getByRole('listitem').filter({ has: page.getByText(`|${bits}⟩`, { exact: true }) });
      assert.ok((await row.innerText()).includes(`p=${probability.toFixed(3)}`));
    };
    // Example 1: actual H probabilities and post-measurement collapsed state.
    await place('H', 0); await place('MEASURE', 0);
    let data = await run();
    assert.deepEqual(data.debug.traces.map(t => t.shot), [1,2]);
    assert.equal(data.shot_results.length, 0); // dedicated tracing does not expand Phase 2 history
    assert.equal(await inspector.getByRole('button', { name:'Previous checkpoint', exact:true }).isDisabled(), true);
    await next(); await basisProbability('00', .5); await basisProbability('01', .5);
    await next();
    const sampled = data.debug.traces[0].checkpoints[2].samples[0].outcome;
    await details.getByText(`Sampled value: ${sampled}`, { exact:true }).waitFor();
    assert.ok((await details.getByRole('region', { name:'Measurement event', exact:true }).innerText()).includes('P(0) = 50.0%'));
    await basisProbability(sampled ? '01' : '00', 1);
    await details.getByRole('region', { name:'Checkpoint classical state', exact:true }).getByText(`c = 0${sampled}`, { exact:true }).waitFor();
    await inspector.getByRole('button', { name:'Previous checkpoint', exact:true }).click();
    await basisProbability('00', .5);
    await inspector.getByRole('button', { name:/^Simulation end/ }).click();
    assert.equal(await inspector.getByRole('button', { name:'Next checkpoint', exact:true }).isDisabled(), true);
    await inspector.getByRole('combobox', { name:'Debug shot', exact:true }).selectOption('2');
    await inspector.getByText('Shot 2 · checkpoint 1 of 4', { exact:true }).waitFor();
    // Example 2: both classical branches, explicit skipped operations and circuit highlight.
    await clear();
    await place('H', 0); await place('MEASURE', 0); await place('X', 1);
    await page.getByRole('combobox', { name:'Operation 3 classical condition', exact:true }).selectOption('c:0');
    await place('MEASURE', 1);
    data = await run();
    assert.deepEqual(new Set(data.debug.traces.map(t => t.checkpoints[3].executed)), new Set([true,false]));
    for (const trace of data.debug.traces) {
      await inspector.getByRole('combobox', { name:'Debug shot', exact:true }).selectOption(String(trace.shot));
      await selectOp(3);
      const evaluation = trace.checkpoints[3].condition;
      const text = await details.getByRole('region', { name:'Classical condition evaluation', exact:true }).innerText();
      assert.ok(text.includes(`Actual: ${evaluation.actual}`));
      assert.ok(text.includes(evaluation.matched ? 'TRUE · EXECUTED' : 'FALSE · SKIPPED'));
      await page.locator('[data-circuit-column="2"][data-executing="true"]').first().waitFor();
      await basisProbability(evaluation.matched ? '11' : '00', 1);
    }
    assert.equal(await inspector.getByRole('combobox', { name:'Debug shot', exact:true }).getByRole('option').count(), 2);
    if (process.env.SIMULATOR_SCREENSHOT) {
      await inspector.scrollIntoViewIfNeeded();
      await page.screenshot({ path:process.env.SIMULATOR_SCREENSHOT });
    }
    // Example 3: reset checkpoint changes quantum state but retains c0 for a condition.
    await clear();
    await place('H', 0); await place('MEASURE', 0); await place('RESET', 0); await place('X', 1);
    await page.getByRole('combobox', { name:'Operation 4 classical condition', exact:true }).selectOption('c:0');
    data = await run();
    for (const trace of data.debug.traces) {
      await inspector.getByRole('combobox', { name:'Debug shot', exact:true }).selectOption(String(trace.shot));
      await selectOp(3);
      await details.getByRole('region', { name:'Reset event', exact:true }).waitFor();
      await basisProbability('00', 1);
      const before = trace.checkpoints[2].classical.c;
      assert.equal(trace.checkpoints[3].classical.c, before);
      await details.getByRole('region', { name:'Checkpoint classical state', exact:true }).getByText(`c = ${before}`, { exact:true }).waitFor();
    }
    // Example 4: later selected shot, selected operations and optional amplitudes.
    await page.getByRole('textbox', { name:'Debug shots (1-based)', exact:true }).fill('32');
    await page.getByRole('combobox', { name:'Checkpoint mode', exact:true }).selectOption('selected');
    await page.getByRole('textbox', { name:'Operations to inspect (1-based)', exact:true }).fill('1');
    await page.getByRole('checkbox', { name:'Include checkpoint amplitudes', exact:true }).check();
    data = await run();
    assert.deepEqual(data.debug.traces.map(t => t.shot), [32]);
    assert.equal(data.debug.traces[0].checkpoints.length, 6); // all important events preserved
    assert.ok(data.debug.traces[0].checkpoints.every(cp => Array.isArray(cp.quantum.statevector)));
    await inspector.getByRole('button', { name:/^Simulation end/ }).click();
    assert.deepEqual(data.debug.traces[0].checkpoints.at(-1).quantum.statevector, data.statevector);
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true, 'mobile overflow');
    // A normal run returns no traces and hides the inspector.
    const priorCounts = data.counts;
    await page.getByRole('checkbox', { name:'Debug execution', exact:true }).uncheck();
    data = await run();
    assert.equal(data.debug, null);
    assert.deepEqual(data.counts, priorCounts);
    assert.equal(await inspector.count(), 0);
    // Out-of-range shot requests fail in the UI before contacting the API.
    await page.getByRole('checkbox', { name:'Debug execution', exact:true }).check();
    await page.getByRole('textbox', { name:'Debug shots (1-based)', exact:true }).fill('33');
    let requests = 0;
    page.on('request', r => { if (r.url().includes('/api/circuits/simulate')) requests++; });
    await page.getByRole('button', { name:'Run simulation', exact:true }).click();
    await page.getByText('Debug shots: use numbers from 1 to 32.', {exact:true}).waitFor();
    assert.equal(requests,0);
    assert.deepEqual(errors,[]);
    console.log('Phase 3 browser passed: opt-in tracing, selected shots, navigation/timeline, H/collapse, both conditions, reset memory, amplitudes, highlights, mobile and disabled mode.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode=1; });
