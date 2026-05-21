/**
 * AgentLog — live operation log shown while the agent is working.
 *
 * Mimics the Claude Code "what's happening" panel: each agent step appears
 * as it arrives over SSE, with a spinner on the current step and a checkmark
 * or cross when done.
 */
import { useEffect, useRef } from "react";
import { CheckCircle2, Circle, AlertCircle, Wrench, Loader2 } from "lucide-react";
import type { AgentProgressEvent } from "@/types/incident";

export interface AgentLogProps {
  events: AgentProgressEvent[];
  isStreaming: boolean;
}

function StepIcon({ type, isLast, isStreaming }: {
  type: AgentProgressEvent["type"];
  isLast: boolean;
  isStreaming: boolean;
}) {
  if (type === "error") {
    return <AlertCircle size={13} strokeWidth={2} style={{ color: "hsl(350 70% 65%)", flexShrink: 0 }} />;
  }
  if (type === "result") {
    return <CheckCircle2 size={13} strokeWidth={2} style={{ color: "hsl(160 60% 55%)", flexShrink: 0 }} />;
  }
  if (type === "step_done") {
    return <CheckCircle2 size={13} strokeWidth={2} style={{ color: "hsl(160 60% 55%)", flexShrink: 0 }} />;
  }
  if (type === "tool_call") {
    return <Wrench size={13} strokeWidth={2} style={{ color: "hsl(210 80% 70%)", flexShrink: 0 }} />;
  }
  // step_start
  if (isLast && isStreaming) {
    return (
      <Loader2
        size={13}
        strokeWidth={2}
        className="animate-spin"
        style={{ color: "hsl(var(--rl-gold-400))", flexShrink: 0 }}
      />
    );
  }
  return <Circle size={13} strokeWidth={2} style={{ color: "hsl(var(--rl-ink-600))", flexShrink: 0 }} />;
}

function labelColor(type: AgentProgressEvent["type"]): string {
  switch (type) {
    case "step_done": return "hsl(var(--rl-ink-300))";
    case "result":    return "hsl(160 60% 60%)";
    case "error":     return "hsl(350 70% 65%)";
    case "tool_call": return "hsl(210 80% 70%)";
    default:          return "hsl(var(--rl-ink-200))";
  }
}

export function AgentLog({ events, isStreaming }: AgentLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  if (events.length === 0) return null;

  return (
    <div
      className="mt-3 overflow-hidden rounded-xl"
      style={{
        background: "hsl(var(--rl-ink-950))",
        border: "1px solid hsl(var(--rl-ink-800))",
      }}
    >
      {/* Header */}
      <div
        className="flex items-center gap-2 px-3 py-2"
        style={{
          borderBottom: "1px solid hsl(var(--rl-ink-800))",
          background: "hsl(var(--rl-ink-900))",
        }}
      >
        {isStreaming ? (
          <Loader2
            size={11}
            strokeWidth={2}
            className="animate-spin"
            style={{ color: "hsl(var(--rl-gold-400))" }}
          />
        ) : (
          <CheckCircle2 size={11} strokeWidth={2} style={{ color: "hsl(160 60% 55%)" }} />
        )}
        <p
          className="text-[9px] font-semibold uppercase tracking-[0.14em]"
          style={{ color: "hsl(var(--rl-ink-500))" }}
        >
          {isStreaming ? "Agent working…" : "Agent complete"}
        </p>
        <span
          className="ml-auto text-[9px] font-medium"
          style={{ color: "hsl(var(--rl-ink-600))" }}
        >
          {events.length} step{events.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Event list */}
      <div className="space-y-0 max-h-52 overflow-y-auto">
        {events.map((ev, i) => {
          const isLast = i === events.length - 1;
          return (
            <div
              key={i}
              className="flex items-start gap-2.5 px-3 py-2"
              style={{
                borderBottom:
                  i < events.length - 1
                    ? "1px solid hsl(var(--rl-ink-900))"
                    : "none",
                background:
                  isLast && isStreaming
                    ? "hsl(var(--rl-gold-400) / 0.03)"
                    : "transparent",
              }}
            >
              <div className="mt-0.5">
                <StepIcon type={ev.type} isLast={isLast} isStreaming={isStreaming} />
              </div>
              <div className="min-w-0 flex-1">
                <p
                  className="text-xs font-medium leading-snug"
                  style={{ color: labelColor(ev.type) }}
                >
                  {ev.label}
                </p>
                {ev.detail && (
                  <p
                    className="mt-0.5 truncate text-[10px] leading-snug"
                    style={{ color: "hsl(var(--rl-ink-600))" }}
                  >
                    {ev.detail}
                  </p>
                )}
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}