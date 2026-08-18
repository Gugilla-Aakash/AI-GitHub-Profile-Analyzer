"use client";

import { ProfileAnalysisResult } from "../lib/api";

interface ScoreCardProps {
  result: ProfileAnalysisResult;
}

export default function ScoreCard({ result }: ScoreCardProps) {
  const { final_score, grade, breakdown } = result;

  const getGradeColor = (g: string) => {
    switch (g.toUpperCase()) {
      case "S":
        return "bg-amber-950/80 border-amber-500/80 text-amber-300 shadow-amber-500/20";
      case "A":
        return "bg-emerald-950/80 text-emerald-400 border-emerald-800";
      case "B":
        return "bg-blue-950/80 text-blue-400 border-blue-800";
      case "C":
        return "bg-amber-950/80 text-amber-400 border-amber-800";
      default:
        return "bg-red-950/80 text-red-400 border-red-800";
    }
  };

  const subScores = [
    { label: "Activity", score: breakdown.activity },
    { label: "Impact", score: breakdown.impact },
    { label: "Skill Breadth", score: breakdown.skill },
    { label: "Language Diversity", score: breakdown.language_diversity },
  ];

  return (
    <div className="p-6 bg-gray-900 border border-gray-800 rounded-2xl shadow-xl space-y-6">
      {/* Header: Score & Grade */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xs font-semibold tracking-wider text-gray-400 uppercase">
            Overall Profile Evaluation
          </h2>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-5xl font-black text-white">
              {final_score}
            </span>
            <span className="text-lg text-gray-500 font-medium">/ 100</span>
          </div>
        </div>

        <div
          className={`px-5 py-2.5 rounded-2xl border text-2xl font-black shadow-inner ${getGradeColor(
            grade,
          )}`}
        >
          Grade {grade}
        </div>
      </div>

      {/* Breakdown Progress Bars */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
        {subScores.map((item) => (
          <div
            key={item.label}
            className="p-3.5 bg-gray-950/60 border border-gray-800/80 rounded-xl space-y-2"
          >
            <div className="flex justify-between items-center text-xs">
              <span className="font-medium text-gray-300">{item.label}</span>
              <span className="font-bold text-gray-100">
                {item.score} / 100
              </span>
            </div>
            <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
              <div
                className="bg-blue-500 h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, Math.max(0, item.score))}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
