import type { ReactNode } from "react";

export type MessageRole = "user" | "assistant";

export interface ChatMessageProps {
  role:    MessageRole;
  content: string | ReactNode;
}

function CrownIcon() {
  return (
    <svg width="12" height="11" viewBox="0 0 12 11" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M1 8.5h10M1 8.5L2 3.5l2.5 2.5L6 1l1.5 5L10 3.5l1 5"
        stroke="hsl(43 85% 62%)"
        strokeWidth="1.25"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <rect
        x="1" y="8.5" width="10" height="2" rx="0.5"
        fill="hsl(43 85% 62%)"
        fillOpacity="0.3"
        stroke="hsl(43 85% 62%)"
        strokeWidth="0.75"
      />
    </svg>
  );
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  const isUser = role === "user";

  if (isUser) {
    return (
      <div className="flex animate-fade-up justify-end">
        <div
          className="relative max-w-[72%] rounded-2xl rounded-br-md px-4 py-3 text-sm leading-relaxed text-white"
          style={{
            background:
              "linear-gradient(135deg, hsl(var(--rl-purple-950)) 0%, hsl(var(--rl-purple-800)) 100%)",
            border:     "1px solid hsl(var(--rl-gold-400) / 0.25)",
            boxShadow:  "0 4px 20px hsl(var(--rl-purple-950) / 0.4), 0 1px 3px hsl(0 0% 0% / 0.2)",
          }}
        >
          {typeof content === "string" ? (
            <p className="leading-relaxed">{content}</p>
          ) : (
            content
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex animate-fade-up items-start gap-3">
      {/* Crown avatar */}
      <div
        className="mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg"
        style={{
          background:
            "linear-gradient(145deg, hsl(var(--rl-purple-950)) 0%, hsl(var(--rl-purple-800)) 100%)",
          border:    "1px solid hsl(var(--rl-gold-400) / 0.35)",
          boxShadow: "0 2px 8px hsl(var(--rl-purple-950) / 0.5)",
        }}
      >
        <CrownIcon />
      </div>

      <div className="max-w-[85%] space-y-1.5">
        <p
          className="text-[10px] font-semibold uppercase tracking-[0.12em]"
          style={{ color: "hsl(var(--rl-gold-400) / 0.75)" }}
        >
          Assistant
        </p>
        <div
          className="text-sm leading-relaxed"
          style={{ color: "hsl(var(--rl-ink-200))" }}
        >
          {typeof content === "string" ? (
            <p className="leading-relaxed">{content}</p>
          ) : (
            content
          )}
        </div>
      </div>
    </div>
  );
}