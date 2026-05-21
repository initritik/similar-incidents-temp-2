import { useState } from "react";
import { ArrowUp, Loader2, Plus, PlusIcon, X } from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────────────

export type SearchType = "description" | "incident_number" | "incident_link";

export interface SendPayload {
  text: string;
  searchType: SearchType;
}

export interface ChatInputProps {
  onSendMessage: (payload: SendPayload) => void;
  isLoading?: boolean;
}

// ── Constants ─────────────────────────────────────────────────────────────────

const SEARCH_OPTIONS: { key: SearchType; title: string; example: string, label: string }[] = [
  {
    key: "description",
    label: "Description",
    title: "Search by Description",
    example: "Payroll application returns 500 error on login",
  },
  {
    key: "incident_number",
    label: "Incident Number",
    title: "Search by Incident Number",
    example: "INC0000018",
  },
  {
    key: "incident_link",
    label: "Incident Link",
    title: "Search by Incident Link",
    example:
      "https://example.service-now.com/nav_to.do?uri=incident.do%3Fsys_id%3D82cd5d235ada5ac7a4e21ff381d392f1",
  },
];

// ── Component ─────────────────────────────────────────────────────────────────

export function ChatInput({ onSendMessage, isLoading = false }: ChatInputProps) {
  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [showSearchOptions, setShowSearchOptions] = useState(false);
  const [searchType, setSearchType] = useState<SearchType>("description");

  const canSend = input.trim().length > 0 && !isLoading;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;
    // Pass both the text AND the selected search type to the parent
    onSendMessage({ text: trimmed, searchType });
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

  const getPlaceholder = () => {
    if (isLoading) return "Waiting for response…";
    switch (searchType) {
      case "description": return "Describe the incident...";
      case "incident_number": return "Enter incident number (e.g. INC0012345)";
      case "incident_link": return "Paste incident link...";
    }
  };

  // const getSearchTypeLabel = () => {
  //   switch (searchType) {
  //     case "description": return "Description";
  //     case "incident_number": return "Incident Number";
  //     case "incident_link": return "Incident Link";
  //   }
  // };

  return (
    <div
      className="px-4 sm:px-6 lg:px-12"
      style={{
        background: "hsl(var(--rl-ink-950))",
        // borderTop: "1px solid hsl(var(--rl-ink-800))",
      }}
    >
      <form onSubmit={handleSubmit} className="mx-auto max-w-3xl ">
        {/* Search Options toggle */}


        {/* Input container */}
        <div
          className="relative rounded-2xl transition-all duration-200"
          style={{
            background: "hsl(var(--rl-ink-900))",
            border: isFocused
              ? "1px solid hsl(var(--rl-gold-400) / 0.45)"
              : "1px solid hsl(var(--rl-ink-700))",
            boxShadow: isFocused
              ? "0 0 0 3px hsl(var(--rl-gold-400) / 0.07), 0 4px 20px hsl(var(--rl-ink-950) / 0.4)"
              : "0 2px 8px hsl(var(--rl-ink-950) / 0.3)",
          }}
        >

          <div className="flex gap-2 m-2">

            {/* <div>
              <button
                type="button"
                onClick={() => setShowSearchOptions((prev) => !prev)}
                className="flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium transition-all duration-200"
                style={{
                  background: "hsl(var(--rl-ink-900))",
                  border: "1px solid hsl(var(--rl-ink-700))",
                  color: "hsl(var(--rl-ink-200))",
                }}
              >
                {showSearchOptions ? <X size={14} /> : <Plus size={14} />}
                {getSearchTypeLabel() ? <>  Searching by: <span className="border rounded-lg py-1 px-2 border-purple-800 text-amber-500">{getSearchTypeLabel()}</span></> : "Search Options"}
              </button>

              {showSearchOptions && (
                <div
                  className="absolute -top-[200px] left-2 right-2 rounded-2xl p-4 space-y-3"
                  style={{
                    background: "hsl(var(--rl-ink-900))",
                    border: "1px solid hsl(var(--rl-ink-700))",
                  }}
                >
                  {SEARCH_OPTIONS.map((option) => {
                    const isActive = searchType === option.key;
                    return (
                      <button
                        type="button"
                        key={option.key}
                        onClick={() => {
                          setSearchType(option.key);
                          setShowSearchOptions(false);
                        }}
                        className="w-full rounded-xl p-3 text-left transition-all duration-200"
                        style={{
                          background: isActive
                            ? "hsl(var(--rl-purple-950) / 0.35)"
                            : "hsl(var(--rl-ink-950))",
                          border: isActive
                            ? "1px solid hsl(var(--rl-gold-400) / 0.4)"
                            : "1px solid hsl(var(--rl-ink-800))",
                        }}
                      >
                        <h4
                          className="text-sm font-semibold mb-1"
                          style={{
                            color: isActive
                              ? "hsl(var(--rl-gold-300))"
                              : "hsl(var(--rl-ink-200))",
                          }}
                        >
                          {option.title}
                        </h4>
                        <p
                          className="text-xs leading-relaxed"
                          style={{ color: "hsl(var(--rl-ink-400))" }}
                        >
                          Example: {option.example}
                        </p>
                      </button>
                    );
                  })}
                </div>
              )}
            </div> */}
            {/* Active search type badge */}
            {/* <div className="px-4 pt-2">
              <div
                className="inline-flex items-center rounded-full px-3 py-1 text-[11px] font-medium"
                style={{
                  background: "hsl(var(--rl-purple-950) / 0.4)",
                  border: "1px solid hsl(var(--rl-gold-400) / 0.25)",
                  color: "hsl(var(--rl-gold-300))",
                }}
              >
                Searching by: {getSearchTypeLabel()}
              </div>
            </div> */}
          </div>

          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            disabled={isLoading}
            placeholder={getPlaceholder()}
            className="w-full resize-none bg-transparent px-4 pt-3 pb-12 text-sm leading-relaxed outline-none disabled:opacity-50"
            style={{
              fontFamily: "'DM Sans', sans-serif",
              color: "hsl(var(--rl-ink-100))",
            }}
            rows={2}
          />

          {/* Bottom row */}
          <div className="absolute bottom-3 left-4 right-3 flex items-center justify-between">
            {/* <p
              className="text-[10px] hidden sm:block"
              style={{ color: "hsl(var(--rl-ink-600))" }}
            >
              Enter to send · Shift+Enter for newline
            </p>
            <p
              className="text-[10px] sm:hidden"
              style={{ color: "hsl(var(--rl-ink-600))" }}
            >
              Tap ↑ to send
            </p> */}
            <div className="flex items-center gap-2">
              <button className="transition p-2 rounded-full border" onClick={() => setShowSearchOptions(prev => !prev)}> {showSearchOptions ? <X className="size-4" /> : <PlusIcon className="size-4" />} </button>
              <div className="flex flex-row gap-2">
                {
                  showSearchOptions && SEARCH_OPTIONS.map((option) => {
                    const isActive = searchType === option.key;
                    return (
                      <button
                        type="button"
                        key={option.key}
                        onClick={() => {
                          setSearchType(option.key);
                          // setShowSearchOptions(false);
                        }}
                        className={`rounded-lg text-center px-2 py-1 text-xs transition-all duration-200 ${isActive ? 'bg-purple-950/35 border border-gold-400/40' : 'bg-ink-950 border border-ink-800'}`}
                      >

                        {option.label}
                      </button>
                    );
                  })}
              </div>

            </div>

            
            <button
              type="submit"
              disabled={!canSend}
              className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-25"
              style={
                canSend
                  ? {
                    background:
                      "linear-gradient(135deg, hsl(var(--rl-purple-950)) 0%, hsl(var(--rl-purple-800)) 100%)",
                    border: "1px solid hsl(var(--rl-gold-400) / 0.4)",
                    boxShadow: "0 2px 10px hsl(var(--rl-purple-950) / 0.5)",
                  }
                  : {
                    background: "hsl(var(--rl-ink-50))",
                    border: "1px solid hsl(var(--rl-ink-100))",
                  }
              }
            >
              {isLoading ? (
                <Loader2
                  size={13}
                  className="animate-spin"
                  style={{ color: "hsl(var(--rl-ink-400))" }}
                />
              ) : (
                <ArrowUp
                  size={13}
                  strokeWidth={2.5}
                  style={{
                    color: canSend
                      ? "hsl(var(--rl-gold-300))"
                      : "hsl(var(--rl-ink-800))",
                  }}
                />
              )}
            </button>
          </div>
        </div>

        {/* Footer */}
        <p
          className="mt-2.5 text-center text-[10px]"
          style={{ color: "hsl(var(--rl-ink-600))" }}
        >
          Royal London · Incident AI · Responses are AI-generated and for guidance only
        </p>
      </form>
    </div>
  );
}