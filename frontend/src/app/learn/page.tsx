import Link from 'next/link';
import { modules } from './modules';
import ModuleItem from './components/ModuleItem';

export default function LearnPage() {
  return (
    <main className="min-h-screen bg-gray-950 p-8 text-white">
      <h1 className="text-3xl font-bold mb-6">Quantum Computing Learning Path</h1>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {modules.map((module) => (
          <ModuleItem key={module.id} module={module} />
        ))}
      </div>
    </main>
  );
}