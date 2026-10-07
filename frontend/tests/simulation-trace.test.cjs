const ts = require('typescript');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const resolve = Module._resolveFilename;
Module._resolveFilename = function(name, ...args) {
  return resolve.call(this, name.startsWith('@/') ? path.join(__dirname, '../src', name.slice(2)) : name, ...args);
};
for (const ext of ['.ts', '.tsx']) require.extensions[ext] = (module, filename) => module._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX } }).outputText, filename);
const { test } = require('node:test');
const assert = require('node:assert/strict');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const { makeDebugRequest, initialDebugSettings, stepCheckpoint, operationLabel } = require('../src/lib/simulation-trace.ts');
const { DebugControls } = require('../src/components/circuit-builder/DebugControls.tsx');
const { ExecutionTrace } = require('../src/components/circuit-builder/ExecutionTrace.tsx');
const { QuantumStateTable } = require('../src/components/circuit-builder/QuantumStateTable.tsx');
const { simulateCircuit } = require('../src/lib/api.ts');
const render = (Component, props) => renderToStaticMarkup(React.createElement(Component, props));
const condition = { register: 'c', bit: 0, operator: 'eq', value: 1 };
const operation = { type: 'X', targets: [1], controls: [], params: {}, condition, destinations: null };
const cp = { kind: 'condition', operation_index: 0, executed: false, quantum: { probabilities: [.5,.5,0,0], statevector: null }, classical: { c: '00' }, condition: { actual: 0, expected: 1, matched: false }, samples: [], outcome: null };
const debug = { version: 1, num_qubits: 2, shot_numbering: 'one_based', operation_indexing: 'zero_based', operations: { '0': operation }, traces: [{ shot: 1, checkpoints: [cp] }, { shot: 5, checkpoints: [cp] }] };

test('debug opt-in, shot and operation numbering and request serialization', async t => {
  assert.equal(makeDebugRequest(initialDebugSettings, 10, [], 2), undefined);
  const settings = { ...initialDebugSettings, enabled: true, shots: '1, 5', mode: 'selected', operations: '1, 3' };
  const request = makeDebugRequest(settings, 10, [{type:'H'}, {type:'X'}, {type:'Z'}], 2);
  assert.deepEqual(request, { enabled: true, shot_numbers: [1,5], checkpoint_mode: 'selected', operation_indices: [0,2], include_statevector: false });
  t.mock.method(globalThis, 'fetch', async (_, options) => {
    assert.deepEqual(JSON.parse(options.body).debug, request);
    return Response.json({ debug });
  });
  assert.deepEqual((await simulateCircuit({ num_qubits: 2, gates: [], debug: request })).debug, debug);
});

test('debug limits, duplicate and out-of-range selection validation', () => {
  for (const shots of ['', '0', '-1', '1,1', '2.3', '11', 'NaN', Array.from({length:17},(_,i)=>i+1).join(',')]) {
    assert.throws(() => makeDebugRequest({ ...initialDebugSettings, enabled:true, shots },10,[],2));
  }
  assert.throws(() => makeDebugRequest({ ...initialDebugSettings, enabled:true }, 1, Array(255).fill({type:'I'}), 2));
  assert.throws(() => makeDebugRequest({ ...initialDebugSettings, enabled:true, shots:'1,2', amplitudes:true }, 2, Array(31).fill({type:'I'}), 2));
  assert.throws(() => makeDebugRequest({ ...initialDebugSettings, enabled:true, mode:'selected', operations:'1' }, 1, Array(255).fill({type:'X',condition}), 2));
});

test('controls hide debug-specific settings when disabled and explain bounds when enabled', () => {
  const hidden = render(DebugControls, { settings: initialDebugSettings, onChange() {} });
  assert.doesNotMatch(hidden, /Debug shots \(1-based\)/);
  const visible = render(DebugControls, { settings: { ...initialDebugSettings, enabled:true, mode:'selected' }, onChange() {} });
  assert.match(visible, /Debug shots \(1-based\)/);
  assert.match(visible, /Operations to inspect \(1-based\)/);
  assert.match(visible, /Include checkpoint amplitudes/);
});

test('navigation clamps to boundaries and timeline exposes skipped operations and shot choices', () => {
  assert.equal(stepCheckpoint(0,-1,5),0);
  assert.equal(stepCheckpoint(4,1,5),4);
  assert.equal(stepCheckpoint(2,1,5),3);
  const html = render(ExecutionTrace, { debug, onOperation() {} });
  assert.match(html, /Shot 5/);
  assert.match(html, /aria-current="step"/);
  assert.match(html, /Condition FALSE/);
  assert.match(html, /SKIPPED/);
  assert.match(html, /Actual: 0/);
  assert.match(html, /Expected: 1/);
  assert.match(html, /c = 00/);
  assert.match(html, /p=0.500/);
  assert.match(html, /Previous checkpoint/);
});

test('measurement and reset render actual probabilities, outcomes and classical state', () => {
  for (const kind of ['measurement','reset']) {
    const sample = { qubit:0, destination: kind === 'reset' ? null : {register:'c',bit:0}, outcome:1, probabilities_before:[.5,.5] };
    const checkpoint = { ...cp, kind, executed:true, condition:null, samples:[sample], classical:{c:'01'}, quantum:{probabilities:[0,1,0,0],statevector:null} };
    const html = render(ExecutionTrace, { debug:{ ...debug, traces:[{shot:1,checkpoints:[checkpoint]}] }, onOperation() {} });
    assert.match(html,/Sampled value: 1/);
    assert.match(html,/P\(0\) = 50.0%/);
    assert.match(html,/P\(1\) = 50.0%/);
    assert.match(html,/p=1.000/);
    assert.match(html,/c = 01/);
    if (kind === 'reset') assert.match(html,/classical memory unchanged/);
    else assert.match(html,/q0 → c\[0\]/);
  }
});

test('quantum controls and classical conditions have separate labels', () => {
  assert.match(operationLabel({...operation, type:'CRX', controls:[0], params:{theta:.5}}), /quantum control q0.*IF c\[0\] == 1/);
});

test('quantum table bounds rendered rows for a ten-qubit checkpoint', () => {
  const html = render(QuantumStateTable, { probabilities:Array(1024).fill(1/1024), numQubits:10 });
  assert.equal((html.match(/<li /g)||[]).length,32);
  assert.match(html,/Basis page 1 of 32/);
  assert.match(html,/Next basis page/);
});
