export interface SimilarIncident {
  incident_number: string;
  short_description: string;
  description: string;
  assignment_group: string;
  priority: string;
  category: string;
  resolution_notes: string;
  servicenow_link: string;
  azure_devops_link: string;
  datafix_code: string;
  similarity_score: number;
}

export interface SearchIncidentsRequest {
  query_text: string;
  top_k?: number;
}

export interface SearchIncidentsResponse {
  status: string;
  query_text: string;
  results: SimilarIncident[];
}

export interface ChatRequest {
  user_query?: string;
  incident_link?: string;
  incident_number?: string;
  top_k?: number;
}

export interface ChatResponse {
  status: string;
  user_query: string;
  results: SimilarIncident[];
  answer: string;
  recommended_resolution: string;
  recommended_datafix: string | null;
}

/** A single progress event streamed from the agent via SSE. */
export interface AgentProgressEvent {
  type: "step_start" | "step_done" | "tool_call" | "result" | "error";
  label: string;
  detail: string;
}