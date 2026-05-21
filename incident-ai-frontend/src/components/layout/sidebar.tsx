import { useState } from "react";
import { Plus, MessageSquare, Settings, ChevronRight, Trash2, Clock, X } from "lucide-react";
import type { ChatSession } from "@/lib/chatStorage";

interface SidebarProps {
  sessions: Omit<ChatSession, "messages">[];
  activeSessionId: string;
  onNewChat: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  onCollapse: () => void;
}

function timeAgo(ts: number): string {
  const diff  = Date.now() - ts;
  const mins  = Math.floor(diff / 60_000);
  const hours = Math.floor(diff / 3_600_000);
  const days  = Math.floor(diff / 86_400_000);
  if (mins  < 1)  return "just now";
  if (mins  < 60) return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days  < 7)  return `${days}d ago`;
  return new Date(ts).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

function groupSessions(sessions: Omit<ChatSession, "messages">[]) {
  const today     = new Date(); today.setHours(0, 0, 0, 0);
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
  const lastWeek  = new Date(today); lastWeek.setDate(today.getDate() - 7);

  const groups: { label: string; items: typeof sessions }[] = [
    { label: "Today",       items: [] },
    { label: "Yesterday",   items: [] },
    { label: "Last 7 days", items: [] },
    { label: "Older",       items: [] },
  ];

  for (const s of sessions) {
    const d = new Date(s.updatedAt); d.setHours(0, 0, 0, 0);
    if      (d >= today)     groups[0].items.push(s);
    else if (d >= yesterday) groups[1].items.push(s);
    else if (d >= lastWeek)  groups[2].items.push(s);
    else                     groups[3].items.push(s);
  }

  return groups.filter((g) => g.items.length > 0);
}

