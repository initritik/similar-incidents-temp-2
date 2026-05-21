import type {
  AgentProgressEvent,
  ChatRequest,
  ChatResponse,
  SearchIncidentsRequest,
  SearchIncidentsResponse,
} from "@/types/incident";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "https://similar-incidents-temp-2.onrender.com";
  // "http://localhost:8000"; // for local development

// How long to wait for the full SSE stream to complete.
// Render free-tier backends cold-start in up to 60 s, so 120 s is safe.
const SSE_TIMEOUT_MS = 120_000;

type ApiErrorPayload = { detail?: string; message?: string };

async function parseJsonResponse<T>(response: Response): Promise<T> {
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new Error("Backend returned an invalid JSON response.");
  }
  if (!response.ok) {
    const err = payload as ApiErrorPayload;
    throw new Error(
      err.detail ?? err.message ?? `Backend request failed with status ${response.status}.`
    );
  }
  return payload as T;
}

async function postJson<TResponse, TRequest>(
  path: string,
  body: TRequest
): Promise<TResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return parseJsonResponse<TResponse>(response);
  } catch (error) {
    if (error instanceof Error) throw error;
    throw new Error("Network request failed.");
  }
}

export async function searchIncidents(
  request: SearchIncidentsRequest
): Promise<SearchIncidentsResponse> {
  const response = await postJson<SearchIncidentsResponse, SearchIncidentsRequest>(
    "/search/similar-incidents",
    request
  );
  if (!response || !Array.isArray(response.results)) {
    throw new Error("Invalid search response from backend.");
  }
  return response;
}

/**
 * Chat with incidents via SSE streaming.
 *
 * Calls onProgress for each agent step event.
 * Resolves with the final ChatResponse when the 'result' event arrives.
 * Rejects on 'error' events, network failure, stream ending without a result,
 * or after SSE_TIMEOUT_MS.
 */
export function chatWithIncidentsStream(
  request: ChatRequest,
  onProgress: (event: AgentProgressEvent) => void
): Promise<ChatResponse> {
  return new Promise((resolve, reject) => {
    // ── Overall timeout guard ───────────────────────────────────────────────
    // Prevents the Promise hanging forever if the backend dies silently or
    // the Render free-tier cold start exceeds our patience.
    const timeoutId = setTimeout(() => {
      reject(
        new Error(
          "Request timed out. The backend may be starting up — please try again in a moment."
        )
      );
    }, SSE_TIMEOUT_MS);

    let settled = false;

    function safeResolve(value: ChatResponse) {
      if (settled) return;
      settled = true;
      clearTimeout(timeoutId);
      resolve(value);
    }

    function safeReject(err: Error) {
      if (settled) return;
      settled = true;
      clearTimeout(timeoutId);
      reject(err);
    }

    fetch(`${API_BASE_URL}/chat/incidents`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    })
      .then((response) => {
        if (!response.ok || !response.body) {
          return response
            .json()
            .then((err: ApiErrorPayload) => {
              safeReject(
                new Error(err.detail ?? err.message ?? `HTTP ${response.status}`)
              );
            })
            .catch(() => {
              safeReject(new Error(`HTTP ${response.status} — backend returned no body.`));
            });
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        function parseSseChunk(chunk: string) {
          const messages = (buffer + chunk).split("\n\n");
          buffer = messages.pop() ?? "";

          for (const msg of messages) {
            let eventType = "message";
            let dataLine = "";

            for (const line of msg.split("\n")) {
              if (line.startsWith("event: ")) eventType = line.slice(7).trim();
              if (line.startsWith("data: "))  dataLine  = line.slice(6).trim();
            }

            if (!dataLine) continue;

            try {
              const parsed = JSON.parse(dataLine);
              if (eventType === "progress") {
                onProgress(parsed as AgentProgressEvent);
              } else if (eventType === "result") {
                safeResolve(parsed as ChatResponse);
              } else if (eventType === "error") {
                safeReject(
                  new Error((parsed as { message: string }).message ?? "Agent error")
                );
              }
            } catch {
              // Malformed SSE data — ignore
            }
          }
        }

        function pump(): Promise<void> {
          return reader.read().then(({ done, value }) => {
            if (done) {
              // Stream ended — if we never got a 'result' event, the Promise
              // would hang forever. Reject with a clear message instead.
              safeReject(
                new Error(
                  "The response stream ended unexpectedly. " +
                    "The backend may have crashed or timed out."
                )
              );
              return;
            }
            parseSseChunk(decoder.decode(value, { stream: true }));
            return pump();
          });
        }

        pump().catch((err: unknown) =>
          safeReject(err instanceof Error ? err : new Error("Stream read error"))
        );
      })
      .catch((err: unknown) =>
        safeReject(err instanceof Error ? err : new Error("Network request failed."))
      );
  });
}

/** Legacy non-streaming chat — kept for backwards compat with search page. */
export async function chatWithIncidents(request: ChatRequest): Promise<ChatResponse> {
  return chatWithIncidentsStream(request, () => {});
}