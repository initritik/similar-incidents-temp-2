import { useEffect, useRef } from "react";
import type { ChatMessageProps } from "./ChatMessage";
import { ChatMessage } from "./ChatMessage";
import { Search, AlertCircle, Shield, Wifi } from "lucide-react";

export interface ChatContainerProps {
  messages:            ChatMessageProps[];
  isLoading?:          boolean;
  onSuggestionClick?:  (label: string) => void;
}

const SUGGESTIONS = [
  { icon: Wifi,        label: "VPN authentication failures",  sub: "Find similar VPN incidents" },
  { icon: AlertCircle, label: "Email delivery problems",       sub: "Explore email incidents" },
  { icon: Search,      label: "Database connection timeout",   sub: "Trace outage patterns" },
  { icon: Shield,      label: "SSL certificate errors",        sub: "Certificate-related issues" },
];

export function ChatContainer({
  messages,
  isLoading = false,
  onSuggestionClick,
}: ChatContainerProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div
      className="flex flex-1 flex-col overflow-y-auto px-4 py-6 sm:px-6 lg:px-12 lg:py-8"
      style={{ background: "hsl(var(--rl-ink-950))" }}
    >
      {/* ── Empty state ── */}
      {messages.length === 0 && !isLoading && (
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-2xl space-y-6 sm:space-y-8 text-center px-2">

            {/* Hero crest */}
            <div className="flex flex-col items-center gap-4 sm:gap-5">
              <div
                className="flex h-14 w-14 sm:h-16 sm:w-16 items-center justify-center rounded-2xl"
                style={{
                  background:
                    "linear-gradient(145deg, hsl(var(--rl-purple-950)) 0%, hsl(var(--rl-purple-800)) 100%)",
                  border:    "1px solid hsl(var(--rl-gold-400) / 0.4)",
                  boxShadow: "0 8px 32px hsl(var(--rl-purple-950) / 0.5), 0 0 0 1px hsl(var(--rl-gold-400) / 0.08)",
                }}
              >
                <svg width="22" height="19" viewBox="0 0 22 19" fill="none">
                  <path
                    d="M2 15h18M2 15L4 5l5 5L11 1l2 9 5-5 2 10"
                    stroke="hsl(43 85% 62%)"
                    strokeWidth="1.75"
                    strokeLinejoin="round"
                    strokeLinecap="round"
                  />
                  <rect x="2" y="15" width="18" height="3.5" rx="1"
                    fill="hsl(43 85% 62%)" fillOpacity="0.2"
                    stroke="hsl(43 85% 62%)" strokeWidth="1.25" />
                </svg>
              </div>

              <div>
                <h2
                  className="tracking-tight"
                  style={{
                    fontFamily:    "'Playfair Display', serif",
                    fontSize:      "clamp(20px, 5vw, 26px)",
                    fontWeight:    500,
                    color:         "hsl(var(--rl-ink-100))",
                    letterSpacing: "-0.02em",
                  }}
                >
                  Incident AI Assistant
                </h2>
                <p
                  className="mt-1 text-[11px] font-medium uppercase tracking-[0.18em]"
                  style={{ color: "hsl(var(--rl-gold-400))" }}
                >
                  Royal London
                </p>
                <p
                  className="mt-3 text-sm"
                  style={{ color: "hsl(var(--rl-ink-400))" }}
                >
                  Describe an incident, paste a link, or ask about past events
                </p>
              </div>
            </div>

            {/* Decorative rule */}
            <div className="relative flex items-center gap-4">
              <div className="flex-1" style={{ borderTop: "1px solid hsl(var(--rl-ink-800))" }} />
              <span
                className="text-[10px] font-semibold uppercase tracking-[0.14em]"
                style={{ color: "hsl(var(--rl-ink-600))" }}
              >
                Try asking
              </span>
              <div className="flex-1" style={{ borderTop: "1px solid hsl(var(--rl-ink-800))" }} />
            </div>

            {/* Clickable suggestion grid */}
            <div className="grid gap-2.5 sm:gap-3 grid-cols-1 sm:grid-cols-2">
              {SUGGESTIONS.map(({ icon: Icon, label, sub }, i) => (
                <button
                  key={i}
                  onClick={() => onSuggestionClick?.(label)}
                  className="group relative overflow-hidden rounded-xl p-3.5 sm:p-4 text-left transition-all duration-200 active:scale-[0.98]"
                  style={{
                    background: "hsl(var(--rl-ink-900))",
                    border:     "1px solid hsl(var(--rl-ink-800))",
                    cursor:     "pointer",
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLButtonElement).style.borderColor =
                      "hsl(var(--rl-gold-400) / 0.4)";
                    (e.currentTarget as HTMLButtonElement).style.background =
                      "hsl(var(--rl-ink-800))";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLButtonElement).style.borderColor =
                      "hsl(var(--rl-ink-800))";
                    (e.currentTarget as HTMLButtonElement).style.background =
                      "hsl(var(--rl-ink-900))";
                  }}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className="mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg"
                      style={{ background: "hsl(var(--rl-purple-950) / 0.6)" }}
                    >
                      <Icon size={13} strokeWidth={2}
                        style={{ color: "hsl(var(--rl-gold-400))" }} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate" style={{ color: "hsl(var(--rl-ink-200))" }}>
                        &ldquo;{label}&rdquo;
                      </p>
                      <p className="mt-0.5 text-xs" style={{ color: "hsl(var(--rl-ink-500))" }}>
                        {sub}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Messages ── */}
      {messages.length > 0 && (
        <div className="space-y-6 sm:space-y-7">
          {messages.map((msg, i) => (
            <ChatMessage key={i} role={msg.role} content={msg.content} />
          ))}
        </div>
      )}

      {/* ── Loading indicator ── */}
      {isLoading && (
        <div className="mt-6 sm:mt-7 flex animate-fade-up items-start gap-3">
          <div
            className="mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg"
            style={{
              background:
                "linear-gradient(145deg, hsl(var(--rl-purple-950)) 0%, hsl(var(--rl-purple-800)) 100%)",
              border:    "1px solid hsl(var(--rl-gold-400) / 0.35)",
              boxShadow: "0 2px 8px hsl(var(--rl-purple-950) / 0.5)",
            }}
          >
            <svg width="12" height="11" viewBox="0 0 12 11" fill="none">
              <path d="M1 8.5h10M1 8.5L2 3.5l2.5 2.5L6 1l1.5 5L10 3.5l1 5"
                stroke="hsl(43 85% 62%)" strokeWidth="1.25"
                strokeLinejoin="round" strokeLinecap="round" />
            </svg>
          </div>
          <div
            className="rounded-xl px-4 py-3"
            style={{
              background: "hsl(var(--rl-ink-900))",
              border:     "1px solid hsl(var(--rl-ink-800))",
            }}
          >
            <div className="flex items-center gap-1.5">
              {[0, 0.18, 0.36].map((delay, i) => (
                <span
                  key={i}
                  className="inline-block h-1.5 w-1.5 rounded-full"
                  style={{
                    background: "hsl(var(--rl-gold-400))",
                    animation:  `typing-dot 1.2s ease-in-out ${delay}s infinite`,
                  }}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      <div ref={endRef} />
    </div>
  );
}