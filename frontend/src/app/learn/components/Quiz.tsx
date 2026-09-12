"use client";
import { ListenButton } from "@/components/narration/provider";
import { useState } from "react";
import type { Question } from "../modules";
import { Button } from "@/components/ui/button";
import { Status } from "@/components/ui/page";
export default function Quiz({ questions }: { questions: Question[] }) {
  const [answers, setAnswers] = useState<(number | null)[]>(() =>
    questions.map(() => null),
  );
  const [submitted, setSubmitted] = useState(false);
  const score = answers.reduce<number>(
    (total, answer, index) =>
      total + (answer === questions[index].answerIndex ? 1 : 0),
    0,
  );
  return (
    <section id="knowledge-check" className="lesson-section">
      <p className="technical !mt-0 mb-3">
        Knowledge check / {questions.length} questions
      </p>
      <h2>Test your understanding.</h2>
      <div className="my-8 space-y-8">
        {questions.map((question, qi) => (
          <fieldset key={question.question} id={`quiz-question-${qi}`}>
            <legend className="mb-3 leading-7">
              {qi + 1}. {question.question}
            </legend>
            <div className="mb-3">
              <ListenButton
                owner={`quiz-question-${qi}`}
                segments={[
                  {
                    id: `quiz-${qi}`,
                    title: `Question ${qi + 1}`,
                    text: `${question.question}\n${question.options.map((option, i) => `${String.fromCharCode(65 + i)}. ${option}`).join("\n")}`,
                    targetId: `quiz-question-${qi}`,
                  },
                ]}
                label="Listen to question"
              />
            </div>
            <div className="grid gap-2">
              {question.options.map((option, oi) => (
                <label
                  key={option}
                  className={`quiz-option ${submitted ? (oi === question.answerIndex ? "correct" : answers[qi] === oi ? "incorrect" : "") : ""}`}
                >
                  <input
                    type="radio"
                    name={`question-${qi}`}
                    checked={answers[qi] === oi}
                    disabled={submitted}
                    onChange={() =>
                      setAnswers((current) =>
                        current.map((answer, index) =>
                          index === qi ? oi : answer,
                        ),
                      )
                    }
                  />
                  <span>
                    <span className="font-mono text-slate-400 mr-2">
                      {String.fromCharCode(65 + oi)}.
                    </span>
                    {option}
                  </span>
                </label>
              ))}
            </div>
            {submitted && (
              <div id={`quiz-feedback-${qi}`}>
                <p className="!mt-3 text-sm">
                  <strong>
                    {answers[qi] === question.answerIndex
                      ? "Correct."
                      : "Not quite."}
                  </strong>{" "}
                  {question.explanation}
                </p>
                <ListenButton
                  className="mt-3"
                  owner={`quiz-feedback-${qi}`}
                  segments={[
                    {
                      id: `feedback-${qi}`,
                      title: `Question ${qi + 1} feedback`,
                      text: `${answers[qi] === question.answerIndex ? "Correct." : "Not quite."} ${question.explanation || ""}`,
                      targetId: `quiz-feedback-${qi}`,
                    },
                  ]}
                  label="Listen to explanation"
                />
              </div>
            )}
          </fieldset>
        ))}
      </div>
      {submitted ? (
        <div className="space-y-4">
          <Status kind={score === questions.length ? "success" : "info"}>
            Your score: {score} / {questions.length}.{" "}
            {score === questions.length
              ? "Ready for the next concept."
              : "Review the explanations above, then try again."}
          </Status>
          <ListenButton
            owner="quiz-score"
            label="Listen to feedback"
            segments={[
              {
                id: "quiz-score",
                title: "Quiz result",
                text: `Your score: ${score} out of ${questions.length}. ${score === questions.length ? "Ready for the next concept." : "Review the explanations above, then try again."}`,
                targetId: "knowledge-check",
              },
            ]}
          />
          <Button
            variant="secondary"
            onClick={() => {
              setAnswers(questions.map(() => null));
              setSubmitted(false);
            }}
          >
            Retry quiz
          </Button>
        </div>
      ) : (
        <div className="flex flex-wrap items-center gap-4">
          <Button
            disabled={answers.some((a) => a === null)}
            onClick={() => setSubmitted(true)}
          >
            Check answers
          </Button>
          <span className="text-sm text-slate-400">
            {answers.filter((a) => a !== null).length} of {questions.length}{" "}
            answered
          </span>
        </div>
      )}
    </section>
  );
}
