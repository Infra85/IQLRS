import Link from "next/link";
import { notFound } from "next/navigation";
import Diagram from "../components/Diagram";
import Quiz from "../components/Quiz";
import { getModule } from "../modules";

export default function ModulePage({ params }: { params: { id: string } }) {
  const module = getModule(Number(params.id));
  if (!module) notFound();
  const challengeHref = module.id === 4 ? "/builder?challenge=bell" : module.id === 6 ? "/builder?challenge=grover" : "/builder";
  return <main className="min-h-screen bg-gray-950 p-6 text-white md:p-10"><Link href="/learn" className="text-sm text-gray-400 hover:text-white">← All modules</Link><article className="mx-auto mt-6 max-w-4xl space-y-8"><header><p className="font-medium text-quantum-400">Module {module.id}</p><h1 className="mt-2 text-3xl font-bold">{module.title.replace(/^Module \d+ – /, "")}</h1><p className="mt-4 leading-7 text-gray-300">{module.introduction}</p></header><section className="rounded-xl border border-gray-800 bg-gray-900/60 p-6"><h2 className="text-xl font-semibold">Objectives</h2><p className="mt-3 leading-7 text-gray-300">{module.objectives}</p></section>{module.sections.map((section, index) => <section key={section.title} className="rounded-xl border border-gray-800 bg-gray-900/60 p-6"><h2 className="text-xl font-semibold">{section.title}</h2><p className="mt-3 leading-7 text-gray-300">{section.description}</p><Diagram label={section.diagram} index={index} /></section>)}<section className="rounded-xl border border-gray-800 bg-gray-900/60 p-6"><h2 className="text-xl font-semibold">Worked example</h2><p className="mt-3 leading-7 text-gray-300">{module.workedExample}</p><h2 className="mt-6 text-xl font-semibold">Key takeaways</h2><p className="mt-3 whitespace-pre-line leading-7 text-gray-300">{module.keyTakeaways}</p>{(module.tryInBuilder || module.id === 4) && <Link href={challengeHref} className="mt-6 inline-block rounded-lg bg-quantum-600 px-4 py-2 font-medium hover:bg-quantum-700">{module.id === 4 || module.id === 6 ? "Open learning challenge" : "Try this in the circuit builder"}</Link>}</section><Quiz questions={module.questions} /></article></main>;
}
