"use client";

import { useToastStore } from "@zhenhang/realtime";

export function ToastCenter() {
  const messages = useToastStore((s) => s.messages);
  const remove = useToastStore((s) => s.remove);
  return (
    <div
      role="status"
      aria-live="polite"
      className="pointer-events-none fixed right-4 top-4 z-50 space-y-2"
    >
      {messages.map((msg) => (
        <div
          key={msg.id}
          className="pointer-events-auto w-80 rounded border bg-white p-3 text-sm shadow dark:border-zinc-700 dark:bg-zinc-900"
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="font-medium">{msg.title}</div>
              {msg.description ? <div className="text-zinc-500">{msg.description}</div> : null}
            </div>
            <button
              type="button"
              className="text-xs"
              aria-label="关闭提示"
              onClick={() => remove(msg.id)}
            >
              关闭
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