export function Sidebar({
  sessions,
  activeSessionId,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  onCollapse,
}: SidebarProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const groups = groupSessions(sessions.filter((s) => s.messageCount > 0));

  return (
    <aside
      className="relative flex w-64 flex-col overflow-hidden h-full"
      style={{
        background:  "hsl(var(--rl-ink-950))",
        borderRight: "1px solid hsl(var(--rl-ink-800))",
      }}
    >
      {/* Top gold hairline */}
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-[2px] z-10"
        style={{
          background:
            "linear-gradient(90deg, transparent 0%, hsl(var(--rl-gold-400)) 40%, hsl(var(--rl-gold-300)) 65%, transparent 100%)",
        }}
      />

      {/* ── Header ── */}
      <div className="px-5 pb-4 pt-7">
        {/* Wordmark row with collapse button */}
        <div className="mb-5 flex items-center gap-3">
          <div
            className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl"
            style={{
              background:
                "linear-gradient(145deg, hsl(var(--rl-purple-950)) 0%, hsl(var(--rl-purple-800)) 100%)",
              border:    "1px solid hsl(var(--rl-gold-400) / 0.35)",
              boxShadow: "0 2px 12px hsl(var(--rl-purple-950) / 0.6)",
            }}
          >
            <svg width="16" height="14" viewBox="0 0 16 14" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M1 11h14M1 11L2.5 4l3.5 3.5L8 1l2 6.5L13.5 4 15 11"
                stroke="hsl(43 85% 62%)"
                strokeWidth="1.5"
                strokeLinejoin="round"
                strokeLinecap="round"
              />
              <rect x="1" y="11" width="14" height="2.5" rx="0.75"
                fill="hsl(43 85% 62%)" fillOpacity="0.25"
                stroke="hsl(43 85% 62%)" strokeWidth="1" />
            </svg>
          </div>

          <div className="flex-1 min-w-0">
            <p
              className="leading-none truncate"
              style={{
                fontFamily:    "'Playfair Display', serif",
                fontSize:      "15px",
                fontWeight:    500,
                color:         "hsl(var(--rl-ink-100))",
                letterSpacing: "-0.01em",
              }}
            >
              Incident AI
            </p>
            <p className="mt-0.5 text-[10px] font-medium uppercase tracking-[0.15em]"
              style={{ color: "hsl(var(--rl-gold-400))" }}>
              Royal London
            </p>
          </div>

          {/* Collapse button inside sidebar
          <button
            onClick={onCollapse}
            className="flex-shrink-0 flex h-7 w-7 items-center justify-center rounded-lg transition-colors"
            style={{ color: "hsl(var(--rl-ink-500))" }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.color =
                "hsl(var(--rl-ink-100))")
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.color =
                "hsl(var(--rl-ink-500))")
            }
            title="Collapse sidebar"
          >
            <X size={14} strokeWidth={2} />
          </button> */}
        </div>

        {/* New Chat CTA */}
        <button
          onClick={onNewChat}
          className="group relative w-full overflow-hidden rounded-xl px-4 py-2.5 text-sm font-medium transition-all duration-200"
          style={{
            background: "hsl(var(--rl-purple-950))",
            border:     "1px solid hsl(var(--rl-gold-400) / 0.3)",
            color:      "hsl(var(--rl-ink-100))",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.borderColor =
              "hsl(var(--rl-gold-400) / 0.6)";
            (e.currentTarget as HTMLButtonElement).style.boxShadow =
              "0 0 0 1px hsl(var(--rl-gold-400) / 0.1)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.borderColor =
              "hsl(var(--rl-gold-400) / 0.3)";
            (e.currentTarget as HTMLButtonElement).style.boxShadow = "none";
          }}
        >
          <div className="flex items-center justify-center gap-2">
            <Plus size={15} strokeWidth={2} style={{ color: "hsl(var(--rl-gold-400))" }} />
            <span>New Chat</span>
          </div>
        </button>
      </div>

      {/* Divider */}
      <div className="mx-5" style={{ borderTop: "1px solid hsl(var(--rl-ink-800))" }} />

      {/* ── History ── */}
      <div className="flex-1 overflow-y-auto px-3 py-4">
        {groups.length === 0 ? (
          <div
            className="flex flex-col items-center gap-2 py-8 text-center"
            style={{ color: "hsl(var(--rl-ink-500))" }}
          >
            <Clock size={18} strokeWidth={1.5} />
            <p className="text-[11px] leading-relaxed">
              Your conversations will<br />appear here
            </p>
          </div>
        ) : (
          <div className="space-y-5">
            {groups.map((group) => (
              <div key={group.label}>
                <p
                  className="mb-2 px-2 text-[9px] font-semibold uppercase tracking-[0.15em]"
                  style={{ color: "hsl(var(--rl-ink-500))" }}
                >
                  {group.label}
                </p>
                <div className="space-y-0.5">
                  {group.items.map((session) => {
                    const isActive  = session.id === activeSessionId;
                    const isHovered = hoveredId === session.id;

                    return (
                      <div
                        key={session.id}
                        className={`sidebar-item group relative flex cursor-pointer items-start gap-2 rounded-lg px-3 py-2.5 transition-all duration-150${isActive ? " active" : ""}`}
                        style={{
                          background: isActive
                            ? "hsl(var(--rl-purple-950) / 0.7)"
                            : isHovered
                            ? "hsl(var(--rl-ink-800))"
                            : "transparent",
                          border: isActive
                            ? "1px solid hsl(var(--rl-gold-400) / 0.25)"
                            : "1px solid transparent",
                        }}
                        onClick={() => onSelectSession(session.id)}
                        onMouseEnter={() => setHoveredId(session.id)}
                        onMouseLeave={() => setHoveredId(null)}
                      >
                        <MessageSquare
                          size={13}
                          className="mt-0.5 flex-shrink-0"
                          strokeWidth={1.75}
                          style={{
                            color: isActive
                              ? "hsl(var(--rl-gold-400))"
                              : "hsl(var(--rl-ink-500))",
                          }}
                        />
                        <div className="min-w-0 flex-1">
                          <p
                            className="truncate text-xs font-medium leading-snug"
                            style={{
                              color: isActive
                                ? "hsl(var(--rl-ink-100))"
                                : "hsl(var(--rl-ink-300))",
                            }}
                          >
                            {session.title}
                          </p>
                          <p
                            className="mt-0.5 text-[10px]"
                            style={{ color: "hsl(var(--rl-ink-500))" }}
                          >
                            {timeAgo(session.updatedAt)}
                          </p>
                        </div>

                        {/* Delete on hover */}
                        {isHovered && !isActive && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onDeleteSession(session.id);
                            }}
                            className="flex-shrink-0 rounded p-0.5 transition-colors"
                            style={{ color: "hsl(var(--rl-ink-500))" }}
                            onMouseEnter={(e) =>
                              ((e.currentTarget as HTMLButtonElement).style.color =
                                "hsl(350 70% 60%)")
                            }
                            onMouseLeave={(e) =>
                              ((e.currentTarget as HTMLButtonElement).style.color =
                                "hsl(var(--rl-ink-500))")
                            }
                            title="Delete"
                          >
                            <Trash2 size={11} strokeWidth={2} />
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Footer ── */}
      <div
        className="px-3 py-3"
        style={{ borderTop: "1px solid hsl(var(--rl-ink-800))" }}
      >
        <button
          className="sidebar-item group flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-sm transition-all duration-150"
          style={{ color: "hsl(var(--rl-ink-500))" }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background =
              "hsl(var(--rl-ink-800))";
            (e.currentTarget as HTMLButtonElement).style.color =
              "hsl(var(--rl-ink-200))";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = "transparent";
            (e.currentTarget as HTMLButtonElement).style.color =
              "hsl(var(--rl-ink-500))";
          }}
        >
          <div className="flex items-center gap-2.5">
            <Settings size={14} strokeWidth={1.75} />
            <span className="text-xs font-medium">Settings</span>
          </div>
          <ChevronRight
            size={12}
            className="opacity-0 transition-opacity group-hover:opacity-40"
          />
        </button>
      </div>
    </aside>
  );
}