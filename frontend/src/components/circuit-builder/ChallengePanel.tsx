'use client';
import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react';
import Link from 'next/link';
import { apiFetch, type CircuitRequest, type CircuitResult } from '@/lib/api';
import { ChallengeFeedback, PredictionComparison } from "./ChallengeFeedback";
import { parseValidationResult, circuitIdentity, validPrediction, type ActivityDetail, type Comparison, type ValidationResult } from '@/lib/learning-challenges';
import { Button } from '@/components/ui/button';

export type ChallengeHandle = { run: () => Promise<void> };
type Props = { id: string | null; module: string | null; circuit: CircuitRequest; load: (c: CircuitRequest) => void; onResult: (r: CircuitResult) => void; onBusy: (busy: boolean) => void; onReady: (ready: boolean, conceptual: boolean) => void };
export const ChallengePanel=forwardRef<ChallengeHandle,Props>(function ChallengePanel({id,module,circuit,load,onResult,onReady,onBusy},ref){
  const [data,setData]=useState<ActivityDetail|null>(null);
  const [values,setValues]=useState<Record<string,string>>({});
  const [committed,setCommitted]=useState<{revision:string;identity:string;prediction:string}|null>(null);
  const [comparison,setComparison]=useState<Comparison|null>(null);
  const [feedback,setFeedback]=useState<ValidationResult|null>(null);
  const [ran,setRan]=useState(false);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const [saved,setSaved]=useState(false);
  const guard=useRef(false);
  const d=data?.definition;
  const identity=circuitIdentity(circuit);
  const clean=!!committed && committed.identity===identity && committed.prediction===JSON.stringify(values);
  const predictionValid=!!d&&validPrediction(d.prediction.labels,values,d.prediction.kind==='distribution');
  const base=d?`/api/challenges/${encodeURIComponent(d.id)}`:'';
  useEffect(()=>{
    let active=true;
    onReady(false,false);
    async function fetchActivity(){
      const number=module ? Number(module.replace(/^module-/,'')) : undefined;
      if(number!==undefined&&(!Number.isInteger(number)||number<1))throw new Error('Invalid module context. Return to the lesson and open its activity.');
      let key=id;
      if(!key){
        const list=await apiFetch('/api/challenges');
        key=list.activities.find((a:{moduleId:number})=>a.moduleId===number)?.id;
        if(!key)throw new Error('No activity exists for this module.');
      }
      const detail:ActivityDetail=await apiFetch(`/api/challenges/${encodeURIComponent(key)}${number?`?module=${number}`:''}`);
      if(!active)return;
      setData(detail);
      const c=detail.workspace?.circuit??detail.definition.starterCircuit;
      load(c);
      if(detail.workspace){
        const v=Object.fromEntries(Object.entries(detail.workspace.prediction).map(([k,v])=>[k,String(v)]));
        setValues(v);
        setCommitted({revision:detail.workspace.revision,identity:circuitIdentity(c),prediction:JSON.stringify(v)});
        setRan(!!detail.workspace.execution);
        setComparison(detail.workspace.comparison);
        if(detail.workspace.execution)onResult(detail.workspace.execution.simulation);
      }
      onReady(true,detail.definition.kind==='conceptual');
    }
    fetchActivity().catch(e=>{if(active)setError(e.message)});
    return ()=>{active=false};
  },[id,module,load,onResult,onReady]);

  async function action(work:()=>Promise<void>){
    if(guard.current)return;
    guard.current=true;setBusy(true);onBusy(true);setError('');
    try{await work()}catch(e){setError(e instanceof Error?e.message:'Activity unavailable. Try again.')}
    finally{guard.current=false;setBusy(false);onBusy(false)}
  }
  async function refresh(){
    if(!d)return;
    const next:ActivityDetail=await apiFetch(`${base}?module=${d.moduleId}`);
    setData(next);
  }
  async function commit(){
    if(!d||!predictionValid)return;
    await action(async()=>{
      const revision=crypto.randomUUID();
      const prediction=Object.fromEntries(d.prediction.labels.map(k=>[k,Number(values[k])]));
      const bounded={gates:circuit.gates,num_qubits:circuit.num_qubits,classical_registers:circuit.classical_registers,shots:circuit.shots??1024,backend:'qiskit'};
      await apiFetch(`${base}/prediction`,{method:'PUT',body:JSON.stringify({module_id:d.moduleId,version:d.version,revision,circuit:bounded,prediction})});
      setCommitted({revision,identity,prediction:JSON.stringify(values)});setRan(false);setComparison(null);setFeedback(null);setSaved(false);
    });
  }
  function payload(){return {module_id:d!.moduleId,version:d!.version,revision:committed!.revision}}
  async function run(){
    if(!d||!clean){setError('Commit your prediction for the current circuit before running.');return}
    await action(async()=>{
      const result=await apiFetch(`${base}/run`,{method:'POST',body:JSON.stringify(payload())});
      onResult(result.simulation);setRan(true);setComparison(result.comparison);
    });
  }
  useImperativeHandle(ref,()=>({run}));
  async function validate(){
    if(!d||!clean)return;
    await action(async()=>{
      const response=await apiFetch(`${base}/validate`,{method:'POST',body:JSON.stringify(payload())});
      setFeedback(parseValidationResult(response.result));if(response.comparison)setComparison(response.comparison);
      await refresh();
    });
  }
  async function hint(){
    if(!d||!data)return;
    await action(async()=>{
      const response=await apiFetch(`${base}/hints`,{method:'POST',body:JSON.stringify({module_id:d.moduleId,version:d.version,index:data.hints.length+1})});
      setData({...data,hints:response.hints});
    });
  }
  function retry(reset=false){
    if(!d)return;
    if(reset){load(d.starterCircuit);if(d.kind==='conceptual')setValues({});}
    setCommitted(null);setRan(false);setComparison(null);setFeedback(null);setSaved(false);
  }
  if(!d)return <section className="panel p-6" aria-label="Learning activity">{error?<><p role="alert">{error}</p><Link className="underline" href="/login">Sign in</Link> · <Link href="/learn">Return to lessons</Link></>:<p role="status">Loading your learning activity…</p>}</section>;
  return <section className="panel p-6 space-y-4" aria-label="Learning activity" data-testid="challenge-panel">
    <p className="technical"><Link href={`/learn/${d.moduleId}`}>Module {d.moduleId} · Back to lesson</Link> · {d.kind==='conceptual'?'Conceptual activity':'Circuit activity'}</p>
    <h2 className="text-xl font-semibold">{d.title}</h2>
    <p>{d.objective}</p><p className="text-slate-300 leading-7">{d.instructions}</p>
    <p className="text-sm">Starting state: {d.initialState} {d.kind==='circuit'&&`· ${d.starterCircuit.num_qubits} qubits`}</p>
    <p role="status">{data?.completed?'✓ Activity completed':'Activity in progress'} · Best score {data?.bestScore??0} · {data?.history.length??0} submitted attempts · Hints used {data?.hints.length??0}</p>
    <fieldset disabled={busy} className="space-y-3"><legend className="font-semibold">{d.kind==='conceptual'?'Work through the example':'Predict before running'}</legend>
      <p>{d.prediction.prompt}</p>
      <div className="flex flex-wrap gap-3">{d.prediction.labels.map(label=><label className="grid gap-1 text-sm max-w-full" key={label}>{d.prediction.displayLabels[label]}<input aria-label={`Prediction ${label}`} className="rounded border border-slate-600 bg-slate-950 px-3 py-2 w-28" type="number" step="any" value={values[label]??''} onChange={e=>setValues({...values,[label]:e.target.value})}/></label>)}</div>
      {!predictionValid&&<p className="text-sm">{d.kind==='circuit'?'Enter every probability between 0 and 1, totaling 1.':'Enter every arithmetic answer.'}</p>}
      <div className="flex flex-wrap gap-3"><Button onClick={commit} disabled={!predictionValid}>Commit prediction</Button>{d.kind==='circuit'&&<Button variant="secondary" onClick={run} disabled={!clean}>Run experiment</Button>}<Button onClick={validate} disabled={!clean||(d.kind==='circuit'&&!ran)}>{d.kind==='conceptual'?'Validate reasoning':'Validate challenge'}</Button></div>
      <p className="text-sm text-slate-400">{clean?'Prediction committed and saved.':'Circuit or prediction changed: commit before running.'} {d.kind==='circuit'?'Runs are experiments; only Validate records an attempt.':'Validate records your reasoning attempt.'} Retrying has no score penalty. Each revealed hint reduces the completion score by 10.</p>
      <div className="flex flex-wrap gap-3"><Button variant="secondary" onClick={()=>retry()}>Try again</Button><Button variant="secondary" onClick={()=>retry(true)}>{d.kind==='conceptual'?'Reset answers':'Reset to starter'}</Button><Button variant="secondary" onClick={hint} disabled={!committed||(data?.hints.length??0)>=d.hintsAvailable}>Reveal next hint ({data?.hints.length??0}/{d.hintsAvailable})</Button>
      {d.kind==='circuit'&&<Button variant="secondary" disabled={!ran||!clean||saved} onClick={()=>action(async()=>{await apiFetch(`${base}/save-circuit`,{method:'POST',body:JSON.stringify(payload())});setSaved(true)})}>{saved?'Circuit saved to simulation history':'Save circuit to my history'}</Button>}</div>
    </fieldset>
    {error&&<p role="alert" className="text-amber-200">{error}</p>}
    {!!data?.hints.length&&<ol className="list-decimal pl-6">{data.hints.map(h=><li key={h}>{h}</li>)}</ol>}
    {comparison&&clean&&<PredictionComparison comparison={comparison} conceptual={d.kind==='conceptual'} labels={d.prediction.displayLabels} />}
    {comparison&&clean&&<p className="text-slate-300 leading-7">{d.reflection}</p>}
    {feedback&&clean&&<ChallengeFeedback feedback={feedback} />}

    <details><summary className="cursor-pointer">Attempt history ({data?.history.length??0})</summary><p className="text-sm">Historical submissions are preserved when you retry or reset.</p><ul>{data?.history.map(a=><li className="py-2" key={a.id}>Attempt {a.number} · {a.passed?'✓ Passed':'↻ '+a.status} · Hints {a.hintsUsed} · Score {a.score} <Button variant="secondary" disabled={busy} onClick={()=>action(async()=>{const past=await apiFetch(`${base}/attempts/${a.number}`);load(past.circuit);setValues(Object.fromEntries(Object.entries(past.prediction).map(([k,v])=>[k,String(v)])));retry()})}>Restore circuit and prediction</Button></li>)}</ul></details>
  </section>;
});
