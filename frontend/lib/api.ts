const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

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
// Core Analysis Endpoints

export async function startAnalysis(
  username: string,
): Promise<AnalysisJobResponse> {
  const res = await fetch(`${API_BASE_URL}/analyze/${username}`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || "Failed to start analysis.");
  }
  return res.json();
}

export async function getAnalysisStatus(
  jobId: string,
): Promise<AnalysisJobResponse> {
  const res = await fetch(`${API_BASE_URL}/analyze/status/${jobId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || "Failed to fetch job status.");
  }
  return res.json();
}
// Session-Based AI Chat Endpoints

// Function 1: Initialize Chat Session
export async function startChat(
  username: string,
): Promise<{ session_id: string }> {
  const res = await fetch(`${API_BASE_URL}/chat/start/${username}`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(
      err.detail || err.message || "Failed to initialize chat session.",
    );
  }
  return res.json();
}

// Function 2: Send Message in Active Session
export async function sendChatMessage(
  sessionId: string,
  message: string,
): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/chat/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message: message,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || "Failed to send message.");
  }

  const data = await res.json();
  return data.response || data.reply || data.message || "No response received.";
}
// Auxiliary Helpers

export async function searchUsers(
  query: string,
): Promise<Array<{ login: string; avatar_url: string }>> {
  if (!query.trim()) return [];
  const res = await fetch(
    `${API_BASE_URL}/search?q=${encodeURIComponent(query)}`,
  );
  if (!res.ok) return [];
  return res.json();
}

// Fetch Real WeasyPrint Binary Stream
export async function downloadPdfReportBlob(username: string): Promise<Blob> {
  const res = await fetch(
    `${API_BASE_URL}/report/${encodeURIComponent(username)}?format=pdf`,
  );

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(
      err.detail || err.message || "Failed to generate PDF report.",
    );
  }

  return res.blob();
}

// Fetch Markdown Report
export async function fetchMarkdownReport(username: string): Promise<string> {
  const res = await fetch(
    `${API_BASE_URL}/report/${encodeURIComponent(username)}?format=md`,
  );

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(
      err.detail || err.message || "Could not fetch Markdown report.",
    );
  }

  return res.text();
}
