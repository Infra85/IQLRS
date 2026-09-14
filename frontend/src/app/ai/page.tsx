"use client";
import { useEffect, useState } from "react";
import { PageHeader, Status } from "@/components/ui/page";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";

type Message = {role: string; content: string};
type Conversation = {id: string; title: string};
export default function TutorPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!localStorage.getItem("access_token")) { window.location.href = "/login"; return; }
    setBusy(true);
    apiFetch("/api/ai/conversations").then(setConversations).catch(e => setError(e.message)).finally(() => setBusy(false));
  }, []);
  async function open(id: string) {
    setBusy(true); setError("");
    try { const history = await apiFetch(`/api/ai/conversations/${id}`); setMessages(history); setConversationId(id); }
    catch(e) { setError(e instanceof Error ? e.message : "Unable to load conversation."); }
    finally { setBusy(false); }
  }
  async function send(event: React.FormEvent) {
    event.preventDefault();
    if (busy || !input.trim()) return;
    setBusy(true); setError("");
    const question = input.trim();
    try {
      const response = await apiFetch("/api/ai/chat", {method: "POST", body: JSON.stringify({message: question, conversation_id: conversationId})});
      setMessages(current => [...current, {role: "user", content: question}, {role: "assistant", content: response.reply}]);
      setConversationId(response.conversation_id); setInput("");
      if (!conversationId) setConversations(current => [{id: response.conversation_id, title: question.slice(0,100)}, ...current]);
    } catch(e) { setError(e instanceof Error ? e.message : "Unable to send. Please retry."); }
    finally { setBusy(false); }
  }
  return <main className="page">
    <PageHeader eyebrow="LEARN / AI TUTOR" title="Explore your quantum questions." description="Ask for an explanation, work through a concept, or discuss a circuit. AI answers can contain mistakes; check important results." />
    <div className="grid gap-6 lg:grid-cols-[16rem_minmax(0,1fr)]">
      <aside className="panel p-5 space-y-4">
        <Button variant="secondary" disabled={busy} onClick={() => {setConversationId(null); setMessages([]); setError(""); setInput("");}}>New conversation</Button>
        <nav aria-label="Conversations" className="grid gap-3">{conversations.map(c => <button key={c.id} disabled={busy} onClick={() => open(c.id)} aria-current={conversationId === c.id ? "page" : undefined} className="text-left text-sm break-words text-slate-300 hover:text-white">{c.title}</button>)}</nav>
      </aside>
      <section className="panel p-6 space-y-6" aria-label="AI conversation">
        <div role="log" aria-live="polite" className="space-y-5 max-h-[60vh] overflow-y-auto">
          {!messages.length && <p className="text-slate-400">Start with a question, such as “How does a Hadamard gate create superposition?”</p>}
          {messages.map((m, i) => <article key={i}><p className="technical mb-2">{m.role === "user" ? "You" : "IQLRS tutor"}</p><p className="whitespace-pre-wrap break-words leading-7">{m.content}</p></article>)}
        </div>
        {busy && <Status kind="info">Working…</Status>}
        {error && <Status kind="error">{error}</Status>}
        <form onSubmit={send} className="space-y-4">
          <label htmlFor="question" className="technical block">Your question</label>
          <textarea id="question" className="ui-input w-full min-h-28" value={input} maxLength={4000} onChange={e => setInput(e.target.value)} disabled={busy} required />
          <Button type="submit" disabled={busy || !input.trim()}>Send question ↗</Button>
        </form>
      </section>
    </div>
  </main>;
}
