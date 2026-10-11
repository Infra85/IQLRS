/* Real authenticated browser flow. Use a dedicated test database/account only.
   PHASE2_EMAIL and PHASE2_PASSWORD are required; NODE_PATH must expose playwright. */
const {chromium}=require('playwright');
const {test,before,after}=require('node:test');
const assert=require('node:assert/strict');
const fixtures=require('../../../backend/tests/fixtures/learning_challenges.json');
const definitions=require('../../../backend/data/challenges.json');
const modules=require('../../../backend/data/modules.json');
let browser,page;
const errors=[];
const base=process.env.PHASE2_URL||'http://127.0.0.1:13002';
before(async()=>{
  assert.ok(process.env.PHASE2_EMAIL&&process.env.PHASE2_PASSWORD,'Use an isolated test learner');
  browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome-stable',headless:true});
  page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'/login');
  await page.getByLabel('Email address').fill(process.env.PHASE2_EMAIL);
  await page.getByLabel('Password',{exact:true}).fill(process.env.PHASE2_PASSWORD);
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await page.waitForURL(base+'/');
});
after(async()=>{await browser?.close();assert.deepEqual(errors,[])});
async function open(id){
  const d=definitions.find(x=>x.id===id);
  await page.goto(`${base}/builder?module=${d.moduleId}&challenge=${id}`);
  await page.getByRole('heading',{name:d.title,exact:true}).waitFor();
  await page.getByRole('button',{name:d.kind==='conceptual'?'Reset answers':'Reset to starter',exact:true}).click();
}
async function prediction(id){
  for(const [key,value] of Object.entries(fixtures[id].prediction))await page.getByLabel(`Prediction ${key}`,{exact:true}).fill(String(value));
}
async function clickResponse(label,path,retried=false){
  const response=page.waitForResponse(r=>r.url().includes(path)&&['POST','PUT'].includes(r.request().method()));
  await page.getByRole('button',{name:label,exact:true}).click();
  const r=await response;
  if(r.status()===429&&!retried){
    // Full-curriculum coverage can exceed the real API's per-minute budget.
    // Keep rate limiting enabled and respect its retry interval.
    await new Promise(resolve=>setTimeout(resolve,Number(r.headers()['retry-after']||60)*1000));
    return clickResponse(label,path,true);
  }
  assert.equal(r.status(),200,await r.text());
  return r.json();
}
async function add(g,index){
  const button=page.locator('.gate-palette').getByRole('button',{name:g.type,exact:true});
  if(await button.getAttribute('aria-pressed')!=='true')await button.click();
  const place=async q=>page.getByRole('button',{name:`Place selected gate on qubit ${q}`,exact:true}).last().click();
  if(g.control!==undefined){await place(g.control);await place(g.target)}else await place(g.qubit??0);
  if(g.condition){const control=page.getByLabel(`Operation ${index+1} classical condition`,{exact:true});if(!await control.isVisible())await page.getByText('Classical registers and conditions',{exact:true}).first().click();await page.getByLabel(`Operation ${index+1} classical condition`,{exact:true}).selectOption(`${g.condition.register}:${g.condition.bit}`)}
}
async function buildReference(id){
  const d=definitions.find(x=>x.id===id),f=fixtures[id];
  for(let i=d.starterCircuit.gates.length;i<f.circuit.gates.length;i++)await add(f.circuit.gates[i],i);
}
async function complete(id){
  await prediction(id);
  await clickResponse('Commit prediction','/prediction');
  if(definitions.find(x=>x.id===id).kind==='circuit'){
    await clickResponse('Run experiment','/run');
    await page.getByRole('heading',{name:'Prediction vs result',exact:true}).waitFor();
  }
  const r=await clickResponse(id.startsWith('m8')?'Validate reasoning':'Validate challenge','/validate');
  assert.equal(r.result.passed,true,JSON.stringify(r));
  await page.getByTestId('challenge-feedback').getByText('✓ Success',{exact:false}).waitFor();
}

test('all eight lessons expose both stable curriculum activity links',async()=>{
  for(const m of modules){
    await page.goto(`${base}/learn/${m.id}`);
    for(const a of [...m.experiments,...m.challenges])assert.equal(await page.locator(`:is(#learning-activities, #lesson-challenges) a[href="/builder?module=${m.id}&challenge=${a.id}"]`).count(),1);
  }
});

