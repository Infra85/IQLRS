// Use the project's installed TypeScript compiler; no test-only application dependency.
const ts = require("typescript");
const fs = require("node:fs");
require.extensions[".ts"] = (module, filename) =>
  module._compile(
    ts.transpileModule(fs.readFileSync(filename, "utf8"), {
      compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2020,
      },
    }).outputText,
    filename,
  );
const { test } = require("node:test");
const assert = require("node:assert/strict");
const {
  normalizeSpeech,
  chunkSpeech,
  prepareNarration,
} = require("../src/lib/narration/text.ts");
const { moduleNarration } = require("../src/lib/narration/content.ts");
const { modules } = require("../src/app/learn/modules.ts");
const { NarrationController } = require("../src/lib/narration/controller.ts");
const tick = () => new Promise((resolve) => setTimeout(resolve, 0));
const segment = (text = "A quantum state.") => [
  { id: "intro", title: "Introduction", text, targetId: "intro" },
];
class Audio {
  constructor() {
    this.currentTime = 0;
    this.duration = 8;
    this.paused = true;
    this.ended = false;
    this.rate = 1;
  }
  set src(value) {
    this._src = value;
    this.onloadedmetadata?.();
  }
  async play() {
    this.paused = false;
    this.onplaying?.();
  }
  pause() {
    this.paused = true;
    this.onpause?.();
  }
  removeAttribute() {
    this._src = "";
  }
  load() {}
  end() {
    this.ended = true;
    this.onended?.();
  }
}

test("quantum states, bra-ket products, probabilities and technical names", () => {
  const output = normalizeSpeech(
    "**Qubit**: |ψ⟩ = α|0⟩ + β|1⟩. |α|² + |β|² = 1. CNOT, Pauli-X, Bloch sphere, Hadamard. |⟨ϕᵢ|ψ⟩|². |101⟩ ⊗ |0⟩.",
  );
  for (const word of [
    "ket psi",
    "ket 0",
    "ket 1",
    "squared magnitude of alpha",
    "controlled NOT",
    "Pauli X",
    "Bloch sphere",
    "inner product of phi sub i",
    "ket 1 0 1",
    "tensor product",
  ])
    assert(output.includes(word), `${word}: ${output}`);
  assert(!/[|⟩⟨⊗αβψ²*]/.test(output), output);
});
test("lists, markup, code, powers, fractions and ASCII notation", () => {
  const output = normalizeSpeech(
    "# Example\n- **First**\n- Second\n```python\nprint(secret)\n```\n|0> = 1/√2. 2ⁿ and a^{r/2} ≠ -1. [Lesson](/learn)",
  );
  assert(!output.includes("print"));
  assert(!output.includes("/learn"));
  assert(output.includes("ket 0"));
  assert(output.includes("divided by square root of 2"));
  assert(output.includes("to the power of n"));
  assert(output.includes("is not equal to minus 1"));
  assert(!output.includes("minus First"));
});
test("chunking preserves sentence content and bounded long text", () => {
  const text = Array.from(
    { length: 150 },
    (_, i) => `Paragraph ${i} explains measurement with probability 0.5.`,
  ).join("\n\n");
  const chunks = chunkSpeech(text);
  assert(chunks.length > 5);
  assert(chunks.every((c) => c.length <= 900));
  assert.equal(
    chunks.join(" ").replace(/\s+/g, " "),
    text.replace(/\s+/g, " "),
  );
  assert(chunkSpeech("x".repeat(4000)).every((c) => c.length <= 900));
});
test("every module has content-driven narration without hidden quiz answers", () => {
  assert.equal(modules.length, 8);
  for (const lesson of modules) {
    const sections = moduleNarration(lesson);
    const chunks = prepareNarration(sections);
    assert(sections.some((s) => s.text === lesson.introduction));
    assert(sections.some((s) => s.text === lesson.workedExample));
    assert(sections.some((s) => s.text === lesson.keyTakeaways));
    assert.equal(sections.length, lesson.sections.length + 4);
    assert(chunks.every((c) => c.spokenText.length <= 900));
    assert(!sections.some((s) => s.id.includes("quiz")));
  }
});
test("play, pause, resume, seek, speed, stop, replay and sequential segments", async () => {
  const audios = [];
  let calls = 0;
  const controller = new NarrationController(
    async () => {
      calls++;
      return new Blob(["audio"]);
    },
    () => {
      const audio = new Audio();
      audios.push(audio);
      return audio;
    },
  );
  controller.start("lesson", segment());
  await tick();
  assert.equal(controller.getSnapshot().status, "playing");
  controller.pause();
  assert.equal(controller.getSnapshot().status, "paused");
  controller.resume();
  await tick();
  assert.equal(calls, 1);
  assert.equal(controller.getSnapshot().status, "playing");
  controller.seek(4);
  assert.equal(controller.getSnapshot().currentTime, 4);
  controller.setSpeed(1.5);
  assert.equal(audios[0].playbackRate, 1.5);
  controller.setVolume(0.3);
  assert.equal(audios[0].volume, 0.3);
  controller.start("new", [
    ...segment(),
    { id: "next", title: "Next", text: "Measurement." },
  ]);
  await tick();
  assert(audios[0].paused);
  audios.at(-1).end();
  await tick();
  assert.equal(controller.getSnapshot().index, 1);
  audios.at(-1).end();
  assert.equal(controller.getSnapshot().status, "ended");
  controller.replay();
  await tick();
  assert.equal(controller.getSnapshot().index, 0);
  controller.stop();
  assert.equal(controller.getSnapshot().status, "idle");
  assert(audios.every((a) => a.paused));
});
test("stop and replacement prevent late requests from starting audio", async () => {
  const pending = [];
  const audios = [];
  const controller = new NarrationController(
    (text, signal) =>
      new Promise((resolve) => pending.push({ resolve, signal })),
    () => {
      const a = new Audio();
      audios.push(a);
      return a;
    },
  );
  controller.start("a", segment());
  controller.stop();
  assert(pending[0].signal.aborted);
  pending[0].resolve(new Blob(["a"]));
  await tick();
  assert.equal(audios.length, 0);
  controller.start("b", segment("B"));
  controller.start("c", segment("C"));
  pending[1].resolve(new Blob(["b"]));
  pending[2].resolve(new Blob(["c"]));
  await tick();
  assert.equal(audios.length, 1);
  assert.equal(controller.getSnapshot().owner, "c");
  controller.stop();
});
test("pause while generating stays paused; retry after failure works", async () => {
  let resolve;
  const controller = new NarrationController(
    () => new Promise((r) => (resolve = r)),
    () => new Audio(),
  );
  controller.start("a", segment());
  controller.pause();
  resolve(new Blob(["a"]));
  await tick();
  assert.equal(controller.getSnapshot().status, "paused");
  controller.resume();
  await tick();
  assert.equal(controller.getSnapshot().status, "playing");
  controller.stop();
  let fail = true;
  const retry = new NarrationController(
    async () => {
      if (fail) throw new Error("Unavailable");
      return new Blob(["a"]);
    },
    () => new Audio(),
  );
  retry.start("a", segment());
  await tick();
  assert.equal(retry.getSnapshot().status, "error");
  fail = false;
  retry.retry();
  await tick();
  assert.equal(retry.getSnapshot().status, "playing");
  retry.stop();
});
