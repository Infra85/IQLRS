/* Production rendering and real quiz API check. Requires a test account token.
   CURRICULUM_TOKEN must belong to an isolated test DB; no provider calls are made. */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const modules = require('../../../backend/data/modules.json');
(async () => {
  assert.ok(process.env.CURRICULUM_TOKEN, 'Provide an isolated test account token');
  const browser = await chromium.launch({executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome-stable', headless:true});
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.addInitScript(token => localStorage.setItem('access_token', token), process.env.CURRICULUM_TOKEN);
  const base = process.env.CURRICULUM_URL || 'http://127.0.0.1:13002';
  try {
    for (const lesson of modules) {
      const response = await page.goto(`${base}/learn/${lesson.id}`);
      assert.equal(response.status(), 200);
      await page.getByRole('heading', {name:lesson.title.replace(/^Module \d+ – /, ''),exact:true}).waitFor();
      for (const section of lesson.sections) {
        await page.getByRole('heading', {name:section.title,exact:true}).waitFor();
        assert.ok(await page.locator('article').textContent().then(t => t.includes(section.description)));
        assert.ok(await page.locator('pre').allTextContents().then(t => t.includes(section.diagram)));
      }
      const article = await page.locator('article').innerText();
      assert.ok(article.includes(lesson.workedExample));
      assert.ok(!article.includes('assessmentQuestionIndices'));
      assert.ok(!article.includes('requiresBuilder'));
      assert.equal(await page.locator('fieldset').count(), lesson.questions.length);
      assert.ok(await page.getByRole('button', {name:'Check answers',exact:true}).isDisabled());
      for (const [i,q] of lesson.questions.entries()) {
        await page.locator(`#quiz-question-${i} input[type=radio]`).nth(q.answerIndex).check();
      }
      const pending = page.waitForResponse(r => r.url().includes(`/api/progress/lessons/${lesson.id}/quiz`) && r.request().method()==='POST');
      await page.getByRole('button', {name:'Check answers',exact:true}).click();
      const submitted = await pending;
      assert.equal(submitted.status(),200,await submitted.text());
      assert.deepEqual(submitted.request().postDataJSON().answers,lesson.questions.map(q=>q.answerIndex));
      await page.getByText(`Your score: ${lesson.questions.length} / ${lesson.questions.length}.`,{exact:false}).waitFor();
      for (const [i,q] of lesson.questions.entries()) {
        assert.ok((await page.locator(`#quiz-feedback-${i}`).innerText()).includes(q.explanation));
      }
      await page.getByRole('button',{name:'Retry quiz',exact:true}).click();
      assert.equal(await page.locator('input[type=radio]:checked').count(),0);
      const builder = page.locator('#example a[href^="/builder"]');
      if (lesson.id<=3) assert.equal(await builder.count(),0);
      else {
        const expected=lesson.id===4?'/builder?challenge=bell':lesson.id===6?'/builder?challenge=grover':'/builder';
        assert.equal(await builder.getAttribute('href'),expected);
        await builder.click();
        await page.waitForURL(`${base}${expected}`);
        await page.getByRole('button',{name:'Run simulation',exact:true}).waitFor();
      }
    }
    assert.deepEqual(errors,[]);
    console.log('PASS: 8 lesson renders, 24 quiz answers/explanations, 8 real API submissions/retries, 5 builder links; no page errors.');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