test('Bell learner path: wrong circuit, hint, edit, prediction, run, semantic validation, reload and module completion',async()=>{
  await page.goto(base+'/learn/4');
  await page.locator('a[href="/builder?module=4&challenge=m4-challenge"]').click();
  await page.getByRole('button',{name:'Reset to starter',exact:true}).click();
  const baseline=await page.evaluate(async()=>{const r=await fetch('/api/challenges/m4-challenge',{headers:{Authorization:'Bearer '+localStorage.getItem('access_token')}});return r.json()});
  await prediction('m4-challenge');
  assert.equal(await page.getByRole('button',{name:'Run experiment',exact:true}).isDisabled(),true);
  await clickResponse('Commit prediction','/prediction');
  await clickResponse('Run experiment','/run');
  const bad=await clickResponse('Validate challenge','/validate');
  assert.equal(bad.result.passed,false);
  assert.ok(bad.result.feedback.explanation.includes('relative plus phase'));
  if(baseline.hints.length<3)await clickResponse(`Reveal next hint (${baseline.hints.length}/3)`,'/hints');
  await buildReference('m4-challenge');
  assert.equal(await page.getByRole('button',{name:'Validate challenge',exact:true}).isDisabled(),true);
  await complete('m4-challenge');
  await clickResponse('Save circuit to my history','/save-circuit');
  await page.reload();
  await page.getByText('✓ Activity completed',{exact:false}).waitFor();
  await page.getByText(`Hints used ${Math.min(3,baseline.hints.length+1)}`,{exact:false}).waitFor();
  await page.getByRole('button',{name:'Try again',exact:true}).click();
  await page.getByRole('button',{name:'Reset to starter',exact:true}).click();
  await page.getByText(`Attempt history (${baseline.history.length+2})`,{exact:true}).waitFor();
  await page.goto(base+'/learn/4');
  await page.locator(':is(#learning-activities, #lesson-challenges) article').filter({has:page.locator('a[href="/builder?module=4&challenge=m4-challenge"]')}).getByText('✓ Completed',{exact:true}).waitFor();
});
for(const [id,label] of definitions.filter(d=>d.id!=='m4-challenge').map(d=>[d.id,`${d.id}: ${d.title}`])){
  test(label,async()=>{
    await open(id);await buildReference(id);await complete(id);
    if(id==='m8-challenge'){
      assert.equal(await page.getByRole('button',{name:'Run simulation',exact:true}).count(),0);
      assert.equal(await page.getByLabel('Circuit canvas',{exact:true}).count(),0);
      await page.setViewportSize({width:390,height:844});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true);
      await page.screenshot({path:'/tmp/iqlrs-phase2-conceptual.png',fullPage:true});
      await page.setViewportSize({width:1440,height:1000});
    }
    if(id==='m7-challenge')await page.screenshot({path:'/tmp/iqlrs-phase2-teleportation.png',fullPage:true});
  });
}
test('activity limits match committed shots and client navigation restores freeform mode',async()=>{
  await open('m1-experiment');
  const shots=page.getByRole('spinbutton',{name:'Shots',exact:true});
  await shots.fill('8192');
  assert.equal(await shots.inputValue(),'2048');
  await prediction('m1-experiment');
  const pending=page.waitForRequest(r=>r.url().endsWith('/prediction')&&r.method()==='PUT');
  await clickResponse('Commit prediction','/prediction');
  assert.equal((await pending).postDataJSON().circuit.shots,2048);
  await page.getByRole('button',{name:'Add one qubit',exact:true}).click();
  await page.getByRole('button',{name:'Add one qubit',exact:true}).click();
  assert.equal(await page.getByRole('button',{name:'Add one qubit',exact:true}).isDisabled(),true);
  assert.equal(await page.getByRole('button',{name:'Run experiment',exact:true}).isDisabled(),true);
  await open('m8-challenge');
  await page.getByRole('navigation',{name:'Primary',exact:true}).getByRole('link',{name:'Circuit builder',exact:true}).click();
  await page.waitForURL(base+'/builder');
  await page.getByRole('button',{name:'Run simulation',exact:true}).waitFor();
  assert.equal(await page.getByTestId('challenge-panel').count(),0);
  assert.equal(await page.getByRole('spinbutton',{name:'Shots',exact:true}).getAttribute('max'),'8192');
});
test('freeform builder, legacy URLs and existing quiz remain usable',async()=>{
  await page.goto(base+'/builder');
  assert.equal(await page.getByTestId('challenge-panel').count(),0);
  await add({type:'H',qubit:0},0);
  await clickResponse('Run simulation','/simulate');
  await page.getByRole('heading',{name:'Measurement counts',exact:true}).waitFor();
  await page.goto(base+'/builder?challenge=bell');
  await page.getByRole('heading',{name:definitions.find(d=>d.id==='m4-challenge').title,exact:true}).waitFor();
  await page.goto(base+'/builder?module=5');
  await page.getByRole('heading',{name:definitions.find(d=>d.id==='m5-experiment').title,exact:true}).waitFor();
  await page.goto(base+'/learn/1');
  const m=modules[0];
  for(const [i,q] of m.questions.entries())await page.locator(`#quiz-question-${i} input[type=radio]`).nth(q.answerIndex).check();
  await clickResponse('Check answers','/quiz');
  await page.getByText(`Your score: ${m.questions.length} / ${m.questions.length}.`,{exact:false}).waitFor();
});
