'use client';
import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';
import { type Journey, type JourneyStep, statusLabel, resumeModule, returnStep } from '@/lib/lesson-journey';
import { Button } from '@/components/ui/button';

type Context = { journey: Journey | null; busy: boolean; signedIn: boolean; update: (id: string, action: 'start' | 'complete', navigate?: boolean) => Promise<void> };
const JourneyContext = createContext<Context | null>(null);
export function useLessonJourney() { return useContext(JourneyContext); }

export function LessonJourney({ moduleId, children }: { moduleId: number; children: React.ReactNode }) {
  const [journey, setJourney] = useState<Journey | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [signedIn, setSignedIn] = useState(false);
  const router = useRouter();
  const refresh = useCallback(async () => {
    const authenticated = !!localStorage.getItem('access_token');
    setSignedIn(authenticated);
    if (authenticated) {
      const data = await apiFetch('/api/progress/journey');
      setJourney(data.modules.find((m: Journey) => m.moduleId === moduleId));
    } else {
      const data = await apiFetch(`/api/progress/lessons/${moduleId}/sequence`);
      setJourney({ moduleId, title: '', steps: data.steps.map((s: JourneyStep) => ({...s, status: 'not_started'})), status: 'not_started', completedSteps: 0, totalSteps: data.steps.length, completionPct: 0, resume: data.steps[0], next: data.steps[0], prerequisites: [], pendingPrerequisites: [], nextModule: null, updatedAt: null });
    }
    setError('');
  }, [moduleId]);
  useEffect(() => {
    let active = true;
    const load = () => { if (active) void refresh().catch(e => { if (active) setError(e.message); }); };
    load();
    window.addEventListener('lesson-progress', load);
    window.addEventListener('focus', load);
    return () => { active = false; window.removeEventListener('lesson-progress', load); window.removeEventListener('focus', load); };
  }, [refresh]);
  async function update(id: string, action: 'start' | 'complete', navigate = false) {
    if (busy || !journey) return;
    if (!signedIn) { router.push(journey.steps.find(s => s.id === id)?.href ?? '/login'); return; }
    setBusy(true); setError('');
    try {
      const next: Journey = await apiFetch(`/api/progress/lessons/${moduleId}/journey`, {method: 'PUT', body: JSON.stringify({step_id: id, action})});
      setJourney(next);
      const destination = action === 'complete' ? next.next : next.steps.find(s => s.id === id);
      if (navigate && destination) router.push(destination.href);
    } catch (e) { setError(e instanceof Error ? e.message : 'Progress could not be saved. Please retry.'); }
    finally { setBusy(false); }
  }
  return <JourneyContext.Provider value={{journey, busy, signedIn, update}}>
    <section id="guided-journey" className="panel p-6 my-6 space-y-4" aria-label="Guided lesson journey">
      <h2 className="text-xl font-semibold">Your guided journey</h2>
      <p>Read → Experiment → Compare and explain → Quiz → Challenge → Next module</p>
      <p>Complete each reading step, validate the experiment, review its explanation, pass the quiz and challenge. Saved predictions and results resume in the builder.</p>
      {!signedIn && <p><Link className="underline" href="/login">Sign in</Link> to save and resume your progress. Lessons and quizzes can be previewed freely.</p>}
      {error && <p role="alert">{error} <button className="underline" onClick={() => void refresh().catch(e => setError(e.message))}>Retry loading progress</button></p>}
      {!journey && !error && <p role="status">Loading journey…</p>}
      {journey && <>
        <p role="status">{statusLabel[journey.status]} · {journey.completedSteps} / {journey.totalSteps} steps completed</p>
        <progress className="w-full" value={journey.completedSteps} max={journey.totalSteps} aria-label="Guided module completion" />
        {!!journey.pendingPrerequisites.length && <p>Recommended first: {journey.pendingPrerequisites.map(n => <Link className="underline mr-3" href={`/learn/${n}#guided-journey`} key={n}>Module {n}</Link>)}. You can still preview this lesson.</p>}
        {journey.resume && <Button disabled={busy} onClick={() => void update(journey.resume!.id, 'start', true)}>Resume: {journey.resume.title}</Button>}
        {journey.status === 'completed' && <p>Module complete: readings, experiment, reflection, quiz and challenge are saved. {journey.nextModule ? <Link className="underline" href={`/learn/${journey.nextModule}#guided-journey`}>Continue to module {journey.nextModule} →</Link> : <Link className="underline" href="/learn">All eight modules completed — review your learning path →</Link>}</p>}
        <details><summary className="cursor-pointer">Activity sequence and progress</summary><ol className="list-decimal pl-6 space-y-2 mt-4">{journey.steps.map(s => <li key={s.id}><button disabled={busy} onClick={() => void update(s.id, 'start', true)} className="underline text-left">{s.title}</button> · {s.kind} · {statusLabel[s.status]}</li>)}</ol></details>
      </>}
    </section>
    {children}
  </JourneyContext.Provider>;
}

