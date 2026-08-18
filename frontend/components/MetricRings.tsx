"use client";

import { Activity, Code2, ShieldCheck, GitBranch, Users } from "lucide-react";
import CircularRing from "./CircularRing";
import { ProfileAnalysisResult } from "../lib/api";

interface MetricRingsProps {
  breakdown: ProfileAnalysisResult["breakdown"];
}

export default function MetricRings({ breakdown }: MetricRingsProps) {
  const metrics = [
    {
      title: "Activity",
      score: breakdown.activity,
      icon: Activity,
      color: "text-indigo-500",
      status: breakdown.activity >= 80 ? "Highly Active" : "Active",
    },
    {
      title: "Lang Diversity",
      score: breakdown.language_diversity,
      icon: Code2,
      color: "text-blue-500",
      status: breakdown.language_diversity >= 80 ? "Very Good" : "Good",
    },
    {
      title: "Code Quality",
      score: breakdown.skill,
      icon: ShieldCheck,
      color: "text-emerald-500",
      status: breakdown.skill >= 80 ? "Excellent" : "Good",
    },
    {
      title: "Repo Impact",
      score: breakdown.impact,
      icon: GitBranch,
      color: "text-amber-500",
      status: breakdown.impact >= 80 ? "High Impact" : "Good",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6 w-full">
      {metrics.map((metric, i) => (
        <div
          key={i}
          className="flex flex-col items-center p-6 bg-neo-light dark:bg-neo-dark rounded-[2rem] shadow-neo-outset dark:shadow-neo-outset-dark"
        >
          <div className="flex items-center gap-2 mb-6 w-full justify-center">
            <metric.icon size={16} className={metric.color} />
            <h3 className="text-xs font-bold text-gray-600 dark:text-gray-300 uppercase tracking-wider">
              {metric.title}
            </h3>
          </div>

          <CircularRing
            percentage={metric.score}
            colorClass={metric.color}
            size={110}
            strokeWidth={10}
          />

          <div className="mt-6 w-full">
            <p className="text-sm font-bold text-gray-800 dark:text-white text-center mb-2">
              {metric.status}
            </p>
            <div className="w-12 h-1.5 rounded-full mx-auto shadow-neo-inset dark:shadow-neo-inset-dark">
              <div
                className={`h-full rounded-full w-full ${metric.color.replace("text-", "bg-")}`}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
