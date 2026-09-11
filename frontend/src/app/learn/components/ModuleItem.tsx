import Link from "next/link";
import type { Module } from "../modules";

export default function ModuleItem({ module, index }: { module: Module; index: number }) {
  const title = module.title.replace(/^Module \d+ – /, "");
  return <article className="module-item"><div className="module-number">0{module.id}</div><div className="module-main"><p className="module-kind">{index < 4 ? "FOUNDATIONS" : "ALGORITHMS + SYSTEMS"}</p><h2>{title}</h2><p>{module.introduction}</p></div><div className="module-meta"><span>03 CONCEPTS</span><span>QUIZ / 03</span><Link href={`/learn/${module.id}`}>Open <b>↗</b></Link></div></article>;
}
