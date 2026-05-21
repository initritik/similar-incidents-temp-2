/**
 * IncidentsPanel — shows similar incidents plus the agent's recommended
 * resolution and optional datafix code in tabbed panels below the cards.
 */
import { useState } from "react";
import { Layers, ShieldCheck, Code2, GitPullRequest } from "lucide-react";
import type { SimilarIncident } from "@/types/incident";
import { IncidentCard } from "./IncidentCard";

export interface IncidentsPanelProps {
  incidents: SimilarIncident[];
  recommendedResolution?: string;
  recommendedDatafix?: string | null;
}

type Tab = "incidents" | "resolution" | "datafix";

function TabButton({
  active,
  onClick,
  icon: Icon,
  label,
  badge,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ElementType;
  label: string;
  badge?: string;
}) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 px-3 py-2.5 text-[10px] font-semibold uppercase tracking-[0.1em] transition-all duration-150 relative"
      style={{
        color: active ? "hsl(var(--rl-gold-400))" : "hsl(var(--rl-ink-500))",
        borderBottom: active
          ? "2px solid hsl(var(--rl-gold-400))"
          : "2px solid transparent",
        background: "transparent",
      }}
      onMouseEnter={(e) => {
        if (!active)
          (e.currentTarget as HTMLButtonElement).style.color = "hsl(var(--rl-ink-300))";
      }}
      onMouseLeave={(e) => {
        if (!active)
          (e.currentTarget as HTMLButtonElement).style.color = "hsl(var(--rl-ink-500))";
      }}
    >
      <Icon size={11} strokeWidth={2} />
      {label}
      {badge && (
        <span
          className="rounded px-1.5 py-0.5 text-[9px] font-bold"
          style={{
            background: active
              ? "hsl(var(--rl-gold-400) / 0.15)"
              : "hsl(var(--rl-ink-800))",
            color: active ? "hsl(var(--rl-gold-400))" : "hsl(var(--rl-ink-500))",
          }}
        >
          {badge}
        </span>
      )}
    </button>
  );
}

