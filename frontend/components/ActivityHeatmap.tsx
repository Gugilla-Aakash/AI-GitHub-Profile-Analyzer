"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import { ProfileAnalysisResult } from "../lib/api";
import {
  Calendar,
  GitPullRequest,
  GitMerge,
  Users,
  CalendarDays,
} from "lucide-react";

// 1. TYPES & INTERFACES
export interface ContributionDay {
  date: string;
  contributionCount: number;
}

export interface ContributionWeek {
  contributionDays: ContributionDay[];
}

export interface ActivityHeatmapProps {
  activity: ProfileAnalysisResult["activity"];
  contributions?: ProfileAnalysisResult["recent_contributions_365_days"];
}

// 2. UTILITIES
const getCellClasses = (count: number) => {
  if (count === 0)
    return "bg-gray-200 text-gray-400 dark:bg-[#1E2432] dark:text-[#1E2432] shadow-[inset_0_1px_2px_rgba(0,0,0,0.06),inset_0_1px_1px_rgba(255,255,255,0.5)] dark:shadow-[inset_0_1px_2px_rgba(0,0,0,0.3),inset_0_1px_1px_rgba(255,255,255,0.02)]";
  if (count <= 2)
    return "bg-[#60A5FA] text-[#60A5FA] dark:bg-[#3B82F6] dark:text-[#3B82F6]";
  if (count <= 5)
    return "bg-[#818CF8] text-[#818CF8] dark:bg-[#4F46E5] dark:text-[#4F46E5]";
  if (count <= 9)
    return "bg-[#2DD4BF] text-[#2DD4BF] dark:bg-[#06B6D4] dark:text-[#06B6D4]";
  return "bg-[#34D399] text-[#34D399] dark:bg-[#14F195] dark:text-[#14F195] shadow-[0_0_8px_rgba(52,211,153,0.5)] dark:shadow-[0_0_8px_rgba(20,241,149,0.35)]";
};

const getSparklineColor = (total: number, max: number) => {
  if (total === 0) return "bg-gray-300 dark:bg-gray-700/50";
  const ratio = total / max;
  if (ratio <= 0.25) return "bg-[#60A5FA] dark:bg-[#3B82F6]";
  if (ratio <= 0.5) return "bg-[#818CF8] dark:bg-[#4F46E5]";
  if (ratio <= 0.75) return "bg-[#2DD4BF] dark:bg-[#06B6D4]";
  return "bg-[#34D399] dark:bg-[#14F195]";
};

const getDotColor = (count: number) => {
  if (count === 0) return "bg-gray-400 dark:bg-gray-500";
  if (count <= 2) return "bg-[#60A5FA] dark:bg-[#3B82F6]";
  if (count <= 5) return "bg-[#818CF8] dark:bg-[#4F46E5]";
  if (count <= 9) return "bg-[#2DD4BF] dark:bg-[#06B6D4]";
  return "bg-[#34D399] dark:bg-[#14F195]";
};

const formatDate = (dateString: string) => {
  const [y, m, d] = dateString.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  return {
    weekday: date.toLocaleDateString("en-US", { weekday: "long" }),
    rest: date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    }),
  };
};

// 3. DATA HOOK (useHeatmapData)
function useHeatmapData(weeks: ContributionWeek[]) {
  return useMemo(() => {
    const dayDataMap = new Map();
    const monthLabels: { label: string; index: number }[] = [];
    const weekToMonth = new Array(weeks.length).fill(0);
    const blooms: {
      id: string;
      weekIdx: number;
      x: number;
      y: number;
      colorClass: string;
    }[] = [];
    const weeklyTotals: number[] = [];

    const allDays = weeks.flatMap((w) => w.contributionDays);
    const total = allDays.reduce((sum, d) => sum + d.contributionCount, 0);
    const dailyAvg = total / (allDays.length || 1);

    let currentStreak = 0;
    let currentMonth = -1;
    let currentMonthStartIdx = 0;
    let maxWeeklyTotal = 1;

    weeks.forEach((week, weekIdx) => {
      let weekTotal = 0;

      if (week.contributionDays.length > 0) {
        const [y, m, d] = week.contributionDays[0].date.split("-").map(Number);
        const date = new Date(y, m - 1, d);
        const month = date.getMonth();

        if (month !== currentMonth) {
          monthLabels.push({
            label: date.toLocaleDateString("en-US", { month: "short" }),
            index: weekIdx,
          });
          currentMonth = month;
          currentMonthStartIdx = weekIdx;
        }
        weekToMonth[weekIdx] = currentMonthStartIdx;

        week.contributionDays.forEach((day, dayIdx) => {
          const count = day.contributionCount;
          weekTotal += count;

          if (count > 0) currentStreak++;
          else currentStreak = 0;

          const globalDayIndex = allDays.findIndex((d) => d.date === day.date);
          const prevDay =
            globalDayIndex > 0 ? allDays[globalDayIndex - 1] : null;
          const diff = prevDay ? count - prevDay.contributionCount : 0;

          dayDataMap.set(day.date, {
            count,
            streak: currentStreak,
            diff,
            isAboveAverage: count > dailyAvg,
          });

          if (count > 2) {
            let colorClass =
              count <= 5
                ? "bg-[#818CF8] dark:bg-[#4F46E5]"
                : count <= 9
                  ? "bg-[#2DD4BF] dark:bg-[#06B6D4]"
                  : "bg-[#34D399] dark:bg-[#14F195]";
            blooms.push({
              id: `${weekIdx}-${dayIdx}`,
              weekIdx,
              x: weekIdx * 18,
              y: dayIdx * 18,
              colorClass,
            });
          }
        });
      }
      weeklyTotals.push(weekTotal);
      if (weekTotal > maxWeeklyTotal) maxWeeklyTotal = weekTotal;
    });

    return {
      dayDataMap,
      monthLabels,
      weekToMonth,
      blooms,
      weeklyTotals,
      maxWeeklyTotal,
    };
  }, [weeks]);
}

