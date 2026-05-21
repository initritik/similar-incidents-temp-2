import type { SimilarIncident } from "@/types/incident";

// ─── Storage keys ────────────────────────────────────────────────────────────
const SESSIONS_INDEX_KEY = "rl_ai_sessions_index";   // ordered list of session IDs
const SESSION_PREFIX     = "rl_ai_session_";          // prefix for individual session data
const ACTIVE_SESSION_KEY = "rl_ai_active_session";    // which session is currently open

// ─── Types ───────────────────────────────────────────────────────────────────

export interface StoredMessage {
  role: "user" | "assistant";
  userText?:   string;
  answerText?: string;
  recommendedResolution?: string;
  recommendedDatafix?: string | null;
  incidents?:  SimilarIncident[];
  timestamp:   number;
}

export interface ChatSession {
  id:          string;
  title:       string;   // auto-generated from first user message
  createdAt:   number;
  updatedAt:   number;
  messageCount: number;
  preview:     string;   // first user message snippet
  messages:    StoredMessage[];
}

export interface ReconstructedMessage {
  role: "user" | "assistant";
  content: string | { answerText: string; incidents: SimilarIncident[]; recommendedResolution: string; recommendedDatafix: string | null };
  timestamp: number;
}

// ─── ID helpers ──────────────────────────────────────────────────────────────

function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

function truncate(text: string, maxLen = 50): string {
  if (!text) return "Untitled chat";
  return text.length <= maxLen ? text : text.slice(0, maxLen - 1) + "…";
}

// ─── Sessions index ───────────────────────────────────────────────────────────

