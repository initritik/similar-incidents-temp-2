import { useState, useEffect, useCallback, useRef } from "react";
import { ChatContainer } from "@/components/chat/ChatContainer";
import { ChatInput } from "@/components/chat/ChatInput";
import type { SendPayload } from "@/components/chat/ChatInput";
import { AgentLog } from "@/components/chat/AgentLog";
import type { ChatMessageProps } from "@/components/chat/ChatMessage";
import { IncidentsPanel } from "@/components/incidents/IncidentsPanel";
import { chatWithIncidentsStream } from "@/services/incidentApi";
import type {
  AgentProgressEvent,
  ChatRequest,
  ChatResponse,
  SimilarIncident,
} from "@/types/incident";
import {
  loadMessagesFromSession,
  saveMessagesToSession,
  clearChatStorage,
} from "@/lib/chatStorage";
import { Trash2 } from "lucide-react";

// ── Stored assistant response shape ─────────────────────────────────────────

interface AssistantResponse {
  answerText: string;
  incidents: SimilarIncident[];
  recommendedResolution: string;
  recommendedDatafix: string | null;
}

// ── Chat page props ──────────────────────────────────────────────────────────

interface ChatPageProps {
  sessionId: string;
  onSessionUpdated?: () => void;
}

// ── AssistantContent: renders answer + agent log + incidents panel ────────────

function AssistantContent({
  answerText,
  incidents,
  recommendedResolution,
  recommendedDatafix,
  agentEvents,
  isStreaming,
}: {
  answerText: string;
  incidents: SimilarIncident[];
  recommendedResolution: string;
  recommendedDatafix: string | null;
  agentEvents?: AgentProgressEvent[];
  isStreaming?: boolean;
}) {
  return (
    <div>
      {/* Answer text */}
      {answerText && (
        <p className="text-sm leading-relaxed" style={{ color: "hsl(var(--rl-ink-200))" }}>
          {answerText}
        </p>
      )}

      {/* Live agent operation log */}
      {agentEvents && agentEvents.length > 0 && (
        <AgentLog events={agentEvents} isStreaming={isStreaming ?? false} />
      )}

      {/* Incidents + resolution + datafix panel */}
      {incidents && incidents.length > 0 && (
        <IncidentsPanel
          incidents={incidents}
          recommendedResolution={recommendedResolution}
          recommendedDatafix={recommendedDatafix}
        />
      )}
    </div>
  );
}

// ── Build ChatRequest from user input ────────────────────────────────────────

function buildChatRequest(payload: SendPayload, topK = 5): ChatRequest {
  switch (payload.searchType) {
    case "incident_number":
      return { incident_number: payload.text, top_k: topK };
    case "incident_link":
      return { incident_link: payload.text, top_k: topK };
    case "description":
    default:
      return { user_query: payload.text, top_k: topK };
  }
}

// ── ChatPage ─────────────────────────────────────────────────────────────────