// 4. MAIN COMPONENT
export default function ActivityHeatmap({
  activity,
  contributions,
}: ActivityHeatmapProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  const weeks: ContributionWeek[] = contributions?.weeks || [];

  const {
    dayDataMap,
    monthLabels,
    weekToMonth,
    blooms,
    weeklyTotals,
    maxWeeklyTotal,
  } = useHeatmapData(weeks);

  const [tooltip, setTooltip] = useState({
    visible: false,
    x: 0,
    y: 0,
    date: "",
    count: 0,
    streak: 0,
    diff: 0,
    isAboveAverage: false,
  });
  const [spotlight, setSpotlight] = useState({ visible: false, x: 0, y: 0 });

  useEffect(() => {
    if (scrollContainerRef.current) {
      requestAnimationFrame(() => {
        // Fix: Safety null check inside the animation frame
        if (scrollContainerRef.current) {
          scrollContainerRef.current.scrollLeft =
            scrollContainerRef.current.scrollWidth;
        }
      });
    }
  }, [weeks]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (cardRef.current) {
      const cardRect = cardRef.current.getBoundingClientRect();
      setSpotlight({
        visible: true,
        x: e.clientX - cardRect.left,
        y: e.clientY - cardRect.top,
      });
    }

    if (!gridRef.current) return;
    const cells = gridRef.current.getElementsByClassName("heatmap-cell");
    const rects = [];
    let closestCellIndex = -1;
    let minTargetDist = Infinity;

    for (let i = 0; i < cells.length; i++) {
      const rect = cells[i].getBoundingClientRect();
      const dist = Math.hypot(
        e.clientX - (rect.left + rect.width / 2),
        e.clientY - (rect.top + rect.height / 2),
      );
      rects.push(dist);
      if (dist < minTargetDist) {
        minTargetDist = dist;
        closestCellIndex = i;
      }
    }

    for (let i = 0; i < cells.length; i++) {
      const dist = rects[i];
      const cell = cells[i] as HTMLElement;
      if (dist < 16) cell.setAttribute("data-hover-state", "hovered");
      else if (dist < 32) cell.setAttribute("data-hover-state", "dist-1");
      else if (dist < 48) cell.setAttribute("data-hover-state", "dist-2");
      else cell.setAttribute("data-hover-state", "none");
    }

    if (closestCellIndex !== -1 && minTargetDist < 24) {
      const closestCell = cells[closestCellIndex] as HTMLElement;
      const dateStr = closestCell.getAttribute("data-date");
      const monthId = closestCell.getAttribute("data-month-id");
      const weekId = closestCell.getAttribute("data-week-id");

      Array.from(gridRef.current.getElementsByClassName("month-label")).forEach(
        (n) => {
          n.setAttribute(
            "data-active",
            n.getAttribute("data-month-id") === monthId ? "true" : "false",
          );
        },
      );

      Array.from(
        gridRef.current.getElementsByClassName("sparkline-bar"),
      ).forEach((n) => {
        n.setAttribute(
          "data-active",
          n.getAttribute("data-week-id") === weekId ? "true" : "false",
        );
      });

      if (dateStr && dayDataMap.has(dateStr)) {
        const data = dayDataMap.get(dateStr);
        let x = e.clientX + 16,
          y = e.clientY + 16;
        if (x + 220 > window.innerWidth) x = e.clientX - 236;
        if (y + 160 > window.innerHeight) y = e.clientY - 176;
        setTooltip({ visible: true, x, y, date: dateStr, ...data });
      }
    } else {
      setTooltip((p) => ({ ...p, visible: false }));
      Array.from(gridRef.current.getElementsByClassName("month-label")).forEach(
        (n) => n.setAttribute("data-active", "false"),
      );
      Array.from(
        gridRef.current.getElementsByClassName("sparkline-bar"),
      ).forEach((n) => n.setAttribute("data-active", "false"));
    }
  };

  const handleMouseLeave = () => {
    setSpotlight((p) => ({ ...p, visible: false }));
    setTooltip((p) => ({ ...p, visible: false }));
    if (!gridRef.current) return;
    Array.from(gridRef.current.getElementsByClassName("heatmap-cell")).forEach(
      (c) => {
        c.setAttribute("data-hover-state", "none");
        c.setAttribute("data-dimmed", "false");
      },
    );
    Array.from(gridRef.current.getElementsByClassName("month-label")).forEach(
      (n) => n.setAttribute("data-active", "false"),
    );
    Array.from(gridRef.current.getElementsByClassName("sparkline-bar")).forEach(
      (n) => n.setAttribute("data-active", "false"),
    );
  };

  const handleSparklineHover = (weekIdx: number | null) => {
    if (!gridRef.current) return;
    const cells = gridRef.current.getElementsByClassName("heatmap-cell");
    for (let i = 0; i < cells.length; i++) {
      if (weekIdx === null) {
        cells[i].setAttribute("data-dimmed", "false");
      } else {
        cells[i].setAttribute(
          "data-dimmed",
          cells[i].getAttribute("data-week-id") === String(weekIdx)
            ? "false"
            : "true",
        );
      }
    }
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="relative p-8 bg-neo-light dark:bg-neo-dark rounded-[2rem] shadow-neo-outset dark:shadow-neo-outset-dark w-full overflow-hidden"
    >
      {/* Spotlight Layer */}
      <div className="pointer-events-none absolute inset-0 z-0">
        <div
          className={`absolute pointer-events-none ${spotlight.visible ? "opacity-100" : "opacity-0"}`}
          style={{
            width: "1200px",
            height: "1200px",
            left: "-600px",
            top: "-600px",
            transform: `translate(${spotlight.x}px, ${spotlight.y}px)`,
            transition:
              "transform 100ms cubic-bezier(0.2, 0.9, 0.3, 1), opacity 400ms ease",
            background:
              "radial-gradient(circle at center, rgba(59,130,246,0.03) 0%, rgba(99,102,241,0.01) 20%, transparent 45%)",
          }}
        />
      </div>

      {/* Global Component Styles */}
      <style
        dangerouslySetInnerHTML={{
          __html: `
        @keyframes staggerFadeIn {
          0% { opacity: 0; transform: translateY(8px); }
          100% { opacity: 1; transform: translateY(0); }
        }
        .animate-stagger {
          opacity: 0;
          animation: staggerFadeIn 350ms cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
        }

        .heatmap-cell {
          transition: transform 200ms cubic-bezier(0.2, 0.9, 0.2, 1), box-shadow 200ms cubic-bezier(0.2, 0.9, 0.2, 1), opacity 200ms ease;
          will-change: transform, box-shadow, opacity;
          position: relative; z-index: 10;
        }
        .heatmap-cell[data-hover-state="hovered"] { transform: scale(1.35) translateY(-2px); z-index: 20; box-shadow: 0 0 12px currentColor !important; }
        .heatmap-cell[data-hover-state="dist-1"] { transform: scale(1.15) translateY(-1px); z-index: 15; }
        .heatmap-cell[data-hover-state="dist-2"] { transform: scale(1.05) translateY(0); z-index: 12; }
        .heatmap-cell[data-hover-state="none"] { transform: scale(1) translateY(0); z-index: 10; }
        .heatmap-cell[data-dimmed="true"] { opacity: 0.25; filter: saturate(0.5); }
        
        .month-label { transition: all 150ms ease; opacity: 0.8; }
        .month-label[data-active="true"] { opacity: 1; text-transform: uppercase; color: #111827 !important; }
        @media (prefers-color-scheme: dark) { .month-label[data-active="true"] { color: #F9FAFB !important; } }
        
        .sparkline-bar { transition: all 150ms ease; opacity: 0.3; }
        .sparkline-bar[data-active="true"] { opacity: 1; transform: scaleY(1.2); }
      `,
        }}
      />

      {/* Header */}
      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold tracking-wider text-gray-500 dark:text-gray-400 uppercase mb-1">
            <Calendar size={14} className="text-indigo-500" />
            365-Day Contribution Calendar
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-gray-800 dark:text-white">
              {activity.total_contributions_365.toLocaleString()}
            </span>
            <span className="text-xs text-gray-500 font-medium">
              contributions in the last year
            </span>
          </div>
        </div>
        <div className="px-4 py-2 rounded-xl bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark text-right self-start sm:self-auto">
          <span className="text-[10px] text-gray-400 block uppercase tracking-wider font-bold">
            Activity Tier
          </span>
          <span className="text-xs font-bold text-emerald-500 capitalize">
            {activity.activity_tier || "N/A"}
          </span>
        </div>
      </div>

      {/* Core Matrix Area */}
      {weeks.length > 0 ? (
        <div className="relative z-10 p-4 rounded-2xl bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark mb-6 flex flex-col">
          <div
            ref={scrollContainerRef}
            className="relative overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-gray-400 dark:scrollbar-thumb-gray-700"
          >
            <div
              ref={gridRef}
              className="inline-block w-max flex-none py-2 relative z-10 px-1"
            >
              {/* Sparkline Layer */}
              <div
                className="relative h-[14px] mb-4 w-full flex gap-1.5"
                onMouseLeave={() => handleSparklineHover(null)}
              >
                {weeklyTotals.map((total, idx) => (
                  <div
                    key={`spark-${idx}`}
                    className="w-3 h-full animate-stagger"
                    style={{ animationDelay: `${idx * 6}ms` }}
                  >
                    <div
                      className="w-full h-full flex items-end justify-center group cursor-pointer"
                      onMouseEnter={() => handleSparklineHover(idx)}
                    >
                      <div
                        data-week-id={idx}
                        className={`sparkline-bar w-[4px] rounded-full origin-bottom ${getSparklineColor(total, maxWeeklyTotal)}`}
                        style={{
                          height: `${Math.max((total / maxWeeklyTotal) * 100, 15)}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Month Labels Layer */}
              <div className="relative h-5 mb-1 w-full">
                {monthLabels.map((month) => (
                  <div
                    key={month.index}
                    className="absolute top-0 animate-stagger"
                    style={{
                      left: `${month.index * 18}px`,
                      animationDelay: `${month.index * 6}ms`,
                    }}
                  >
                    <span
                      data-month-id={month.index}
                      data-active="false"
                      className="month-label text-[10px] font-medium text-gray-500"
                    >
                      {month.label}
                    </span>
                  </div>
                ))}
              </div>

              {/* Grid & Blooms Layer */}
              <div className="relative">
                <div className="absolute inset-0 pointer-events-none z-0">
                  {blooms.map((bloom) => (
                    <div
                      key={bloom.id}
                      className="absolute animate-stagger"
                      style={{
                        left: bloom.x,
                        top: bloom.y,
                        animationDelay: `${bloom.weekIdx * 6}ms`,
                      }}
                    >
                      <div
                        className={`absolute rounded-full blur-[16px] opacity-10 transition-all ${bloom.colorClass}`}
                        style={{
                          width: "28px",
                          height: "28px",
                          transform: "translate(-8px, -8px)",
                        }}
                      />
                    </div>
                  ))}
                </div>
                <div className="inline-flex gap-1.5 relative z-10">
                  {weeks.map((week: ContributionWeek, weekIdx: number) => (
                    <div
                      key={weekIdx}
                      className="flex flex-col gap-1.5 animate-stagger"
                      style={{ animationDelay: `${weekIdx * 6}ms` }}
                    >
                      {week.contributionDays.map((day: ContributionDay) => (
                        <div
                          key={day.date}
                          data-date={day.date}
                          data-month-id={weekToMonth[weekIdx]}
                          data-week-id={weekIdx}
                          data-dimmed="false"
                          className={`heatmap-cell w-3 h-3 rounded-[4px] cursor-pointer ${getCellClasses(day.contributionCount)}`}
                        />
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Color Scale Legend */}
          <div
            className="flex items-center justify-end gap-2 mt-4 text-xs text-gray-400 font-medium select-none animate-stagger"
            style={{ animationDelay: "300ms" }}
          >
            <span>Low</span>
            <div className="w-3 h-3 rounded-[4px] bg-gray-200 dark:bg-[#1E2432] shadow-[inset_0_1px_2px_rgba(0,0,0,0.06),inset_0_1px_1px_rgba(255,255,255,0.5)] dark:shadow-[inset_0_1px_2px_rgba(0,0,0,0.3),inset_0_1px_1px_rgba(255,255,255,0.02)]" />
            <div className="w-3 h-3 rounded-[4px] bg-[#60A5FA] dark:bg-[#3B82F6]" />
            <div className="w-3 h-3 rounded-[4px] bg-[#818CF8] dark:bg-[#4F46E5]" />
            <div className="w-3 h-3 rounded-[4px] bg-[#2DD4BF] dark:bg-[#06B6D4]" />
            <div className="w-3 h-3 rounded-[4px] bg-[#34D399] dark:bg-[#14F195] shadow-[0_0_8px_rgba(52,211,153,0.5)] dark:shadow-[0_0_8px_rgba(20,241,149,0.35)]" />
            <span>High</span>
          </div>
        </div>
      ) : (
        <div className="relative z-10 p-6 bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark rounded-2xl text-center text-xs text-gray-400 font-medium mb-6">
          No calendar graph data retrieved from GraphQL.
        </div>
      )}

      {/* Activity Summary Metrics */}
      <div className="relative z-10 grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
        <MetricCard
          icon={<GitPullRequest size={18} />}
          title="Lifetime PRs"
          value={activity.lifetime_prs.toLocaleString()}
          color="text-indigo-500"
        />
        <MetricCard
          icon={<GitMerge size={18} />}
          title="Lifetime Issues"
          value={activity.lifetime_issues.toLocaleString()}
          color="text-blue-500"
        />
        <MetricCard
          icon={<Users size={18} />}
          title="Collaboration Ratio"
          value={`${Math.round(activity.collaboration_ratio_365)}%`}
          color="text-emerald-500"
        />
      </div>

      {/* Tooltip Portal */}
      <div
        className={`fixed z-50 pointer-events-none transition-all duration-200 ease-out ${tooltip.visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"}`}
        style={{ left: tooltip.x, top: tooltip.y }}
      >
        <div className="bg-white/80 dark:bg-[#1E2432]/85 backdrop-blur-md border border-gray-200/50 dark:border-gray-700/50 p-4 rounded-[1.25rem] shadow-xl flex flex-col min-w-[220px]">
          <div className="flex flex-col gap-1 mb-2">
            <span className="text-sm font-black text-gray-800 dark:text-white">
              {tooltip.date && formatDate(tooltip.date).weekday}
            </span>
            <div className="flex items-center gap-2 text-xs font-semibold text-gray-500 dark:text-gray-400">
              <CalendarDays size={12} />
              {tooltip.date && formatDate(tooltip.date).rest}
            </div>
          </div>
          <hr className="border-gray-200/60 dark:border-gray-700/60 my-2" />
          {tooltip.count > 0 ? (
            <div className="flex flex-col gap-2 mt-1">
              <div className="text-sm font-black text-gray-900 dark:text-white flex items-center gap-2">
                <div
                  className={`w-2.5 h-2.5 rounded-full shadow-inner ${getDotColor(tooltip.count)}`}
                />
                {tooltip.count} Contributions
              </div>
              {tooltip.streak > 1 && (
                <div className="text-xs font-bold text-orange-500 flex items-center gap-1.5">
                  🔥 Day {tooltip.streak} of streak
                </div>
              )}
              {tooltip.isAboveAverage && (
                <div className="text-xs font-bold text-emerald-500 flex items-center gap-1.5">
                  ⚡ Above daily average
                </div>
              )}
              {tooltip.diff !== 0 && (
                <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
                  {tooltip.diff > 0
                    ? `↑ +${tooltip.diff}`
                    : `↓ ${Math.abs(tooltip.diff)}`}{" "}
                  from yesterday
                </div>
              )}
            </div>
          ) : (
            <div className="mt-1 text-sm font-semibold text-gray-500 dark:text-gray-400 italic">
              No activity. Take a break? 🙂
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  icon,
  title,
  value,
  color,
}: {
  icon: React.ReactNode;
  title: string;
  value: string | number;
  color: string;
}) {
  return (
    <div
      className="p-4 rounded-2xl bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark flex items-center gap-4 animate-stagger"
      style={{ animationDelay: "300ms" }}
    >
      <div
        className={`p-3 rounded-xl bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark ${color}`}
      >
        {icon}
      </div>
      <div>
        <span className="text-[10px] text-gray-400 uppercase tracking-wider font-bold block">
          {title}
        </span>
        <span className="text-lg font-black text-gray-800 dark:text-white">
          {value}
        </span>
      </div>
    </div>
  );
}
