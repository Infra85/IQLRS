import Link from "next/link";
import { modules } from "../learn/modules";
import { PageHeader, Status } from "@/components/ui/page";
import { Button } from "@/components/ui/button";
export default function InstructorPage() {
  return (
    <main className="page">
      <PageHeader
        eyebrow="TEACHING / CURRICULUM DESK"
        title="Guide the next discovery."
        description="Review the learning sequence and choose practical exercises to pair with each concept."
      />
      <div className="mb-8">
        <Status>
          Learner analytics and assignment management are not connected in this
          version. The curriculum and guided circuit exercises below are
          available to review and share by URL.
        </Status>
      </div>
      <section className="panel overflow-hidden">
        <div className="panel-heading">
          <h2 className="section-title">Curriculum overview</h2>
          <span className="technical">{modules.length} modules</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">
              Modules, concept counts, knowledge checks, and lesson links
            </caption>
            <thead className="technical bg-white/[.02]">
              <tr>
                <th scope="col" className="p-5">
                  Module
                </th>
                <th scope="col" className="p-5">
                  Concepts
                </th>
                <th scope="col" className="p-5">
                  Questions
                </th>
                <th scope="col" className="p-5">
                  Lesson
                </th>
              </tr>
            </thead>
            <tbody>
              {modules.map((m) => (
                <tr key={m.id} className="border-t hover:bg-white/[.02]">
                  <th scope="row" className="p-5 font-normal min-w-[15rem]">
                    <span className="font-mono text-slate-500 mr-4">
                      {String(m.id).padStart(2, "0")}
                    </span>
                    {m.title.replace(/^Module \d+ – /, "")}
                  </th>
                  <td className="p-5 font-mono text-slate-400">
                    {m.sections.length}
                  </td>
                  <td className="p-5 font-mono text-slate-400">
                    {m.questions.length}
                  </td>
                  <td className="p-5">
                    <Link
                      className="auth-link whitespace-nowrap"
                      href={`/learn/${m.id}`}
                      aria-label={`Review ${m.title}`}
                    >
                      Review ↗
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="mt-10">
        <h2 className="section-title mb-5">Guided practice</h2>
        <div className="grid gap-5 sm:grid-cols-2">
          {[
            {
              title: "Prepare a Bell state",
              text: "Connect superposition and entanglement through an H → CNOT circuit.",
              key: "bell",
            },
            {
              title: "Explore Grover search",
              text: "Inspect a two-qubit circuit that amplifies the marked state |11⟩.",
              key: "grover",
            },
          ].map((ex) => (
            <div className="panel p-6" key={ex.key}>
              <p className="technical mb-3">Circuit challenge</p>
              <h3 className="text-xl">{ex.title}</h3>
              <p className="text-slate-400 text-sm leading-7 my-4">{ex.text}</p>
              <Button asChild variant="secondary">
                <Link href={`/builder?challenge=${ex.key}`}>
                  Open exercise ↗
                </Link>
              </Button>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