export function ChatPage({ sessionId, onSessionUpdated }: ChatPageProps) {
  const [messages,           setMessages]           = useState<ChatMessageProps[]>([]);
  const [assistantResponses, setAssistantResponses] = useState<AssistantResponse[]>([]);
  const [isLoading,          setIsLoading]          = useState(false);

  // Live streaming state — only relevant for the in-progress message
  const [streamingEvents, setStreamingEvents] = useState<AgentProgressEvent[]>([]);
  const streamingEventsRef = useRef<AgentProgressEvent[]>([]);

  // ── Restore session ─────────────────────────────────────────────────────

  useEffect(() => {
    const stored = loadMessagesFromSession(sessionId);
    if (stored.length === 0) {
      setMessages([]);
      setAssistantResponses([]);
      return;
    }

    const reconstructed: ChatMessageProps[] = [];
    const responses: AssistantResponse[]    = [];

    stored.forEach((msg) => {
      if (msg.role === "user") {
        reconstructed.push({ role: "user", content: msg.content as string });
      } else {
        const data = msg.content as AssistantResponse;
        responses.push(data);
        reconstructed.push({
          role: "assistant",
          content: (
            <AssistantContent
              answerText={data.answerText}
              incidents={data.incidents}
              recommendedResolution={data.recommendedResolution}
              recommendedDatafix={data.recommendedDatafix}
            />
          ),
        });
      }
    });

    setMessages(reconstructed);
    setAssistantResponses(responses);
  }, [sessionId]);

  // ── Clear chat ──────────────────────────────────────────────────────────

  const handleClearChat = () => {
    setMessages([]);
    setAssistantResponses([]);
    setStreamingEvents([]);
    streamingEventsRef.current = [];
    clearChatStorage();
    onSessionUpdated?.();
  };

  // ── Send message with SSE streaming ────────────────────────────────────

  const handleSendMessage = useCallback(
    async (payload: SendPayload) => {
      // Display the raw user text in the chat bubble
      const userMsg: ChatMessageProps = { role: "user", content: payload.text };
      const newMessages = [...messages, userMsg];

      // Reset streaming log
      streamingEventsRef.current = [];
      setStreamingEvents([]);
      setIsLoading(true);

      // Add a placeholder assistant message that shows only the live agent log
      const placeholderContent = (
        <AssistantContent
          answerText=""
          incidents={[]}
          recommendedResolution=""
          recommendedDatafix={null}
          agentEvents={[]}
          isStreaming={true}
        />
      );
      setMessages([...newMessages, { role: "assistant", content: placeholderContent }]);

      // Build the correct request shape based on the search type
      const request: ChatRequest = buildChatRequest(payload);

      // ── Progress callback — called for each SSE progress event ──────────
      const onProgress = (event: AgentProgressEvent) => {
        streamingEventsRef.current = [...streamingEventsRef.current, event];
        const snapshot = [...streamingEventsRef.current];

        // Update the placeholder assistant message with the latest events
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: (
              <AssistantContent
                answerText=""
                incidents={[]}
                recommendedResolution=""
                recommendedDatafix={null}
                agentEvents={snapshot}
                isStreaming={true}
              />
            ),
          };
          return updated;
        });

        setStreamingEvents(snapshot);
      };

      try {
        const response: ChatResponse = await chatWithIncidentsStream(request, onProgress);
        const finalEvents = [...streamingEventsRef.current];

        const responseData: AssistantResponse = {
          answerText:            response.answer,
          incidents:             response.results || [],
          recommendedResolution: response.recommended_resolution || "",
          recommendedDatafix:    response.recommended_datafix ?? null,
        };

        // Replace placeholder with the full response (events still shown)
        const assistantMessage: ChatMessageProps = {
          role: "assistant",
          content: (
            <AssistantContent
              answerText={response.answer}
              incidents={response.results || []}
              recommendedResolution={response.recommended_resolution || ""}
              recommendedDatafix={response.recommended_datafix ?? null}
              agentEvents={finalEvents}
              isStreaming={false}
            />
          ),
        };

        const updatedMessages  = [...newMessages, assistantMessage];
        const updatedResponses = [...assistantResponses, responseData];

        setMessages(updatedMessages);
        setAssistantResponses(updatedResponses);
        setStreamingEvents([]);

        saveMessagesToSession(sessionId, updatedMessages, updatedResponses);
        onSessionUpdated?.();
      } catch (err) {
        const msg = err instanceof Error ? err.message : "An error occurred";
        console.error("Chat SSE error:", msg);

        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: (
              <div
                className="rounded-xl border px-4 py-3 text-sm"
                style={{
                  background:  "hsl(350 70% 55% / 0.08)",
                  borderColor: "hsl(350 70% 55% / 0.2)",
                  color:       "hsl(350 70% 72%)",
                }}
              >
                <p className="font-semibold">Something went wrong</p>
                <p className="mt-1 text-xs opacity-80">{msg}</p>
              </div>
            ),
          };
          return updated;
        });
      } finally {
        setIsLoading(false);
        streamingEventsRef.current = [];
      }
    },
    [messages, assistantResponses, sessionId, onSessionUpdated]
  );

  // ── Render ──────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Toolbar */}
      {/* <div
        className="flex items-center h-16 justify-between pl-12 pr-4 sm:pl-14 sm:pr-6 lg:px-12 py-3.5"
        style={{
          borderBottom:   "1px solid hsl(var(--rl-ink-800))",
          background:     "hsl(var(--rl-ink-950) / 0.85)",
          backdropFilter: "blur(8px)",
        }}
      >
        <div />
        <button
          onClick={handleClearChat}
          disabled={messages.length === 0}
          className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-30"
          style={{ color: "hsl(var(--rl-ink-500))" }}
          onMouseEnter={(e) => {
            if (!(e.currentTarget as HTMLButtonElement).disabled) {
              (e.currentTarget as HTMLButtonElement).style.background = "hsl(var(--rl-ink-800))";
              (e.currentTarget as HTMLButtonElement).style.color = "hsl(var(--rl-ink-200))";
            }
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = "transparent";
            (e.currentTarget as HTMLButtonElement).style.color = "hsl(var(--rl-ink-500))";
          }}
        >
          <Trash2 size={12} strokeWidth={2} />
          Clear
        </button>
      </div> */}

      {/* Messages */}
      <ChatContainer
        messages={messages}
        isLoading={false}
        onSuggestionClick={(label) =>
          handleSendMessage({ text: label, searchType: "description" })
        }
      />

      {/* Input */}
      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
}