const ts=require('typescript');
const fs=require('node:fs');
const path=require('node:path');
const Module=require('node:module');
const resolve=Module._resolveFilename;
Module._resolveFilename=function(name,...args){return resolve.call(this,name.startsWith('@/')?path.join(__dirname,'../src',name.slice(2)):name,...args)};
for(const ext of ['.ts','.tsx'])require.extensions[ext]=(module,filename)=>module._compile(ts.transpileModule(fs.readFileSync(filename,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX}}).outputText,filename);
const {test}=require('node:test');
const assert=require('node:assert/strict');
const React=require('react');
const {renderToStaticMarkup}=require('react-dom/server');
const {parseValidationResult,validPrediction,circuitIdentity}=require('../src/lib/learning-challenges.ts');
const {ChallengeFeedback,PredictionComparison}=require('../src/components/circuit-builder/ChallengeFeedback.tsx');
const contract=require('./fixtures/challenge-contract.json');
const modules=require('../../backend/data/modules.json');
const render=(C,p)=>renderToStaticMarkup(React.createElement(C,p));

test('all 16 curriculum identities and actual backend validator results satisfy runtime frontend contract',()=>{
  assert.equal(contract.length,16);
  for(const row of contract){
    const r=parseValidationResult(row.result);
    assert.equal(r.challengeId,row.definition.id);assert.equal(r.moduleId,row.definition.moduleId);
    const lesson=modules.find(m=>m.id===r.moduleId);
    assert.ok([...lesson.experiments,...lesson.challenges].some(a=>a.id===r.challengeId));
    assert.ok(row.definition.validationTypes.length);assert.equal(r.score,100);
    const html=render(ChallengeFeedback,{feedback:r});
    assert.match(html,/✓ Success/);assert.match(html,/role="status"/);
  }
});
test('frontend rejects malformed feedback, invented status, inconsistent pass and unbounded scores',()=>{
  for(const patch of [{status:'completed'},{score:101},{score:-1},{passed:false},{checks:[{passed:'yes'}]},{feedback:{summary:'fake'}},{moduleId:'4'}])assert.throws(()=>parseValidationResult({...contract[0].result,...patch}));
});
test('prediction form requires a full finite normalized distribution',()=>{
  assert.equal(validPrediction(['0','1'],{'0':'.5','1':'.5'},true),true);
  for(const v of [{'0':'','1':'1'},{'0':'NaN','1':'0'},{'0':'.6','1':'.6'},{'0':'-1','1':'2'}])assert.equal(validPrediction(['0','1'],v,true),false);
});
test('circuit identity invalidates commitment for gate, qubit, register and shot changes',()=>{
  const base={gates:[],num_qubits:2,shots:1024};
  for(const patch of [{gates:[{type:'H',qubit:0}]},{num_qubits:1},{shots:256},{classical_registers:[{name:'c',size:2}]}])assert.notEqual(circuitIdentity(base),circuitIdentity({...base,...patch}));
});
test('conceptual predictions require bounded integers just like the API',()=>{
  assert.equal(validPrediction(['order'],{order:'4'},false),true);
  for(const order of ['4.5','100001','-100001','Infinity',''])assert.equal(validPrediction(['order'],{order},false),false);
});
test('near miss and invalid feedback include textual status and per-check explanations',()=>{
  const base=contract[0].result;
  assert.match(render(ChallengeFeedback,{feedback:{...base,passed:false,score:0,status:'near_miss'}}),/Near miss/);
  assert.match(render(ChallengeFeedback,{feedback:{...base,passed:false,score:0,status:'invalid_circuit'}}),/Invalid circuit/);
});
test('prediction comparison separates ideal behavior from noisy shots',()=>{
  const comparison={matches:true,prediction:{'0':.5,'1':.5},actual:{'0':.48,'1':.52},ideal:{'0':.5,'1':.5},basis:'ideal probabilities',tolerance:.03};
  const html=render(PredictionComparison,{comparison,conceptual:false});
  assert.match(html,/Prediction matches/);assert.match(html,/Ideal/);assert.match(html,/Sampled result/);assert.match(html,/0.480/);
});
test('comparison exposes unexpected outcomes after changing the circuit width',()=>{
  const comparison={matches:false,prediction:{'0':.5,'1':.5},actual:{'00':1},ideal:{'00':1},basis:'ideal probabilities',tolerance:.03};
  const html=render(PredictionComparison,{comparison,conceptual:false});
  assert.match(html,/<th>00<\/th><td>Not predicted<\/td><td>1.000<\/td><td>1.000<\/td>/);
});
test('frontend contains no local module-specific correctness rules or legacy challenge definitions',()=>{
  const builder=fs.readFileSync(path.join(__dirname,'../src/components/circuit-builder/CircuitBuilder.tsx'),'utf8');
  const lesson=fs.readFileSync(path.join(__dirname,'../src/app/learn/[id]/page.tsx'),'utf8');
  assert.doesNotMatch(builder,/const CHALLENGES|challengeKey ===|conceptualCircuit/);
  assert.doesNotMatch(lesson,/lesson\.id === [45678]/);
});
