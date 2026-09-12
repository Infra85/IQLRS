import { ListenButton } from "@/components/narration/provider";
import { moduleNarration } from "@/lib/narration/content";
import { StateExplorer } from "@/components/state-explorer";
import Link from "next/link";
import { notFound } from "next/navigation";
import Diagram from "../components/Diagram";
import Quiz from "../components/Quiz";
import { getModule, modules } from "../modules";
import { PageHeader } from "@/components/ui/page";
import { Button } from "@/components/ui/button";
import { LearningText } from "@/components/learning-text";
export default function ModulePage({ params }: { params: { id: string } }) {
  const lesson = getModule(Number(params.id));
  if (!lesson) notFound();
  const narration = moduleNarration(lesson);
  const owner = `lesson-${lesson.id}`;
  const challengeHref =
    lesson.id === 4
      ? "/builder?challenge=bell"
      : lesson.id === 6
        ? "/builder?challenge=grover"
        : "/builder";
  return (
    <main className="page">
      <Link
        href="/learn"
        className="technical inline-block py-2 hover:text-white"
      >
        ← All modules
      </Link>
      <div id="lesson-introduction">
        <PageHeader
          eyebrow={`LEARN / MODULE ${String(lesson.id).padStart(2, "0")}`}
          title={lesson.title.replace(/^Module \d+ – /, "")}
          description={<LearningText text={lesson.introduction} />}
        />
      </div>
      <div className="lesson-listen">
        <ListenButton
          owner={owner}
          segments={narration}
          label="Listen to lesson"
        />
        <p>
          Natural AI narration · Includes explanations, notation, and examples.
        </p>
      </div>
      <div className="lesson-layout">
        <nav className="lesson-aside" aria-label="Lesson sections">
          <p className="technical mb-3">In this module</p>
          <a href="#objectives">Learning objectives</a>
          {lesson.sections.map((s, i) => (
            <a key={s.title} href={`#concept-${i}`}>
              {s.title}
            </a>
          ))}
          <a href="#example">Worked example</a>
          <a href="#knowledge-check">Knowledge check</a>
        </nav>
        <article className="lesson-content">
          {lesson.id <= 2 && <StateExplorer />}
          <section id="objectives" className="panel p-6">
            <div className="narration-section-heading">
              <p className="technical">Your objective</p>
              <ListenButton
                owner={`${owner}-objectives`}
                segments={[narration[1]]}
              />
            </div>
            <p className="leading-8 text-slate-300">
              <LearningText text={lesson.objectives} />
            </p>
          </section>
          {lesson.sections.map((section, index) => (
            <section
              id={`concept-${index}`}
              key={section.title}
              className="lesson-section"
            >
              <div className="narration-section-heading">
                <h2>{section.title}</h2>
                <ListenButton
                  owner={`${owner}-concept-${index}`}
                  segments={[narration[index + 2]]}
                />
              </div>
              <p>
                <LearningText text={section.description} />
              </p>
              <Diagram label={section.diagram} index={index} />
            </section>
          ))}
          <section id="example" className="lesson-section">
            <p className="technical !mt-0 mb-3">Put it together</p>
            <div className="narration-section-heading">
              <h2>Worked example</h2>
              <ListenButton
                owner={`${owner}-example`}
                segments={[narration[narration.length - 2]]}
              />
            </div>
            <p>
              <LearningText text={lesson.workedExample} />
            </p>
            <div id="takeaways" className="mt-8">
              <div className="narration-section-heading">
                <h2>Key takeaways</h2>
                <ListenButton
                  owner={`${owner}-takeaways`}
                  segments={[narration[narration.length - 1]]}
                />
              </div>
              <p>
                <LearningText text={lesson.keyTakeaways} />
              </p>
            </div>
            {(lesson.tryInBuilder || lesson.id === 4) && (
              <Button asChild className="mt-6">
                <Link href={challengeHref}>
                  {lesson.id === 4 || lesson.id === 6
                    ? "Open learning challenge"
                    : "Try in the circuit builder"}{" "}
                  ↗
                </Link>
              </Button>
            )}
          </section>
          <Quiz key={lesson.id} questions={lesson.questions} />
          <div className="flex flex-wrap justify-between gap-4 pt-8">
            <Button asChild variant="secondary">
              <Link href={lesson.id > 1 ? `/learn/${lesson.id - 1}` : "/learn"}>
                ← {lesson.id > 1 ? "Previous module" : "All modules"}
              </Link>
            </Button>
            <Button asChild>
              <Link
                href={
                  lesson.id < modules.length
                    ? `/learn/${lesson.id + 1}`
                    : "/builder"
                }
              >
                {lesson.id < modules.length
                  ? "Next module"
                  : "Start an experiment"}{" "}
                →
              </Link>
            </Button>
          </div>
        </article>
      </div>
    </main>
  );
}
