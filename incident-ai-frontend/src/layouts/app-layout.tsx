import type { ReactNode } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import type { ChatSession } from "@/lib/chatStorage";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { cn } from "@/lib/utils";

type AppLayoutProps = {
  children: ReactNode;
  sessions: Omit<ChatSession, "messages">[];
  activeSessionId: string;
  onNewChat: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  sidebarCollapsed: boolean;
  onToggleSidebar: () => void;
};

export function AppLayout({
  children,
  sessions,
  activeSessionId,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  sidebarCollapsed,
  onToggleSidebar,
}: AppLayoutProps) {
  return (
    <div
      className="flex h-screen overflow-hidden text-foreground relative"
      style={{ background: "hsl(var(--surface-0))" }}
    >
      {/* Mobile overlay backdrop */}
      {!sidebarCollapsed && (
        <div
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={onToggleSidebar}
        />
      )}

      {/* Sidebar — slides in/out on mobile, collapses width on desktop */}
      <div
        className={`
          fixed lg:relative z-30 lg:z-auto
          h-full flex-shrink-0
          transition-all duration-300 ease-in-out
          ${sidebarCollapsed
            ? "-translate-x-full lg:translate-x-0 lg:w-0 lg:overflow-hidden"
            : "translate-x-0 w-64"
          }
        `}
      >
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onNewChat={onNewChat}
          onSelectSession={onSelectSession}
          onDeleteSession={onDeleteSession}
          onCollapse={onToggleSidebar}
        />
      </div>

      {/* Main content */}
      <main className="flex flex-1 flex-col overflow-hidden min-w-0">
        {/* Toggle button — always visible */}
        
        <button
          onClick={onToggleSidebar}
          className={cn("absolute top-6 z-40 flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-150 ", sidebarCollapsed ? "left-4" : "left-[200px]")}
          style={{
            background: "hsl(var(--rl-ink-900))",
            border: "1px solid hsl(var(--rl-ink-700))",
            color: "hsl(var(--rl-ink-400))",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background =
              "hsl(var(--rl-ink-800))";
            (e.currentTarget as HTMLButtonElement).style.color =
              "hsl(var(--rl-ink-100))";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background =
              "hsl(var(--rl-ink-900))";
            (e.currentTarget as HTMLButtonElement).style.color =
              "hsl(var(--rl-ink-400))";
          }}
          title={sidebarCollapsed ? "Open sidebar" : "Close sidebar"}
        >
          {sidebarCollapsed ? (
            <PanelLeftOpen size={15} strokeWidth={1.75} />
          ) : (
            <PanelLeftClose size={15} strokeWidth={1.75} />
          )}
        </button>

        {children}
      </main>
    </div>
  );
}