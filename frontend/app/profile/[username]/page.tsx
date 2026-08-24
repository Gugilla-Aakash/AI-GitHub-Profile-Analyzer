"use client";

import { useState, useEffect } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  startAnalysis,
  getAnalysisStatus,
  AnalysisJobResponse,
} from "../../../lib/api";
import ProfileHeader from "@/components/ProfileHeader";
import ProfileOverview from "@/components/ProfileOverview";
import MetricRings from "@/components/MetricRings";
import LanguageChart from "../../../components/LanguageChart";
import ActivityHeatmap from "../../../components/ActivityHeatmap";
import ChatWithProfile from "../../../components/ChatWithProfile";
import DownloadButtons from "../../../components/DownloadButtons";
import RepositoriesModal from "@/components/RepositoriesModal";

export default function ProfilePage() {
  const params = useParams();
  const router = useRouter(); // <-- Initialize router here
  const searchParams = useSearchParams();
  const rawUsername = params?.username;
  const username = (typeof rawUsername === "string" ? rawUsername : "")
    .toLowerCase()
    .trim();

  const [jobId, setJobId] = useState<string | null>(null);
  const [initialData, setInitialData] = useState<AnalysisJobResponse | null>(
    null,
  );
  const [initError, setInitError] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  const isReposModalOpen = searchParams.get("modal") === "repos";

  const handleCloseReposModal = () => {
    const newParams = new URLSearchParams(searchParams.toString());
    newParams.delete("modal");
    const queryStr = newParams.toString() ? `?${newParams.toString()}` : "";
    router.push(`/profile/${username}${queryStr}`, { scroll: false });
  };

  useEffect(() => {
    if (!username) return;
    let isMounted = true;
    setIsInitializing(true);
    setInitError(null);
    setInitialData(null);
    setJobId(null);

    startAnalysis(username)
      .then((res) => {
        if (!isMounted) return;
        setInitialData(res);
        if (res.job_id) setJobId(res.job_id);
      })
      .catch((err) => {
        if (!isMounted) return;
        setInitError(err.message || "Failed to start profile analysis.");
      })
      .finally(() => {
        if (isMounted) setIsInitializing(false);
      });

    return () => {
      isMounted = false;
    };
  }, [username]);

  const isInitialFinished =
    initialData?.status === "finished" || initialData?.status === "completed";

  const {
    data: statusData,
    isError,
    error,
  } = useQuery({
    queryKey: ["analysisStatus", jobId],
    queryFn: () => getAnalysisStatus(jobId!),
    enabled:
      Boolean(jobId) && !isInitialFinished && initialData?.status !== "failed",
    refetchInterval: (query) => {
      if (query.state.status === "error") return false;
      const status = query.state.data?.status;
      if (
        status === "finished" ||
        status === "completed" ||
        status === "failed"
      )
        return false;
      return 1500;
    },
  });

  const currentJob = statusData || initialData;
  const isFinished =
    isInitialFinished ||
    currentJob?.status === "finished" ||
    currentJob?.status === "completed";
  const isFailed =
    (!isFinished && (currentJob?.status === "failed" || isError)) ||
    Boolean(initError);
  const result = currentJob?.result;

  // State A: Initializing Request
  if (isInitializing && !currentJob && !isFailed) {
    return (
      <div className="max-w-7xl mx-auto p-4 sm:p-8 space-y-6">
        <ProfileHeader />
        <div className="min-h-[60vh] flex flex-col items-center justify-center text-center">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-gray-500 dark:text-gray-400">
            Initializing analysis for{" "}
            <span className="text-indigo-500 font-bold">@{username}</span>...
          </p>
        </div>
      </div>
    );
  }

  // State B: Analysis Error View
  if (isFailed) {
    const rawErrorMessage =
      initError ||
      (error as Error)?.message ||
      currentJob?.message ||
      "An unexpected error occurred.";
    const formattedError =
      rawErrorMessage === "Not Found"
        ? `GitHub user "@${username}" was not found or backend service is unreachable.`
        : rawErrorMessage;

    return (
      <div className="max-w-7xl mx-auto p-4 sm:p-8 space-y-6">
        <ProfileHeader />
        <div className="min-h-[60vh] flex flex-col items-center justify-center text-center max-w-md mx-auto">
          <div className="p-8 bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark rounded-[2rem] w-full mb-6">
            <div className="w-12 h-12 shadow-neo-inset dark:shadow-neo-inset-dark text-red-500 rounded-full flex items-center justify-center mx-auto mb-4 font-bold text-xl">
              ✕
            </div>
            <h3 className="font-black text-xl mb-2 text-gray-800 dark:text-white">
              Analysis Failed
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
              {formattedError}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // State C: Background Job Polling
  if (!isFinished) {
    return (
      <div className="max-w-7xl mx-auto p-4 sm:p-8 space-y-6">
        <ProfileHeader />
        <div className="min-h-[60vh] flex flex-col items-center justify-center text-center">
          <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
          <h2 className="text-2xl font-black text-gray-800 dark:text-white mb-2">
            Auditing @{username}...
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md">
            Fetching repositories, contribution calendar via GraphQL, checking
            READMEs, and running evaluation models...
          </p>
        </div>
      </div>
    );
  }

  // State D: Full Profile Dashboard View
  return (
    <div id="overview" className="max-w-screen-2xl mx-auto p-4 sm:p-8">
      <ProfileHeader />

      {/* Main 2-Column Dashboard Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* LEFT COLUMN: Profile & Metrics */}
        <div className="xl:col-span-2 space-y-8">
          {result && (
            <ProfileOverview
              username={username}
              grade={result.grade}
              finalScore={result.final_score}
              totalStars={result.impact.total_stars}
            />
          )}

          <div id="activity">
            {result?.activity && (
              <ActivityHeatmap
                activity={result.activity}
                contributions={result.recent_contributions_365_days}
              />
            )}
          </div>

          <div id="repositories">
            {result && <MetricRings breakdown={result.breakdown} />}
          </div>

          <div id="languages">
            {result?.language && <LanguageChart language={result.language} />}
          </div>
        </div>

        {/* RIGHT COLUMN: AI Chat & Downloads */}
        <div className="xl:col-span-1 space-y-8">
          {result && <DownloadButtons username={username} result={result} />}
          <div id="ai-insights">
            {username && <ChatWithProfile username={username} />}
          </div>
        </div>
      </div>

      {/* Repositories Insights Modal */}
      {username && (
        <RepositoriesModal
          username={username}
          isOpen={isReposModalOpen}
          onClose={handleCloseReposModal}
        />
      )}
    </div>
  );
}
