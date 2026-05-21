import { useState } from "react";
import { ChevronDown, Hash, ExternalLink, GitPullRequest, Code2 } from "lucide-react";
import type { SimilarIncident } from "@/types/incident";

export interface IncidentCardProps {
  incident: SimilarIncident;
}

function LinkBadge({
  href,
  icon: Icon,
  label,
  colorVar,
}: {
  href: string;
  icon: React.ElementType;
  label: string;
  colorVar: string;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      title={`Open in ${label}`}
      className="flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide transition-colors duration-100"
      style={{
        background: `${colorVar} / 0.1)`.replace("hsl(", "hsl("),
        color: colorVar,
        border: `1px solid ${colorVar.replace(")", " / 0.25)")}`,
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLAnchorElement).style.opacity = "0.8";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLAnchorElement).style.opacity = "1";
      }}
      onClick={(e) => e.stopPropagation()}
    >
      <Icon size={8} strokeWidth={2.5} />
      {label}
    </a>
  );
}

export function IncidentCard({ incident }: IncidentCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showDatafix, setShowDatafix] = useState(false);
  const scorePercent = Math.round(incident.similarity_score * 100);

  const scoreStyle =
    scorePercent >= 80
      ? { bg: "hsl(160 60% 35% / 0.15)", text: "hsl(160 60% 60%)", border: "hsl(160 60% 40% / 0.25)" }
      : scorePercent >= 60
      ? { bg: "hsl(var(--rl-gold-400) / 0.1)", text: "hsl(var(--rl-gold-400))", border: "hsl(var(--rl-gold-400) / 0.25)" }
      : { bg: "hsl(350 70% 50% / 0.1)", text: "hsl(350 70% 65%)", border: "hsl(350 70% 50% / 0.2)" };

  const priorityColor =
    incident.priority?.match(/1|critical/i)
      ? "hsl(350 70% 65%)"
      : incident.priority?.match(/2|high/i)
      ? "hsl(var(--rl-gold-400))"
      : "hsl(var(--rl-ink-400))";

  const hasDetails = !!(incident.description || incident.resolution_notes || incident.datafix_code);

  return (
    <div
      className="group rounded-xl p-4 transition-all duration-150"
      style={{
        background: "hsl(var(--rl-ink-900))",
        border: "1px solid hsl(var(--rl-ink-800))",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = "hsl(var(--rl-gold-400) / 0.2)";
        (e.currentTarget as HTMLDivElement).style.background = "hsl(var(--rl-ink-800))";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = "hsl(var(--rl-ink-800))";
        (e.currentTarget as HTMLDivElement).style.background = "hsl(var(--rl-ink-900))";
      }}
    >
      {/* ── Header ── */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 flex-1 items-start gap-2">
          <Hash size={12} className="mt-0.5 flex-shrink-0" strokeWidth={2}
            style={{ color: "hsl(var(--rl-ink-500))" }} />
          <div className="min-w-0 flex-1">
            {/* Number + link badges */}
            <div className="flex flex-wrap items-center gap-1.5 mb-1">
              <p
                className="text-[10px] font-medium uppercase tracking-[0.12em]"
                style={{ fontFamily: "'JetBrains Mono', monospace", color: "hsl(var(--rl-ink-500))" }}
              >
                {incident.incident_number}
              </p>

              {incident.servicenow_link && (
                <a
                  href={incident.servicenow_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  title="Open in ServiceNow"
                  className="flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide transition-opacity duration-100 hover:opacity-80"
                  style={{
                    background: "hsl(var(--rl-gold-400) / 0.1)",
                    color: "hsl(var(--rl-gold-400))",
                    border: "1px solid hsl(var(--rl-gold-400) / 0.25)",
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <ExternalLink size={8} strokeWidth={2.5} />
                  ServiceNow
                </a>
              )}

              {incident.azure_devops_link && (
                <a
                  href={incident.azure_devops_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  title="Open Datafix PR in Azure DevOps"
                  className="flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide transition-opacity duration-100 hover:opacity-80"
                  style={{
                    background: "hsl(210 80% 55% / 0.12)",
                    color: "hsl(210 80% 70%)",
                    border: "1px solid hsl(210 80% 55% / 0.25)",
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <GitPullRequest size={8} strokeWidth={2.5} />
                  DevOps PR
                </a>
              )}

              {incident.datafix_code && (
                <span
                  className="flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide"
                  style={{
                    background: "hsl(270 60% 60% / 0.1)",
                    color: "hsl(270 60% 75%)",
                    border: "1px solid hsl(270 60% 60% / 0.2)",
                  }}
                >
                  <Code2 size={8} strokeWidth={2.5} />
                  Datafix
                </span>
              )}
            </div>

            <p className="line-clamp-2 text-sm font-medium leading-snug"
              style={{ color: "hsl(var(--rl-ink-200))" }}>
              {incident.short_description}
            </p>
          </div>
        </div>

        {/* Score badge */}
        <div
          className="flex-shrink-0 rounded-lg border px-2.5 py-1 text-xs font-semibold"
          style={scoreStyle}
        >
          {scorePercent}%
        </div>
      </div>

      {/* ── Metadata row ── */}
      <div
        className="mt-3.5 grid grid-cols-3 gap-3 pt-3.5"
        style={{ borderTop: "1px solid hsl(var(--rl-ink-800))" }}
      >
        {[
          { label: "Priority", value: incident.priority, color: priorityColor },
          { label: "Category", value: incident.category, color: "hsl(var(--rl-ink-300))" },
          { label: "Group",    value: incident.assignment_group, color: "hsl(var(--rl-ink-300))" },
        ].map(({ label, value, color }) => (
          <div key={label}>
            <p className="mb-0.5 text-[9px] font-semibold uppercase tracking-[0.1em]"
              style={{ color: "hsl(var(--rl-ink-600))" }}>
              {label}
            </p>
            <p className="truncate text-xs font-medium" style={{ color }}>
              {value || "—"}
            </p>
          </div>
        ))}
      </div>

      {/* ── Expandable section ── */}
      {hasDetails && (
        <>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="mt-3 flex items-center gap-1 text-[10px] font-medium uppercase tracking-wide transition-colors duration-100"
            style={{ color: "hsl(var(--rl-ink-500))" }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.color = "hsl(var(--rl-ink-300))")
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.color = "hsl(var(--rl-ink-500))")
            }
          >
            <ChevronDown
              size={11}
              strokeWidth={2}
              style={{
                transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)",
                transition: "transform 150ms ease",
              }}
            />
            {isExpanded ? "Hide details" : "Show details"}
          </button>

          {isExpanded && (
            <div className="mt-3 space-y-3">
              {incident.description && (
                <div>
                  <p className="mb-1 text-[9px] font-semibold uppercase tracking-[0.1em]"
                    style={{ color: "hsl(var(--rl-ink-600))" }}>
                    Description
                  </p>
                  <p className="text-xs leading-relaxed" style={{ color: "hsl(var(--rl-ink-400))" }}>
                    {incident.description}
                  </p>
                </div>
              )}

              {incident.resolution_notes && (
                <div
                  className="rounded-lg p-3"
                  style={{
                    background: "hsl(160 60% 35% / 0.08)",
                    border: "1px solid hsl(160 60% 40% / 0.15)",
                  }}
                >
                  <p className="mb-1 text-[9px] font-semibold uppercase tracking-[0.1em]"
                    style={{ color: "hsl(160 60% 55%)" }}>
                    Resolution Notes
                  </p>
                  <p className="text-xs leading-relaxed" style={{ color: "hsl(var(--rl-ink-300))" }}>
                    {incident.resolution_notes}
                  </p>
                </div>
              )}

              {incident.datafix_code && (
                <div
                  className="rounded-lg overflow-hidden"
                  style={{ border: "1px solid hsl(270 60% 60% / 0.2)" }}
                >
                  <button
                    onClick={() => setShowDatafix(!showDatafix)}
                    className="w-full flex items-center justify-between px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.1em] transition-colors duration-100"
                    style={{
                      background: "hsl(270 60% 60% / 0.08)",
                      color: "hsl(270 60% 75%)",
                    }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.background = "hsl(270 60% 60% / 0.14)";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.background = "hsl(270 60% 60% / 0.08)";
                    }}
                  >
                    <span className="flex items-center gap-1.5">
                      <Code2 size={10} strokeWidth={2} />
                      Datafix Code
                    </span>
                    <ChevronDown
                      size={10}
                      strokeWidth={2}
                      style={{
                        transform: showDatafix ? "rotate(180deg)" : "rotate(0deg)",
                        transition: "transform 150ms ease",
                      }}
                    />
                  </button>

                  {showDatafix && (
                    <pre
                      className="overflow-x-auto p-3 text-[10px] leading-relaxed"
                      style={{
                        fontFamily: "'JetBrains Mono', monospace",
                        color: "hsl(var(--rl-ink-300))",
                        background: "hsl(var(--rl-ink-950))",
                        maxHeight: "240px",
                        overflowY: "auto",
                      }}
                    >
                      {incident.datafix_code}
                    </pre>
                  )}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}