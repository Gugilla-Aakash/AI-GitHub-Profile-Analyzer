"use client";

import { useState } from "react";
import { ProfileAnalysisResult } from "../lib/api";
import {
  Code2,
  Minus,
  BarChart3,
  PieChart as PieChartIcon,
} from "lucide-react";

interface LanguageChartProps {
  language: ProfileAnalysisResult["language"];
}

type ChartType = "linear" | "bar" | "pie";

const LANGUAGE_COLORS: Record<string, string> = {
  Python: "#3572A5",
  JavaScript: "#f1e05a",
  TypeScript: "#3178c6",
  HTML: "#e34c26",
  CSS: "#563d7c",
  C: "#555555",
  "C++": "#f34b7d",
  Java: "#b07219",
  Go: "#00ADD8",
  Rust: "#dea584",
  PHP: "#4F5D95",
  Ruby: "#701516",
  Shell: "#89e051",
  Vue: "#41b883",
  React: "#61dafb",
  Svelte: "#ff3e00",
  Kotlin: "#A97BFF",
  Swift: "#F05138",
};

const getLanguageColor = (lang: string) => {
  if (LANGUAGE_COLORS[lang]) return LANGUAGE_COLORS[lang];
  let hash = 0;
  for (let i = 0; i < lang.length; i++) {
    hash = lang.charCodeAt(i) + ((hash << 5) - hash);
  }
  let color = "#";
  for (let i = 0; i < 3; i++) {
    let value = (hash >> (i * 8)) & 0xff;
    color += ("00" + value.toString(16)).slice(-2);
  }
  return color;
};

const getLanguageIconUrl = (lang: string) => {
  const map: Record<string, string> = {
    Python: "python/python-original.svg",
    JavaScript: "javascript/javascript-original.svg",
    TypeScript: "typescript/typescript-original.svg",
    HTML: "html5/html5-original.svg",
    CSS: "css3/css3-original.svg",
    C: "c/c-original.svg",
    "C++": "cplusplus/cplusplus-original.svg",
    Java: "java/java-original.svg",
    Go: "go/go-original.svg",
    Rust: "rust/rust-original.svg",
    PHP: "php/php-original.svg",
    Ruby: "ruby/ruby-original.svg",
    Vue: "vuejs/vuejs-original.svg",
    React: "react/react-original.svg",
    Kotlin: "kotlin/kotlin-original.svg",
    Swift: "swift/swift-original.svg",
  };
  const key = Object.keys(map).find(
    (k) => k.toLowerCase() === lang.toLowerCase(),
  );
  if (key) {
    return `https://cdn.jsdelivr.net/gh/devicons/devicon/icons/${map[key]}`;
  }
  return null;
};

const CHART_OPTIONS: { type: ChartType; label: string; icon: typeof Minus }[] =
  [
    { type: "linear", label: "Linear", icon: Minus },
    { type: "bar", label: "Bar", icon: BarChart3 },
    { type: "pie", label: "Pie", icon: PieChartIcon },
  ];

