const rawBaseUrl = (
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");

const API_BASE_URL = rawBaseUrl.endsWith("/api/v1")
  ? rawBaseUrl
  : `${rawBaseUrl}/api/v1`;

export interface ProfileAnalysisResult {
  username: string;
  final_score: number;
  grade: string;
  breakdown: {
    activity: number;
    impact: number;
    skill: number;
    language_diversity: number;
  };
  language: {
    total_bytes: number;
    primary_language: string;
    percentages: Record<string, number>;
    language_count: number;
    diversity_score: number;
  };
  impact: {
    total_stars: number;
    total_forks: number;
    owned_repo_count: number;
    forked_repo_count: number;
    hero_repo?: {
      name: string;
      description?: string;
      stargazer_count: number;
      fork_count: number;
    };
  };
  activity: {
    total_contributions_365: number;
    lifetime_prs: number;
    lifetime_issues: number;
    collaboration_ratio_365: number;
    activity_tier: string;
  };
  recent_contributions_365_days?: {
    totalContributions?: number;
    weeks: Array<{
      contributionDays: Array<{
        date: string;
        contributionCount: number;
      }>;
    }>;
  };
}

export interface AnalysisJobResponse {
  job_id: string;
  status: "queued" | "started" | "finished" | "completed" | "failed";
  cached?: boolean;
  result?: ProfileAnalysisResult;
  message?: string;
}

const STORAGE_UNAVAILABLE_MESSAGE =
  "The service is temporarily unable to reach its storage backend. Please try again in a moment.";

/**
 * Turns a non-OK response into a readable Error.
 *
 * FastAPI returns `{ "detail": "..." }`, but a 5xx can also arrive as HTML or
 * an empty body, so fall back rather than throwing a JSON parse error.
 */
async function toError(res: Response, fallback: string): Promise<Error> {
  if (res.status === 503) {
    return new Error(STORAGE_UNAVAILABLE_MESSAGE);
  }
  try {
    const body = await res.json();
    const detail = body?.detail ?? body?.message;
    if (typeof detail === "string" && detail.trim()) {
      return new Error(detail);
    }
  } catch {
    // Non-JSON error body; fall through to the generic message below.
  }
  return new Error(`${fallback} (HTTP ${res.status})`);
}

export async function startAnalysis(
  username: string,
): Promise<AnalysisJobResponse> {
  const res = await fetch(`${API_BASE_URL}/analyze/${username}`, {
    method: "POST",
  });
  if (!res.ok) {
    throw await toError(res, "Failed to start analysis.");
  }
  return res.json();
}

export async function getAnalysisStatus(
  jobId: string,
): Promise<AnalysisJobResponse> {
  const res = await fetch(`${API_BASE_URL}/analyze/status/${jobId}`);
  if (!res.ok) {
    throw await toError(res, "Failed to fetch job status.");
  }
  return res.json();
}

export async function startChat(
  username: string,
): Promise<{ session_id: string }> {
  const res = await fetch(`${API_BASE_URL}/chat/start/${username}`, {
    method: "POST",
  });
  if (!res.ok) {
    throw await toError(res, "Failed to initialize chat session.");
  }
  return res.json();
}

export async function streamChatMessage(
  sessionId: string,
  message: string,
  onChunk: (accumulatedText: string) => void,
): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/chat/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message: message,
    }),
  });

  // MAGIC FIX: Read error as plain text to prevent JSON parse crashes in the UI
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || `HTTP Error: ${res.status}`);
  }

  if (!res.body) {
    throw new Error("No response stream available.");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let accumulatedText = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      accumulatedText += chunk;
      onChunk(accumulatedText);
    }
  } finally {
    // Crucial: Release the lock so the browser can clean up the memory
    reader.releaseLock();
  }

  return accumulatedText;
}

export async function searchUsers(
  query: string,
): Promise<Array<{ login: string; avatar_url: string }>> {
  if (!query.trim()) return [];
  // Trailing slash matches the backend route exactly, avoiding a 307 redirect
  // round-trip on every keystroke.
  const res = await fetch(
    `${API_BASE_URL}/search/?q=${encodeURIComponent(query)}`,
  );
  if (!res.ok) return [];
  return res.json();
}

export async function downloadPdfReportBlob(username: string): Promise<Blob> {
  const res = await fetch(
    `${API_BASE_URL}/report/${encodeURIComponent(username)}?format=pdf`,
  );
  if (!res.ok) {
    throw await toError(res, "Failed to generate PDF report.");
  }
  return res.blob();
}

export async function fetchMarkdownReport(username: string): Promise<string> {
  const res = await fetch(
    `${API_BASE_URL}/report/${encodeURIComponent(username)}?format=md`,
  );
  if (!res.ok) {
    throw await toError(res, "Could not fetch Markdown report.");
  }
  return res.text();
}
