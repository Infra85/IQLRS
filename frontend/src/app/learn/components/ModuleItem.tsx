import Link from "next/link";
import type { Module } from "../modules";

export default function ModuleItem({ module }: { module: Module }) {
  return (
    <article className="rounded-xl border border-gray-800 bg-gray-900/60 p-6">
      <p className="text-sm font-medium text-quantum-400">Module {module.id}</p>
      <h2 className="mt-2 text-xl font-semibold">{module.title.replace(/^Module \d+ – /, "")}</h2>
      <p className="mt-3 line-clamp-3 text-sm leading-6 text-gray-400">{module.introduction}</p>
      <p className="mt-4 text-sm text-gray-500">3 sections · 3-question quiz</p>
      <Link href={`/learn/${module.id}`} className="mt-5 inline-block rounded-lg bg-quantum-600 px-4 py-2 text-sm font-medium hover:bg-quantum-700">Start module</Link>
    </article>
  );
}
