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
