'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiFetch } from '@/lib/api';
type Activity={id:string;title:string;learnerAction:string;type:string};
export default function Activities({moduleId,experiments,challenges}:{moduleId:number;experiments:Activity[];challenges:Activity[]}){
  const [completed,setCompleted]=useState<string[]>([]);
  useEffect(()=>{let active=true;apiFetch('/api/challenges').then(data=>{if(active)setCompleted(data.activities.filter((a:{completed:boolean})=>a.completed).map((a:{id:string})=>a.id))}).catch(()=>{});return()=>{active=false}},[]);
  return <section id="learning-activities" className="panel p-6 space-y-4"><h2 className="text-xl font-semibold">Learn by experimenting</h2><p>Predict, explore, compare, then validate. Activity completion is recorded separately from the quiz.</p>{[['Experiment',experiments],['Challenge',challenges]].map(([kind,items])=><div key={kind as string} className="space-y-4">{(items as Activity[]).map(a=><article key={a.id}><h3 className="font-semibold">{kind as string}: {a.title} {completed.includes(a.id)&&<span>✓ Completed</span>}</h3><p className="text-slate-300 my-2">{a.learnerAction}</p><Link className="ui-button button-secondary" href={`/builder?module=${moduleId}&challenge=${a.id}`}>{a.type==='conceptual'?'Open conceptual activity':'Open learning activity'} ↗</Link></article>)}</div>)}</section>
}
