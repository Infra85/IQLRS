import { LessonJourney, ReadingProgress, Reflections } from "../components/LessonJourney";
import Activities from "../components/Activities";
import { ListenButton, NarratorOnly } from "@/components/narration/provider";
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
export default async function ModulePage({ params }: { params: Promise<{ id: string }> }) {
  const {id} = await params;
  const lesson = getModule(Number(id));
  if (!lesson) notFound();
  const narration = moduleNarration(lesson);
  const owner = `lesson-${lesson.id}`;
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
      <NarratorOnly>
        <div className="lesson-listen">
          <ListenButton
            owner={owner}
            segments={narration}
            label="Listen to lesson"
          />
          <p>Read aloud · Includes explanations, notation, and examples.</p>
        </div>
      </NarratorOnly>
      <LessonJourney moduleId={lesson.id} key={lesson.id}>
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
          <a href="#learning-activities">Experiments and challenges</a>
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
            <ReadingProgress id="objectives" />
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
              <ReadingProgress id={`concept-${index}`} />
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

            <ReadingProgress id="example" />
          </section>
          <Activities moduleId={lesson.id} experiments={lesson.experiments} challenges={[]} />
          <Reflections />
          <Quiz moduleId={lesson.id} key={lesson.id} questions={lesson.questions} />
          <Activities moduleId={lesson.id} experiments={[]} challenges={lesson.challenges} />
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
                  ? "Preview next module"
                  : "Start an experiment"}{" "}
                →
              </Link>
            </Button>
          </div>
        </article>
      </div>
      </LessonJourney>
    </main>
  );
}
