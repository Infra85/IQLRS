const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');
const source = fs.readFileSync(path.join(__dirname, '../src/app/learn/modules.ts'), 'utf8');
const compiled = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.CommonJS}}).outputText;
const exported = {};
new Function('exports', compiled)(exported);
const server = JSON.parse(fs.readFileSync(path.join(__dirname, '../../backend/data/modules.json'), 'utf8'));
assert.deepEqual(exported.modules, server, 'Rendered questions and server-side quiz scoring must match.');
require('node:child_process').execFileSync(process.execPath, [path.join(__dirname, '../scripts/sync-curriculum.cjs'), '--check']);
assert.equal(exported.getModule(999), undefined);
for (const lesson of exported.modules) {
  assert.equal(exported.getModule(lesson.id), lesson);
  assert.ok(lesson.questions.every(q => q.explanation && Number.isInteger(q.answerIndex)));
}
