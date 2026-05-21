import { useState, useEffect, useCallback } from "react";
import { AppLayout } from "@/layouts/app-layout";
import { ChatPage } from "@/pages/chat-page";
import {
  createNewSession,
  getAllSessions,
  deleteSession,
  type ChatSession,
} from "@/lib/chatStorage";

export function useMediaQuery(query: string) {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);

    // Set initial value
    setMatches(media.matches);

    // Listener
    const listener = () => {
      setMatches(media.matches);
    };

    media.addEventListener("change", listener);

    return () => {
      media.removeEventListener("change", listener);
    };
  }, [query]);

  return matches;
}


export default function App() {
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [sessions, setSessions] = useState<Omit<ChatSession, "messages">[]>([]);

  const isMobile = useMediaQuery("(max-width: 767px)");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  

  // On every page load (including browser refresh), always start a FRESH new
  // session. The previous session was already persisted to localStorage, so it
  // will appear in the chat history sidebar automatically.
  useEffect(() => {
      setSidebarCollapsed(isMobile);
  },[isMobile]);
  useEffect(() => {
    const id = createNewSession();
    setActiveSessionId(id);
    setSessions(getAllSessions());

  }, [isMobile]);

  const handleNewChat = useCallback(() => {
    const id = createNewSession();
    setActiveSessionId(id);
    setSessions(getAllSessions());
  }, []);

  const handleSelectSession = useCallback((id: string) => {
    setActiveSessionId(id);
    setSessions(getAllSessions());
  }, []);

  const handleDeleteSession = useCallback(
    (id: string) => {
      deleteSession(id);
      const remaining = getAllSessions();
      setSessions(remaining);
      if (id === activeSessionId) {
        if (remaining.length > 0) {
          handleSelectSession(remaining[0].id);
        } else {
          handleNewChat();
        }
      }
    },
    [activeSessionId, handleNewChat, handleSelectSession]
  );

  const refreshSessions = useCallback(() => {
    setSessions(getAllSessions());
  }, []);

  if (!activeSessionId) return null;

  return (
    <AppLayout
      sessions={sessions}
      activeSessionId={activeSessionId}
      onNewChat={handleNewChat}
      onSelectSession={handleSelectSession}
      onDeleteSession={handleDeleteSession}
      sidebarCollapsed={sidebarCollapsed}
      onToggleSidebar={() => setSidebarCollapsed((c) => !c)}
    >
      <ChatPage
        key={activeSessionId}
        sessionId={activeSessionId}
        onSessionUpdated={refreshSessions}
      />
    </AppLayout>
  );
}