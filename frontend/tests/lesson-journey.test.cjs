const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const ts=require('typescript');
const exported={};
new Function('exports',ts.transpileModule(fs.readFileSync(require('node:path').join(__dirname,'../src/lib/lesson-journey.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText)(exported);
const {returnStep,resumeModule,statusLabel}=exported;
const steps=[{id:'concept-0',kind:'section',status:'completed'},{id:'experiment',kind:'experiment',status:'completed'},{id:'reflection',kind:'reflection',status:'not_started'},{id:'quiz',kind:'quiz',status:'retry_needed'}];
test('return to explanation after successful experiment, review section after failure',()=>{
  assert.equal(returnStep({steps,next:steps[2]},'experiment').id,'reflection');
  assert.equal(returnStep({steps:steps.map(s=>s.id==='experiment'?{...s,status:'retry_needed'}:s),next:steps[2]},'experiment').id,'concept-0');
  assert.equal(returnStep({steps,next:steps[2]},'unknown').id,'reflection');
});
test('resume follows available prerequisites and recent activity, skips completed modules',()=>{
  const modules=[{moduleId:1,status:'in_progress',pendingPrerequisites:[],updatedAt:'2026-01-01'},{moduleId:2,status:'in_progress',pendingPrerequisites:[1],updatedAt:'2026-02-01'},{moduleId:3,status:'completed',pendingPrerequisites:[],updatedAt:'2026-03-01'}];
  assert.equal(resumeModule(modules).moduleId,1);
  modules[1].pendingPrerequisites=[];
  assert.equal(resumeModule(modules).moduleId,2);
  assert.equal(resumeModule([]),undefined);
});
test('every progress state has an explicit readable label',()=>{
  assert.equal(Object.keys(statusLabel).length,4);
  assert.match(statusLabel.retry_needed,/Retry needed/);
  assert.match(statusLabel.not_started,/Not started/);
});
