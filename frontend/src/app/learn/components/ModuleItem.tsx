import { ListenButton } from "@/components/narration/provider";
import { LearningText } from "@/components/learning-text";
import Link from "next/link";
import type { Module } from "../modules";

export default function ModuleItem({
  module,
  index,
}: {
  module: Module;
  index: number;
}) {
  const title = module.title.replace(/^Module \d+ – /, "");
  return (
    <article className="module-item" id={`module-${module.id}`}>
      <div className="module-number">0{module.id}</div>
      <div className="module-main">
        <p className="module-kind">
          {index < 4 ? "FOUNDATIONS" : "ALGORITHMS + SYSTEMS"}
        </p>
        <h2>{title}</h2>
        <p>
          <LearningText text={module.introduction} />
        </p>
      </div>
      <div className="module-meta">
        <ListenButton
          owner={`module-intro-${module.id}`}
          segments={[
            {
              id: `intro-${module.id}`,
              title,
              text: module.introduction,
              targetId: `module-${module.id}`,
            },
          ]}
          label="Listen"
        />
        <span>{String(module.sections.length).padStart(2, "0")} CONCEPTS</span>
        <span>QUIZ / {String(module.questions.length).padStart(2, "0")}</span>
        <Link href={`/learn/${module.id}`}>
          Open <b>↗</b>
        </Link>
      </div>
    </article>
  );
}