export function ReadingProgress({ id }: { id: string }) {
  const context = useContext(JourneyContext);
  const step = context?.journey?.steps.find(s => s.id === id);
  if (!context || !step) return null;
  const ready = !step.activityId || context.journey?.steps.find(s => s.id === step.activityId)?.status === 'completed';
  return <div className="mt-5 space-y-3" data-reading-step={id}>
    <p className="text-sm">{statusLabel[step.status]}</p>
    {context.signedIn ? <Button variant="secondary" disabled={context.busy || !ready || step.status === 'completed'} onClick={() => void context.update(id, 'complete', true)}>{step.kind === 'reflection' ? 'I compared my prediction and reviewed the explanation' : 'Mark read and continue'}</Button> : <Link className="underline" href="/login">Sign in to record this step</Link>}
    {!ready && <p>Complete and validate the experiment to record this reflection.</p>}
  </div>;
}

export function Reflections() {
  const context = useContext(JourneyContext);
  return <>{context?.journey?.steps.filter(s => s.kind === 'reflection').map(s => <section className="lesson-section" id={s.id} key={s.id}>
    <h2>{s.title}</h2><p>{s.explanation}</p><p>How did your prediction compare with the result? Explain the difference using the lesson above. Revisit the activity to inspect your saved comparison and feedback.</p>
    <Link className="underline" href={context.journey!.steps.find(a => a.id === s.activityId)!.href}>Review experiment and comparison ↗</Link>
    <ReadingProgress id={s.id} />
  </section>)}</>;
}

export function JourneyOverview() {
  const [modules, setModules] = useState<Journey[] | null>(null);
  const [error, setError] = useState('');
  useEffect(() => { if (localStorage.getItem('access_token')) apiFetch('/api/progress/journey').then(data => setModules(data.modules)).catch(e => setError(e.message)); }, []);
  if (error) return <p role="alert">Learning progress unavailable: {error} <button className="underline" onClick={() => window.location.reload()}>Retry</button></p>;
  if (!modules) return null;
  const resume = resumeModule(modules);
  return <section className="panel p-6 mb-6 space-y-3" aria-label="Guided curriculum progress"><h2 className="text-xl">Guided curriculum progress</h2>
    <p>{modules.filter(m => m.status === 'completed').length} / {modules.length} full modules completed. Quiz scores remain a separate record.</p>
    {resume && <Link className="ui-button button-primary" href={`/learn/${resume.moduleId}#guided-journey`}>Resume module {resume.moduleId}: {resume.resume?.title}</Link>}
    <ul className="space-y-2">{modules.map(m => <li key={m.moduleId}><Link className="underline" href={`/learn/${m.moduleId}#guided-journey`}>Module {m.moduleId}</Link> · {statusLabel[m.status]} · {m.completedSteps}/{m.totalSteps} steps {m.pendingPrerequisites.length > 0 && `· Recommended prerequisites: ${m.pendingPrerequisites.join(', ')}`}</li>)}</ul>
  </section>;
}

export function JourneyReturn({ moduleId, activityId, completed }: { moduleId: number; activityId: string; completed: boolean }) {
  const [journey, setJourney] = useState<Journey | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    apiFetch(`/api/progress/lessons/${moduleId}/journey`, {method: 'PUT', body: JSON.stringify({step_id: activityId, action: 'start'})}).then(data => {if (active) setJourney(data);}).catch(e => {if (active) setError(e.message);});
    return () => {active = false;};
  }, [moduleId, activityId, completed]);
  const next = journey ? returnStep(journey, activityId) : null;
  return <div className="space-y-2 border-t border-slate-700 pt-4">
    {error && <p role="alert">Resume location could not be saved: {error}</p>}
    <Link className="ui-button button-secondary" href={next?.href ?? `/learn/${moduleId}#guided-journey`}>{completed ? 'Continue lesson' : 'Review lesson'}{next ? `: ${next.title}` : ''} →</Link>
    <p className="text-sm">{completed ? 'Your successful activity attempt is saved. Return to finish the remaining lesson steps.' : 'Opening or running an activity does not complete it. Commit, run and validate; conceptual activities use reasoning validation.'}</p>
  </div>;
}

export function NextJourneyActivity() {
  const context = useLessonJourney();
  const next = context?.journey?.next;
  if (!context || !next) return null;
  return <Button disabled={context.busy} onClick={() => void context.update(next.id, 'start', true)}>Next guided activity: {next.title} →</Button>;
}