function getSessionsIndex(): string[] {
  try {
    const raw = localStorage.getItem(SESSIONS_INDEX_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveSessionsIndex(ids: string[]): void {
  try {
    localStorage.setItem(SESSIONS_INDEX_KEY, JSON.stringify(ids));
  } catch {}
}

// ─── Individual session CRUD ──────────────────────────────────────────────────

export function getSession(id: string): ChatSession | null {
  try {
    const raw = localStorage.getItem(SESSION_PREFIX + id);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveSession(session: ChatSession): void {
  try {
    localStorage.setItem(SESSION_PREFIX + session.id, JSON.stringify(session));
  } catch (e) {
    console.error("Failed to save session:", e);
  }
}

function removeSession(id: string): void {
  try {
    localStorage.removeItem(SESSION_PREFIX + id);
  } catch {}
}

// ─── Active session tracking ──────────────────────────────────────────────────

/**
 * Returns the active session ID stored in sessionStorage (tab-scoped).
 * Each new browser tab gets a fresh session because sessionStorage is not
 * shared across tabs.
 */
export function getActiveSessionId(): string | null {
  try {
    return sessionStorage.getItem(ACTIVE_SESSION_KEY);
  } catch {
    return null;
  }
}

export function setActiveSessionId(id: string): void {
  try {
    sessionStorage.setItem(ACTIVE_SESSION_KEY, id);
  } catch {}
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Create a brand-new empty session, register it in the index, and set it as
 * the active session for this tab.  Returns the new session ID.
 */
export function createNewSession(): string {
  const id = generateSessionId();
  const session: ChatSession = {
    id,
    title:        "New conversation",
    createdAt:    Date.now(),
    updatedAt:    Date.now(),
    messageCount: 0,
    preview:      "",
    messages:     [],
  };
  saveSession(session);

  const index = getSessionsIndex();
  // Prepend so newest is first
  saveSessionsIndex([id, ...index]);
  setActiveSessionId(id);
  return id;
}

/**
 * Persist messages to the given session.  Also updates the title and preview
 * from the first user message if not already set.
 */
export function saveMessagesToSession(
  sessionId: string,
  messages: Array<{ role: "user" | "assistant"; content: string | any }>,
  assistantData?: Array<{ answerText: string; incidents: SimilarIncident[]; recommendedResolution?: string; recommendedDatafix?: string | null }>,
): void {
  try {
    const existing = getSession(sessionId);
    if (!existing) return;

    const stored: StoredMessage[] = [];
    let assistantIdx = 0;

    messages.forEach((msg) => {
      if (msg.role === "user") {
        stored.push({
          role:      "user",
          userText:  msg.content as string,
          timestamp: Date.now(),
        });
      } else {
        const data = assistantData?.[assistantIdx];
        stored.push({
          role:       "assistant",
          answerText: data?.answerText ?? "",
          recommendedResolution: data?.recommendedResolution ?? "",
          recommendedDatafix: data?.recommendedDatafix ?? null,
          incidents:  data?.incidents ?? [],
          timestamp:  Date.now(),
        });
        assistantIdx++;
      }
    });

    // Auto-title from first user message
    const firstUser = stored.find((m) => m.role === "user");
    const title     = firstUser ? truncate(firstUser.userText ?? "", 48) : existing.title;
    const preview   = firstUser ? truncate(firstUser.userText ?? "", 80) : existing.preview;

    const updated: ChatSession = {
      ...existing,
      title,
      preview,
      messages:     stored,
      messageCount: stored.length,
      updatedAt:    Date.now(),
    };

    saveSession(updated);

    // Keep this session at the top of the index
    const index = getSessionsIndex().filter((sid) => sid !== sessionId);
    saveSessionsIndex([sessionId, ...index]);
  } catch (e) {
    console.error("saveMessagesToSession error:", e);
  }
}

/**
 * Load messages from a session and return them in ReconstructedMessage format.
 */
export function loadMessagesFromSession(sessionId: string): ReconstructedMessage[] {
  try {
    const session = getSession(sessionId);
    if (!session) return [];

    return session.messages.map((msg) => ({
      role:      msg.role,
      content:
        msg.role === "user"
          ? (msg.userText ?? "")
          : { answerText: msg.answerText ?? "", incidents: msg.incidents ?? [], recommendedResolution: msg.recommendedResolution ?? "", recommendedDatafix: msg.recommendedDatafix ?? null },
      timestamp: msg.timestamp,
    }));
  } catch {
    return [];
  }
}

/**
 * Return all sessions sorted newest-first, without their message payloads
 * (to keep the sidebar lightweight).
 */
export function getAllSessions(): Omit<ChatSession, "messages">[] {
  const index = getSessionsIndex();
  const sessions: Omit<ChatSession, "messages">[] = [];

  for (const id of index) {
    const session = getSession(id);
    if (session) {
      const { messages: _messages, ...meta } = session;
      sessions.push(meta);
    }
  }

  return sessions;
}

/**
 * Delete a session by ID.
 */
export function deleteSession(sessionId: string): void {
  removeSession(sessionId);
  const index = getSessionsIndex().filter((id) => id !== sessionId);
  saveSessionsIndex(index);
}

// ─── Legacy compatibility shims ───────────────────────────────────────────────
// These keep backward-compatibility in case other parts of the codebase import
// the old functions.  They delegate to the new session system.

/** @deprecated Use saveMessagesToSession with an explicit session ID instead. */
export function saveChatToStorage(
  messages: Array<{ role: "user" | "assistant"; content: string | any }>,
  assistantData?: Array<{ answerText: string; incidents: SimilarIncident[]; recommendedResolution?: string; recommendedDatafix?: string | null }>,
): void {
  const id = getActiveSessionId();
  if (id) saveMessagesToSession(id, messages, assistantData);
}

/** @deprecated Use loadMessagesFromSession with an explicit session ID instead. */
export function loadChatFromStorage(): ReconstructedMessage[] {
  const id = getActiveSessionId();
  return id ? loadMessagesFromSession(id) : [];
}

/** @deprecated Use deleteSession instead. */
export function clearChatStorage(): void {
  const id = getActiveSessionId();
  if (id) {
    // Only clear messages, keep the session in history
    const session = getSession(id);
    if (session) {
      saveSession({ ...session, messages: [], messageCount: 0, title: "New conversation", preview: "" });
    }
  }
}