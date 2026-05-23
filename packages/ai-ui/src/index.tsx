import * as React from "react";

export function AIPanel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded border bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900">
      <h3 className="mb-2 text-sm font-semibold">{title}</h3>
      {children}
    </section>
  );
}

export function AIChat({ messages }: { messages: Array<{ role: "user" | "assistant"; content: string }> }) {
  return (
    <div className="max-h-56 space-y-2 overflow-auto text-sm">
      {messages.map((m, idx) => (
        <div key={idx} className="rounded border p-2">
          <span className="mr-1 font-medium">{m.role}:</span>
          <span>{m.content}</span>
        </div>
      ))}
    </div>
  );
}

export function AIContextInjection({ context }: { context: Record<string, string> }) {
  return (
    <div className="rounded border p-2 text-xs">
      {Object.entries(context).map(([k, v]) => (
        <div key={k}>
          <span className="font-medium">{k}</span>: {v}
        </div>
      ))}
    </div>
  );
}

export function RetrievalPreview({ chunks }: { chunks: Array<{ id: string; score: number; text: string }> }) {
  return (
    <div className="space-y-2 text-xs">
      {chunks.map((c) => (
        <div key={c.id} className="rounded border p-2">
          <div className="mb-1 font-medium">score: {c.score.toFixed(3)}</div>
          <div className="line-clamp-3">{c.text}</div>
        </div>
      ))}
    </div>
  );
}
