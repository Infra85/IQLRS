const ts = require("typescript");
const fs = require("node:fs");
require.extensions[".ts"] = (module, filename) =>
  module._compile(
    ts.transpileModule(fs.readFileSync(filename, "utf8"), {
      compilerOptions: { module: ts.ModuleKind.CommonJS },
    }).outputText,
    filename,
  );
const { test } = require("node:test");
const assert = require("node:assert/strict");
const {
  dropGate,
} = require("../src/components/circuit-builder/edit-circuit.ts");
test("palette insertion preserves operation order and input", () => {
  const gates = [{ type: "H", qubit: 0 }];
  assert.deepEqual(dropGate(gates, { type: "X" }, { qubit: 1, column: 0 }, 2), [
    { type: "X", qubit: 1 },
    ...gates,
  ]);
  assert.equal(gates.length, 1);
});
test("move between wires and reorder without duplicating gates", () => {
  const gates = [
    { type: "H", qubit: 0 },
    { type: "X", qubit: 1 },
  ];
  assert.deepEqual(
    dropGate(gates, { type: "H", index: 0 }, { qubit: 1, column: 2 }, 2),
    [gates[1], { type: "H", qubit: 1 }],
  );
});
test("CNOT movement preserves linked endpoints and rejects out of bounds", () => {
  const gates = [{ type: "CNOT", control: 0, target: 1 }];
  assert.deepEqual(
    dropGate(
      gates,
      { type: "CNOT", index: 0, anchorQubit: 0 },
      { qubit: 1, column: 0 },
      3,
    ),
    [{ type: "CNOT", control: 1, target: 2 }],
  );
  assert.equal(
    dropGate(
      gates,
      { type: "CNOT", index: 0, anchorQubit: 0 },
      { qubit: 1, column: 0 },
      2,
    ),
    null,
  );
  assert.equal(
    dropGate(gates, { type: "H" }, { qubit: -1, column: 0 }, 2),
    null,
  );
  assert.equal(
    dropGate(gates, { type: "CNOT" }, { qubit: 0, column: 0 }, 2),
    null,
  );
});

const { PALETTE, isLinked, isRotation, parseAngle, makeGate, validateCircuit } = require('../src/components/circuit-builder/edit-circuit.ts');
test('angle input supports radians and common pi expressions without evaluation', () => {
  for (const [input, value] of [['pi/2', Math.PI/2], ['-π/2', -Math.PI/2], ['3*pi/4', 3*Math.PI/4], ['0.731', .731], ['0', 0], ['1e-3', .001]]) assert.equal(parseAngle(input), value);
  for (const input of ['', 'NaN', 'Infinity', 'pi/0', 'alert(1)', 'pi + 1']) assert.throws(() => parseAngle(input));
});
test('every palette operation serializes numeric parameters and correct endpoints', () => {
  for (const type of PALETTE) {
    const gate = makeGate(type, 1, isLinked(type) ? 0 : undefined, Math.PI/2);
    validateCircuit([gate], 2);
    const json = JSON.parse(JSON.stringify(gate));
    if (isRotation(type)) assert.equal(json.params.theta, Math.PI/2);
    if (isLinked(type)) assert.deepEqual([json.control, json.target], [0, 1]);
    else if (type === 'MEASURE_ALL') assert.deepEqual(json, { type });
    else assert.equal(json.qubit, 1);
  }
});
test('moving linked V2 operations preserves parameters and endpoints', () => {
  for (const type of PALETTE.filter(isLinked)) {
    const gate = makeGate(type, 1, 0, .75);
    const moved = dropGate([gate], { type, index: 0, anchorQubit: 0 }, { qubit: 1, column: 0 }, 3);
    assert.deepEqual(moved, [{ ...gate, control: 1, target: 2 }]);
  }
  assert.deepEqual(dropGate([{ type: 'MEASURE_ALL' }], { type: 'MEASURE_ALL', index: 0 }, { qubit: 1, column: 0 }, 2), [{ type: 'MEASURE_ALL' }]);
  assert.deepEqual(dropGate([], { type: 'RX', theta: .3 }, { qubit: 0, column: 0 }, 1), [{ type: 'RX', qubit: 0, params: { theta: .3 } }]);
});
test('invalid builder operations fail before serialization', () => {
  for (const gate of [{type:'RX',qubit:0}, {type:'RY',qubit:0,params:{theta:Infinity}}, {type:'CZ',control:0,target:0}, {type:'X',qubit:2}, {type:'X'}, {type:'NOPE',qubit:0}]) assert.throws(() => validateCircuit([gate], 2));
});