export default function LanguageChart({ language }: LanguageChartProps) {
  const { primary_language, percentages, diversity_score } = language;
  const [chartType, setChartType] = useState<ChartType>("linear");

  const entries = Object.entries(percentages || {}).sort((a, b) => b[1] - a[1]);

  // Precompute cumulative offsets for the donut chart
  let cumulative = 0;
  const donutSegments = entries.map(([lang, pct]) => {
    const offset = cumulative;
    cumulative += pct;
    return { lang, pct, offset, color: getLanguageColor(lang) };
  });

  const RADIUS = 80;
  const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

  return (
    <div className="p-8 bg-neo-light dark:bg-neo-dark rounded-[2rem] shadow-neo-outset dark:shadow-neo-outset-dark space-y-6 w-full transition-all duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold tracking-wider text-gray-500 dark:text-gray-400 uppercase mb-1">
            <Code2 size={14} className="text-indigo-500" />
            Language Breakdown
          </div>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-2xl font-black text-gray-800 dark:text-white">
              {primary_language || "N/A"}
            </span>
            <span className="text-xs px-3 py-1 bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark text-indigo-500 font-bold rounded-full">
              Primary
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-auto">
          {/* Chart Type Toggle */}
          <div className="flex items-center gap-1 p-1 rounded-2xl bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark">
            {CHART_OPTIONS.map(({ type, label, icon: Icon }) => {
              const active = chartType === type;
              return (
                <button
                  key={type}
                  type="button"
                  onClick={() => setChartType(type)}
                  title={`${label} chart`}
                  aria-pressed={active}
                  className={`flex items-center justify-center p-2 rounded-xl transition-all duration-300 ${
                    active
                      ? "bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark text-indigo-500"
                      : "text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
                  }`}
                >
                  <Icon size={14} />
                </button>
              );
            })}
          </div>

          <div className="px-5 py-2.5 rounded-2xl bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark text-right">
            <span className="text-[10px] text-gray-400 block uppercase tracking-wider font-bold">
              Diversity Score
            </span>
            <span className="text-sm font-extrabold text-indigo-500">
              {diversity_score ?? "0.00"}
            </span>
          </div>
        </div>
      </div>

      {/* Chart Area */}
      {entries.length > 0 ? (
        <>
          {chartType === "linear" && (
            <div className="w-full h-4 bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark rounded-full overflow-hidden flex p-1">
              {entries.map(([lang, pct]) => {
                const color = getLanguageColor(lang);
                return (
                  <div
                    key={lang}
                    style={{ width: `${pct}%`, backgroundColor: color }}
                    title={`${lang}: ${pct}%`}
                    className="h-full first:rounded-l-full last:rounded-r-full transition-all duration-700 ease-out hover:opacity-80"
                  />
                );
              })}
            </div>
          )}

          {chartType === "bar" && (
            <div className="p-5 rounded-2xl bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark">
              <div className="flex items-end gap-3 h-48 px-1">
                {entries.map(([lang, pct]) => {
                  const color = getLanguageColor(lang);
                  return (
                    <div
                      key={lang}
                      className="flex-1 flex flex-col items-center justify-end gap-2 h-full group min-w-0"
                    >
                      <span className="text-[10px] font-bold text-gray-500 dark:text-gray-400">
                        {pct}%
                      </span>
                      <div
                        title={`${lang}: ${pct}%`}
                        className="w-full rounded-t-lg transition-all duration-700 ease-out group-hover:opacity-80"
                        style={{
                          height: `${Math.max(pct, 2)}%`,
                          backgroundColor: color,
                        }}
                      />
                      <span className="text-[10px] font-semibold text-gray-600 dark:text-gray-300 truncate max-w-full">
                        {lang}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {chartType === "pie" && (
            <div className="p-6 rounded-2xl bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark flex flex-col sm:flex-row items-center justify-center gap-8">
              <div className="relative w-48 h-48 shrink-0">
                <svg viewBox="0 0 200 200" className="w-48 h-48 -rotate-90">
                  <circle
                    cx="100"
                    cy="100"
                    r={RADIUS}
                    fill="none"
                    strokeWidth="24"
                    className="stroke-gray-200 dark:stroke-gray-800/40"
                  />
                  {donutSegments.map((seg) => {
                    const dash = (seg.pct / 100) * CIRCUMFERENCE;
                    const dashArray = `${dash} ${CIRCUMFERENCE - dash}`;
                    const dashOffset = -((seg.offset / 100) * CIRCUMFERENCE);
                    return (
                      <circle
                        key={seg.lang}
                        cx="100"
                        cy="100"
                        r={RADIUS}
                        fill="none"
                        stroke={seg.color}
                        strokeWidth="24"
                        strokeDasharray={dashArray}
                        strokeDashoffset={dashOffset}
                        strokeLinecap="butt"
                        className="transition-all duration-700 ease-out hover:opacity-80"
                      >
                        <title>{`${seg.lang}: ${seg.pct}%`}</title>
                      </circle>
                    );
                  })}
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-xl font-black text-gray-800 dark:text-white truncate max-w-[80%]">
                    {primary_language || "N/A"}
                  </span>
                  <span className="text-[10px] text-gray-400 uppercase tracking-wider font-bold">
                    Primary
                  </span>
                </div>
              </div>

              <div className="flex flex-col gap-2 w-full sm:w-auto">
                {donutSegments.map((seg) => (
                  <div
                    key={seg.lang}
                    className="flex items-center gap-2 text-xs"
                  >
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: seg.color }}
                    />
                    <span className="font-bold text-gray-700 dark:text-gray-200">
                      {seg.lang}
                    </span>
                    <span className="text-indigo-500 font-mono font-black">
                      {seg.pct}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="text-xs text-gray-400 italic py-2 text-center">
          No language byte data available.
        </div>
      )}

      {/* Individual Language Cards Grid with Inset Shadows & Readability Dots */}
      <div className="max-h-64 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-gray-400 dark:scrollbar-thumb-gray-700">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {entries.map(([lang, pct]) => {
            const color = getLanguageColor(lang);
            const iconUrl = getLanguageIconUrl(lang);
            return (
              <div
                key={lang}
                className="flex items-center justify-between p-4 bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark rounded-2xl text-xs transition-all duration-300 hover:scale-[1.02]"
              >
                <div className="flex items-center gap-3 truncate">
                  {iconUrl ? (
                    <img
                      src={iconUrl}
                      alt={lang}
                      className="w-6 h-6 object-contain shrink-0"
                    />
                  ) : (
                    <span
                      className="w-3.5 h-3.5 rounded-full shrink-0 shadow-sm"
                      style={{ backgroundColor: color }}
                    />
                  )}
                  <div className="flex items-center gap-2 truncate">
                    <span className="font-bold text-gray-700 dark:text-gray-200 truncate">
                      {lang}
                    </span>
                    {/* Readability Dot */}
                    <span
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ backgroundColor: color }}
                      title={`${lang} color`}
                    />
                  </div>
                </div>
                <span className="text-indigo-500 font-mono font-black text-sm pl-2">
                  {pct}%
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
