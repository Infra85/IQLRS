import type { Module } from "../../app/learn/modules";
import type { NarrationSegment } from "./text";

/** Uses the same catalogue values that render each lesson; no second transcript. */
export function moduleNarration(lesson: Module): NarrationSegment[] {
  return [
    {
      id: "introduction",
      title: lesson.title,
      text: lesson.introduction,
      targetId: "lesson-introduction",
    },
    {
      id: "objectives",
      title: "Learning objectives",
      text: lesson.objectives,
      targetId: "objectives",
    },
    ...lesson.sections.map((section, index) => ({
      id: `concept-${index}`,
      title: section.title,
      text: `${section.description}\n\n${section.diagram}`,
      targetId: `concept-${index}`,
    })),
    {
      id: "example",
      title: "Worked example",
      text: lesson.workedExample,
      targetId: "example",
    },
    {
      id: "takeaways",
      title: "Key takeaways",
      text: lesson.keyTakeaways,
      targetId: "takeaways",
    },
  ];
}
