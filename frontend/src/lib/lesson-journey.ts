export type StepStatus = 'not_started' | 'in_progress' | 'completed' | 'retry_needed';
export type JourneyStep = {
  id: string; title: string; kind: 'section' | 'experiment' | 'reflection' | 'quiz' | 'challenge';
  href: string; status: StepStatus; activityId?: string; explanation?: string;
};
export type Journey = {
  moduleId: number; title: string; steps: JourneyStep[]; status: StepStatus;
  completedSteps: number; totalSteps: number; completionPct: number;
  resume: JourneyStep | null; next: JourneyStep | null;
  prerequisites: number[]; pendingPrerequisites: number[]; nextModule: number | null;
  updatedAt: string | null;
};
export const statusLabel: Record<StepStatus, string> = {
  not_started: '○ Not started', in_progress: '→ In progress', completed: '✓ Completed', retry_needed: '↻ Retry needed',
};
export function returnStep(journey: Journey, activity: string): JourneyStep | null {
  const index = journey.steps.findIndex(s => s.id === activity);
  if (index < 0) return journey.next;
  if (journey.steps[index].status !== 'completed') return journey.steps.slice(0, index).reverse().find(s => s.kind === 'section') ?? journey.next;
  return journey.steps.slice(index + 1).find(s => s.status !== 'completed') ?? journey.next;
}
export function resumeModule(modules: Journey[]): Journey | undefined {
  const available = modules.filter(m => m.status !== 'completed' && !m.pendingPrerequisites.length);
  return available.filter(m => m.updatedAt).sort((a,b) => b.updatedAt!.localeCompare(a.updatedAt!))[0] ?? available[0];
}
