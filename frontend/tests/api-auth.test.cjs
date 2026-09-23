const ts = require("typescript");
const fs = require("node:fs");
require.extensions[".ts"] = (module, filename) =>
  module._compile(ts.transpileModule(fs.readFileSync(filename, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS },
  }).outputText, filename);
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { simulateCircuit } = require("../src/lib/api.ts");
const circuit = { gates: [], num_qubits: 1, shots: 64 };

function browser(t, token) {
  const storage = new Map(token ? [["access_token", token]] : []);
  t.mock.method(globalThis, "fetch");
  const oldWindow = globalThis.window;
  const oldStorage = globalThis.localStorage;
  globalThis.window = {};
  globalThis.localStorage = {
    getItem: (key) => storage.get(key) ?? null,
    removeItem: (key) => storage.delete(key),
  };
  t.after(() => {
    if (oldWindow === undefined) delete globalThis.window;
    else globalThis.window = oldWindow;
    if (oldStorage === undefined) delete globalThis.localStorage;
    else globalThis.localStorage = oldStorage;
  });
  return storage;
}

test("simulation sends the stored bearer token and preserves a valid session", async (t) => {
  const storage = browser(t, "valid-token");
  fetch.mock.mockImplementation(async (url, options) => {
    assert.ok(url.endsWith("/api/circuits/simulate"));
    assert.equal(new Headers(options.headers).get("Authorization"), "Bearer valid-token");
    assert.equal(options.method, "POST");
    assert.deepEqual(JSON.parse(options.body), circuit);
    return Response.json({ simulation_id: "saved", counts: { "0": 64 } });
  });
  assert.equal((await simulateCircuit(circuit)).simulation_id, "saved");
  assert.equal(storage.get("access_token"), "valid-token");
});

test("rejected token is cleared without silently retrying a simulation as a guest", async (t) => {
  const storage = browser(t, "stale-token");
  fetch.mock.mockImplementation(async () => Response.json(
    { detail: "Could not validate credentials" }, { status: 401 },
  ));
  await assert.rejects(simulateCircuit(circuit), /Please sign in again/);
  assert.equal(storage.has("access_token"), false);
  assert.equal(fetch.mock.callCount(), 1);
  storage.set("access_token", "new-login-token");
  fetch.mock.mockImplementation(async (url, options) => {
    assert.equal(new Headers(options.headers).get("Authorization"), "Bearer new-login-token");
    return Response.json({ simulation_id: "saved" });
  });
  assert.equal((await simulateCircuit(circuit)).simulation_id, "saved");
});

test("a late 401 does not clear a newer login", async (t) => {
  const storage = browser(t, "old-token");
  fetch.mock.mockImplementation(async () => {
    storage.set("access_token", "new-token");
    return Response.json({ detail: "Could not validate credentials" }, { status: 401 });
  });
  await assert.rejects(simulateCircuit(circuit));
  assert.equal(storage.get("access_token"), "new-token");
});

test("guest simulation omits authorization; non-auth failures preserve the session", async (t) => {
  const storage = browser(t);
  fetch.mock.mockImplementation(async (url, options) => {
    assert.equal(new Headers(options.headers).get("Authorization"), null);
    return Response.json({ simulation_id: null });
  });
  assert.equal((await simulateCircuit(circuit)).simulation_id, null);
  storage.set("access_token", "valid-token");
  fetch.mock.mockImplementation(async () => Response.json({ detail: "Save failed" }, { status: 503 }));
  await assert.rejects(simulateCircuit(circuit), /Save failed/);
  assert.equal(storage.get("access_token"), "valid-token");
});
