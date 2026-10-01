const ts = require('typescript');
const fs = require('node:fs');
require.extensions['.ts'] = (module, filename) => module._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, filename);
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { withDefaultDestinations, validateClassicalCircuit, classicalBits, conditionLabel, setMeasurementDestination } = require('../src/components/circuit-builder/classical-circuit.ts');
const { dropGate } = require('../src/components/circuit-builder/edit-circuit.ts');
const { simulateCircuit } = require('../src/lib/api.ts');
const registers = [{ name: 'c', size: 2 }];
const ref = bit => ({ register: 'c', bit });

test('legacy operations remain unchanged; explicit measurements get positional defaults', () => {
  const legacy = { type: 'MEASURE', qubit: 0 };
  assert.equal(withDefaultDestinations(legacy, undefined, 2), legacy);
  assert.deepEqual(withDefaultDestinations(legacy, registers, 2), { ...legacy, destinations: [ref(0)] });
  assert.deepEqual(withDefaultDestinations({ type: 'MEASURE_ALL' }, registers, 2), { type: 'MEASURE_ALL', destinations: [ref(0), ref(1)] });
  const custom = { ...legacy, destinations: [ref(1)] };
  assert.equal(withDefaultDestinations(custom, registers, 2), custom);
  assert.deepEqual(classicalBits([...registers, { name: 'flag', size: 1 }]), [ref(0), ref(1), { register: 'flag', bit: 0 }]);
});

test('movement preserves classical destinations and conditions independently of quantum controls', () => {
  const condition = { register: 'c', bit: 0, operator: 'eq', value: 1 };
  const gate = { type: 'CNOT', control: 0, target: 1, condition };
  assert.deepEqual(dropGate([gate], { type: 'CNOT', index: 0, anchorQubit: 0 }, { qubit: 1, column: 0 }, 3), [{ ...gate, control: 1, target: 2 }]);
  const m = { type: 'MEASURE', qubit: 0, destinations: [ref(1)] };
  assert.deepEqual(dropGate([m], { type: 'MEASURE', index: 0 }, { qubit: 1, column: 0 }, 2), [{ ...m, qubit: 1 }]);
  assert.equal(conditionLabel(gate), 'IF c[0] == 1');
  assert.equal(conditionLabel({ ...gate, condition: { ...condition, bit: null, value: 3 } }), 'IF c == 3');
});

test('classical validation rejects invalid memory, destinations and conditions', () => {
  for (const rs of [[], [{ name: 'bad name', size: 1 }], [{ name: 'c', size: 0 }], [...registers, ...registers], [{ name: 'c', size: 33 }]]) assert.throws(() => validateClassicalCircuit([], rs, 2));
  for (const gate of [
    { type: 'MEASURE', qubit: 0 },
    { type: 'MEASURE', qubit: 0, destinations: [ref(2)] },
    { type: 'MEASURE_ALL', destinations: [ref(0), ref(0)] },
    { type: 'MEASURE_ALL', destinations: new Array(2) },
    { type: 'X', qubit: 0, condition: { register: 'missing', bit: 0, operator: 'eq', value: 1 } },
    { type: 'X', qubit: 0, condition: { register: 'c', bit: 0, operator: 'eq', value: 2 } },
    { type: 'X', qubit: 0, condition: { register: 'c', operator: 'eq', value: 4 } },
  ]) assert.throws(() => validateClassicalCircuit([gate], registers, 2));
  validateClassicalCircuit([{ type: 'X', qubit: 0, condition: { register: 'c', operator: 'eq', value: 3 } }], registers, 2);
});

test('simulation serializes named registers, destinations, conditions, seed and shot limit', async t => {
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, '/api/circuits/simulate');
    assert.deepEqual(JSON.parse(options.body), payload);
    return Response.json({ counts: { '11': 1 }, last_classical: { c: '11' }, shot_results: [] });
  });
  const payload = { num_qubits: 2, shots: 1, seed: 7, shot_record_limit: 1, classical_registers: registers,
    gates: [{ type: 'MEASURE', qubit: 0, destinations: [ref(0)] }, { type: 'X', qubit: 1, condition: { register: 'c', bit: 0, operator: 'eq', value: 1 } }] };
  assert.deepEqual((await simulateCircuit(payload)).last_classical, { c: '11' });
});


test('editing a later measurement destination cannot leave sparse invalid memory', () => {
  const gate = setMeasurementDestination({ type: 'MEASURE_ALL', destinations: [] }, 2, ref(1), 3);
  assert.deepEqual(gate.destinations, [{ register: '', bit: -1 }, { register: '', bit: -1 }, ref(1)]);
  assert.throws(() => validateClassicalCircuit([gate], registers, 3));
});