export function IncidentsPanel({
  incidents,
  recommendedResolution,
  recommendedDatafix,
}: IncidentsPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>("incidents");

  if (!incidents || incidents.length === 0) return null;

  const avgScore = (
    incidents.reduce((sum, inc) => sum + inc.similarity_score, 0) / incidents.length
  ).toFixed(2);

  const hasResolution = !!recommendedResolution?.trim();
  const hasDatafix    = !!recommendedDatafix?.trim();

  // Count how many incidents have Azure DevOps PRs
  const prCount = incidents.filter((i) => i.azure_devops_link).length;

  return (
    <div
      className="mt-4 overflow-hidden rounded-2xl"
      style={{
        background: "hsl(var(--rl-ink-950))",
        border: "1px solid hsl(var(--rl-ink-800))",
      }}
    >
      {/* ── Panel header ── */}
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{
          background: "hsl(var(--rl-purple-950) / 0.4)",
          borderBottom: "1px solid hsl(var(--rl-ink-800))",
        }}
      >
        <div className="flex items-center gap-2.5">
          <div
            className="flex h-6 w-6 items-center justify-center rounded-md"
            style={{ background: "hsl(var(--rl-gold-400) / 0.12)" }}
          >
            <Layers size={12} strokeWidth={2} style={{ color: "hsl(var(--rl-gold-400))" }} />
          </div>
          <p
            className="text-[11px] font-semibold uppercase tracking-[0.1em]"
            style={{ color: "hsl(var(--rl-ink-400))" }}
          >
            AI Incident Analysis
          </p>
          <span
            className="rounded-md px-2 py-0.5 text-[10px] font-semibold"
            style={{
              background: "hsl(var(--rl-gold-400) / 0.12)",
              color: "hsl(var(--rl-gold-400))",
            }}
          >
            {incidents.length}
          </span>
          {prCount > 0 && (
            <span
              className="flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-semibold"
              style={{
                background: "hsl(210 80% 55% / 0.1)",
                color: "hsl(210 80% 70%)",
              }}
            >
              <GitPullRequest size={9} strokeWidth={2.5} />
              {prCount} PR{prCount !== 1 ? "s" : ""}
            </span>
          )}
        </div>
        <p className="text-[11px]" style={{ color: "hsl(var(--rl-ink-500))" }}>
          Avg match{" "}
          <span className="font-semibold" style={{ color: "hsl(var(--rl-gold-400))" }}>
            {Math.round(parseFloat(avgScore) * 100)}%
          </span>
        </p>
      </div>

      {/* ── Tabs ── */}
      <div
        className="flex items-center gap-0"
        style={{ borderBottom: "1px solid hsl(var(--rl-ink-800))" }}
      >
        <TabButton
          active={activeTab === "incidents"}
          onClick={() => setActiveTab("incidents")}
          icon={Layers}
          label="Similar Incidents"
          badge={String(incidents.length)}
        />
        {hasResolution && (
          <TabButton
            active={activeTab === "resolution"}
            onClick={() => setActiveTab("resolution")}
            icon={ShieldCheck}
            label="Recommended Resolution"
          />
        )}
        {hasDatafix && (
          <TabButton
            active={activeTab === "datafix"}
            onClick={() => setActiveTab("datafix")}
            icon={Code2}
            label="Recommended Datafix"
          />
        )}
      </div>

      {/* ── Tab content ── */}

      {/* Incidents tab */}
      {activeTab === "incidents" && (
        <div className="space-y-2 p-3">
          {incidents.map((incident, index) => (
            <IncidentCard
              key={`${incident.incident_number}-${index}`}
              incident={incident}
            />
          ))}
        </div>
      )}

      {/* Resolution tab */}
      {activeTab === "resolution" && hasResolution && (
        <div className="p-4">
          <div
            className="rounded-xl p-4"
            style={{
              background: "hsl(160 60% 35% / 0.06)",
              border: "1px solid hsl(160 60% 40% / 0.15)",
            }}
          >
            <div className="flex items-center gap-2 mb-3">
              <ShieldCheck size={14} strokeWidth={2} style={{ color: "hsl(160 60% 55%)" }} />
              <p
                className="text-[10px] font-semibold uppercase tracking-[0.12em]"
                style={{ color: "hsl(160 60% 55%)" }}
              >
                AI-Recommended Resolution Steps
              </p>
            </div>
            <div className="space-y-1.5">
              {recommendedResolution!.split("\n").filter(Boolean).map((line, i) => (
                <p
                  key={i}
                  className="text-sm leading-relaxed"
                  style={{ color: "hsl(var(--rl-ink-200))" }}
                >
                  {line}
                </p>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Datafix tab */}
      {activeTab === "datafix" && hasDatafix && (
        <div className="p-4">
          <div
            className="rounded-xl overflow-hidden"
            style={{ border: "1px solid hsl(270 60% 60% / 0.2)" }}
          >
            <div
              className="flex items-center gap-2 px-4 py-2.5"
              style={{
                background: "hsl(270 60% 60% / 0.08)",
                borderBottom: "1px solid hsl(270 60% 60% / 0.15)",
              }}
            >
              <Code2 size={13} strokeWidth={2} style={{ color: "hsl(270 60% 75%)" }} />
              <p
                className="text-[10px] font-semibold uppercase tracking-[0.12em]"
                style={{ color: "hsl(270 60% 75%)" }}
              >
                AI-Recommended Datafix Code
              </p>
              <span
                className="ml-auto text-[9px] font-medium"
                style={{ color: "hsl(var(--rl-ink-600))" }}
              >
                Adapted from similar resolved incidents
              </span>
            </div>
            <pre
              className="overflow-x-auto p-4 text-[11px] leading-relaxed"
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                color: "hsl(var(--rl-ink-200))",
                background: "hsl(var(--rl-ink-950))",
                maxHeight: "400px",
                overflowY: "auto",
              }}
            >
              {recommendedDatafix}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}