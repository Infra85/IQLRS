"use client";
import Link from "next/link";
import { useLessonJourney } from "./LessonJourney";
import { statusLabel } from "@/lib/lesson-journey";

type Activity = {id: string; title: string; learnerAction: string; type: string};
export default function Activities({moduleId, experiments, challenges}: {moduleId: number; experiments: Activity[]; challenges: Activity[]}) {
  const context = useLessonJourney();
  return <section id={experiments.length ? "learning-activities" : "lesson-challenges"} className="panel p-6 space-y-4">
    <h2 className="text-xl font-semibold">{experiments.length ? "Learn by experimenting" : "Apply what you learned"}</h2>
    <p>Predict, explore, compare, then validate. Activity completion is recorded separately from the quiz.</p>
    {[...experiments, ...challenges].map(activity => {
      const step = context?.journey?.steps.find(s => s.id === activity.id);
      return <article key={activity.id}>
        <h3 className="font-semibold">{experiments.length ? "Experiment" : "Challenge"}: {activity.title}</h3>
        {step && <p>{statusLabel[step.status]}</p>}
        <p className="text-slate-300 my-2">{activity.learnerAction}</p>
        <Link className="ui-button button-secondary" href={`/builder?module=${moduleId}&challenge=${activity.id}`} onClick={event => {
          if (context?.signedIn && context.journey && !event.ctrlKey && !event.metaKey && !event.shiftKey && event.button === 0) {
            event.preventDefault();
            void context.update(activity.id, 'start', true);
          }
        }}>{activity.type === 'conceptual' ? 'Open conceptual activity' : 'Open learning activity'} ↗</Link>
      </article>;
    })}
  </section>;
}
