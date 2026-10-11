/* Real UI journey through all eight modules. Requires a fresh dedicated learner.
   JOURNEY_TOKEN must belong to an isolated database; no live provider calls. */
const {chromium}=require('playwright');
const {test,before,after}=require('node:test');
const assert=require('node:assert/strict');
const fixtures=require('../../../backend/tests/fixtures/learning_challenges.json');
const definitions=require('../../../backend/data/challenges.json');
const modules=require('../../../backend/data/modules.json');
const base=process.env.JOURNEY_URL||'http://127.0.0.1:13002';
let browser,page;
const errors=[];
before(async()=>{
  assert.ok(process.env.JOURNEY_TOKEN,'Provide a fresh isolated learner token');
  browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome-stable',headless:true});
  page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.setDefaultTimeout(20000);
  page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(token=>localStorage.setItem('access_token',token),process.env.JOURNEY_TOKEN);
  await page.goto(base+'/learn/1');
});
after(async()=>{await browser?.close();assert.deepEqual(errors,[])});
async function responseClick(locator,path){
  const pending=page.waitForResponse(r=>r.url().includes(path)&&['POST','PUT'].includes(r.request().method()));
  await locator.click();
  const response=await pending;
  if(response.status()===429){
    await new Promise(resolve=>setTimeout(resolve,Number(response.headers()['retry-after']||60)*1000));
    return responseClick(locator,path);
  }
  assert.equal(response.status(),200,await response.text());
  return response.json();
}
async function click(label,path){return responseClick(page.getByRole('button',{name:label,exact:true}),path);}
async function completeActivity(id){
  const definition=definitions.find(d=>d.id===id),fixture=fixtures[id];
  await page.waitForURL(`${base}/builder?module=${definition.moduleId}&challenge=${id}`);
  await page.getByRole('heading',{name:definition.title,exact:true}).waitFor();
  for(let i=definition.starterCircuit.gates.length;i<fixture.circuit.gates.length;i++){
    const gate=fixture.circuit.gates[i];
    const button=page.locator('.gate-palette').getByRole('button',{name:gate.type,exact:true});
    if(await button.getAttribute('aria-pressed')!=='true')await button.click();
    const place=q=>page.getByRole('button',{name:`Place selected gate on qubit ${q}`,exact:true}).last().click();
    if(gate.control!==undefined){await place(gate.control);await place(gate.target);}else await place(gate.qubit??0);
    if(gate.condition){
      const control=page.getByLabel(`Operation ${i+1} classical condition`,{exact:true});
      if(!await control.isVisible())await page.getByText('Classical registers and conditions',{exact:true}).first().click();
      await control.selectOption(`${gate.condition.register}:${gate.condition.bit}`);
    }
  }
  for(const [key,value] of Object.entries(fixture.prediction))await page.getByLabel(`Prediction ${key}`,{exact:true}).fill(String(value));
  await click('Commit prediction','/prediction');
  if(id==='m1-experiment'){
    await page.getByRole('link',{name:'Module 1 · Back to lesson',exact:true}).click();
    await page.getByRole('button',{name:`Resume: ${definition.title}`,exact:true}).click();
    await page.waitForURL(`${base}/builder?module=1&challenge=${id}`);
    await page.reload();
    await page.getByText('Prediction committed and saved.',{exact:false}).waitFor();
    assert.equal(await page.getByLabel('Prediction 0',{exact:true}).inputValue(),String(fixture.prediction['0']));
  }
  if(definition.kind==='circuit'){
    await click('Run experiment','/run');
    await page.getByRole('heading',{name:'Prediction vs result',exact:true}).waitFor();
  }else{
    assert.equal(await page.getByLabel('Circuit canvas',{exact:true}).count(),0);
  }
  const result=await click(definition.kind==='circuit'?'Validate challenge':'Validate reasoning','/validate');
  assert.equal(result.result.passed,true,JSON.stringify(result));
  await page.getByTestId('challenge-feedback').getByText('✓ Success',{exact:false}).waitFor();
  await page.reload();
  await page.getByTestId('challenge-feedback').getByText('✓ Success',{exact:false}).waitFor();
  const back=page.getByRole('link',{name:/^Continue lesson/});
  // Wait for the asynchronously derived destination, not its loading fallback.
  if(id.endsWith('experiment'))await page.waitForFunction(()=>document.querySelector('a[href$="-reflection"]'));
  await back.click();
  await page.waitForURL(new RegExp(`/learn/${definition.moduleId}(#|$)`));
}
for(const lesson of modules){
  test(`module ${lesson.id}: full guided sequence, durable completion and next module`,async()=>{
    const panel=page.getByRole('region',{name:'Guided lesson journey'});
    await panel.getByText('0 /',{exact:false}).waitFor();
    if(lesson.id===1){
      await page.route('**/api/progress/lessons/1/journey',route=>route.abort('failed'));
      await page.locator('[data-reading-step="objectives"]').getByRole('button').click();
      await panel.getByRole('alert').waitFor();
      assert.ok(await page.locator('[data-reading-step="objectives"]').getByText('○ Not started',{exact:true}).count());
      await page.unroute('**/api/progress/lessons/1/journey');
    }
    for(const key of ['objectives',...lesson.sections.map((_,i)=>`concept-${i}`),'example']){
      await responseClick(page.locator(`[data-reading-step="${key}"]`).getByRole('button',{name:'Mark read and continue',exact:true}),'/journey');
      if(lesson.id===1&&key==='objectives'){
        await page.reload();
        await page.locator('[data-reading-step="objectives"]').getByText('✓ Completed',{exact:true}).waitFor();
        await panel.getByRole('button',{name:`Resume: ${lesson.sections[0].title}`,exact:true}).waitFor();
      }
    }
    for(const activity of lesson.experiments){
      await completeActivity(activity.id);
      await responseClick(page.locator(`[data-reading-step="${activity.id}-reflection"]`).getByRole('button'),'/journey');
    }
    // A failed quiz creates a retry state; a later pass cannot be undone by a retry.
    if(lesson.id===1){
      for(const [i,q] of lesson.questions.entries())await page.locator(`#quiz-question-${i} input[type=radio]`).nth((q.answerIndex+1)%q.options.length).check();
      await click('Check answers','/quiz');
      await panel.getByText('Activity sequence and progress',{exact:true}).click();
      await panel.getByText('quiz · ↻ Retry needed',{exact:false}).waitFor();
      await page.getByRole('button',{name:'Retry quiz',exact:true}).click();
    }
    for(const [i,q] of lesson.questions.entries())await page.locator(`#quiz-question-${i} input[type=radio]`).nth(q.answerIndex).check();
    await click('Check answers','/quiz');
    await page.getByRole('button',{name:`Next guided activity: ${lesson.challenges[0].title} →`,exact:true}).waitFor();
    await page.getByRole('button',{name:/^Next guided activity:/}).click();
    for(const activity of lesson.challenges)await completeActivity(activity.id);
    await panel.getByText('Module complete: readings, experiment, reflection, quiz and challenge are saved.',{exact:false}).waitFor();
    await page.reload();
    await panel.getByText('Module complete:',{exact:false}).waitFor();
    if(lesson.id===1){
      await page.setViewportSize({width:390,height:844});
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'mobile page overflows');
      await page.screenshot({path:'/tmp/iqlrs-journey-mobile.png',fullPage:true});
      await page.setViewportSize({width:1440,height:1000});
    }
    if(lesson.id<8){
      await panel.getByRole('link',{name:`Continue to module ${lesson.id+1} →`,exact:true}).click();
      await page.waitForURL(`${base}/learn/${lesson.id+1}#guided-journey`);
    }else{
      await panel.getByRole('link',{name:/All eight modules completed/}).click();
      await page.getByText('8 / 8 full modules completed.',{exact:false}).waitFor();
      await page.screenshot({path:'/tmp/iqlrs-journey-complete.png',fullPage:true});
    }
  });
}

test('activity link remains usable while journey progress is still loading',async()=>{
  let pending;
  const blocked=new Promise(resolve=>{pending=resolve;});
  let release;
  const held=new Promise(resolve=>{release=resolve;});
  await page.route('**/api/progress/journey',async route=>{
    pending();
    await held;
    await route.continue().catch(()=>{});
  });
  try {
    await page.goto(base+'/learn/4');
    await blocked;
    await page.locator('#lesson-challenges a').click();
    await page.waitForURL(base+'/builder?module=4&challenge=m4-challenge',{timeout:5000});
    await page.getByRole('button',{name:'Reset to starter',exact:true}).waitFor();
  } finally {
    release();
    await page.unroute('**/api/progress/journey');
  }
});
