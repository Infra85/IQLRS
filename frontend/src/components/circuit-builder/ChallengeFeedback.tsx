import type { Comparison, ValidationResult } from '@/lib/learning-challenges';
export function ChallengeFeedback({feedback}:{feedback:ValidationResult}){
  return <div role="status" data-testid="challenge-feedback"><h3 className="font-semibold">{feedback.passed?'✓ Success':feedback.status==='near_miss'?'↻ Near miss':feedback.status==='invalid_circuit'?'✗ Invalid circuit':'↻ Keep exploring'} · Score {feedback.score}</h3><p>{feedback.feedback.summary}</p><ul className="space-y-1">{feedback.checks.map(c=><li key={c.id}>{c.passed?'✓':'✗'} {c.message}</li>)}</ul><p className="mt-2">{feedback.feedback.explanation}</p></div>;
}
export function PredictionComparison({comparison,conceptual,labels}:{comparison:Comparison;conceptual:boolean;labels?:Record<string,string>}){
  const outcomes = [...new Set([
    ...Object.keys(comparison.prediction),
    ...Object.keys(comparison.ideal ?? {}),
    ...Object.keys(comparison.actual),
  ])];
  return <div aria-label="Prediction comparison"><h3 className="font-semibold">Prediction vs result</h3><p>{comparison.matches?(conceptual?'✓ Your arithmetic agrees with the worked example.':'✓ Prediction matches this circuit’s behavior.'):'↻ The result differs from your prediction. Compare the values and reconsider your preparation.'}</p><p className="text-sm">Compared against {comparison.basis}; tolerance {comparison.tolerance.toFixed(3)}. {!conceptual&&'Sample counts may fluctuate.'}</p><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr><th>Outcome</th><th>Prediction</th>{comparison.ideal&&<th>Ideal</th>}<th>{conceptual?'Arithmetic result':'Sampled result'}</th></tr></thead><tbody>{outcomes.map(k=><tr key={k}><th>{labels?.[k]??k}</th><td>{comparison.prediction[k]??'Not predicted'}</td>{comparison.ideal&&<td>{(comparison.ideal[k]??0).toFixed(3)}</td>}<td>{conceptual?comparison.actual[k]:(comparison.actual[k]??0).toFixed(3)}</td></tr>)}</tbody></table></div></div>;
}
