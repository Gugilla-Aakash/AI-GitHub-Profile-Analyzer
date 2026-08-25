"use client";

import SearchBox from "@/components/SearchBox";
import { Sparkles, Activity, Check } from "lucide-react";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { useEffect, useState, Suspense } from "react";

export default function HomePage() {
  // --- 1. Apple-Style Mouse Parallax (Point 2: Tiny 3D Hover) ---
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const mouseXSpring = useSpring(x, { stiffness: 150, damping: 35 });
  const mouseYSpring = useSpring(y, { stiffness: 150, damping: 35 });

  // Adjusted to exactly 2deg X and 3deg Y for that subtle premium feel
  const rotateX = useTransform(mouseYSpring, [-0.5, 0.5], ["2deg", "-2deg"]);
  const rotateY = useTransform(mouseXSpring, [-0.5, 0.5], ["-3deg", "3deg"]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    x.set(mouseX / width - 0.5);
    y.set(mouseY / height - 0.5);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  // --- 2. Heatmap Living Data Simulation (Point 1: Animate Forever) ---
  const [activeCells, setActiveCells] = useState<number[]>([]);
  useEffect(() => {
    const basePattern = [0, 5, 7, 12, 14, 21, 25, 28, 33];
    setActiveCells(basePattern);

    const interval = setInterval(() => {
      const newPattern = [...basePattern];
      // Randomly pick 2 to 4 cells to brighten every 4.5 seconds
      const extraCells = Math.floor(Math.random() * 3) + 2;
      for (let i = 0; i < extraCells; i++) {
        newPattern.push(Math.floor(Math.random() * 36));
      }
      setActiveCells(newPattern); // Old random cells fade, new ones light up
    }, 4500);

    return () => clearInterval(interval);
  }, []);

  const staggerContainer = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.12 } },
  };

  const fadeUp = {
    hidden: { opacity: 0, y: 20, filter: "blur(4px)" },
    show: {
      opacity: 1,
      y: 0,
      filter: "blur(0px)",
      transition: { duration: 0.7, ease: "easeOut" },
    },
  } as any;

  return (
    <main className="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-gray-50 px-6 py-12 dark:bg-[#181a22] lg:px-12 xl:px-24">
      {/* Background Grid & Centralized Glow */}
      <motion.div
        animate={{ y: [0, -24, 0] }}
        transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
        className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:24px_24px] opacity-60"
      />
      <motion.div
        animate={{ opacity: [0.15, 0.3, 0.15], scale: [1, 1.05, 1] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        className="pointer-events-none absolute left-1/2 top-1/2 h-[60%] w-[60%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-indigo-500/10 blur-[140px]"
      />

      <div className="relative z-10 grid w-full max-w-7xl grid-cols-1 items-center gap-16 lg:grid-cols-2">
        {/* LEFT COLUMN */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="show"
          className="flex flex-col space-y-8"
        >
          <motion.div
            variants={fadeUp}
            className="inline-flex w-max items-center gap-2 rounded-full px-4 py-2 text-xs font-bold uppercase tracking-wider text-indigo-500 shadow-neo-inset dark:bg-[#1a1d24] dark:shadow-[inset_2px_2px_4px_#121419,inset_-2px_-2px_4px_#22262f]"
          >
            <Sparkles size={14} /> GitHub Profile Intelligence
          </motion.div>

          <motion.div variants={fadeUp} className="space-y-6">
            <h1 className="text-5xl font-black leading-tight tracking-tight text-gray-800 dark:text-white sm:text-6xl lg:text-[4.5rem]">
              Audit & Analyze <br />
              <span className="bg-gradient-to-r from-indigo-500 to-purple-500 bg-clip-text text-transparent drop-shadow-sm">
                Any GitHub Profile
              </span>
            </h1>
            <p className="max-w-xl text-lg font-medium leading-relaxed text-gray-500 dark:text-gray-400">
              Get an instant AI-powered audit report, activity heatmaps, skill
              domain breakdowns, and chat directly with developer profiles.
            </p>
          </motion.div>

          <motion.div variants={fadeUp} className="mt-10 space-y-6">
            <div className="relative w-full max-w-lg">
              {/* Wrapped SearchBox in Suspense */}
              <Suspense
                fallback={
                  <div className="h-14 w-full rounded-2xl bg-neo-light dark:bg-[#1a1d24] shadow-neo-inset animate-pulse" />
                }
              >
                <SearchBox />
              </Suspense>
            </div>

            <div className="flex items-center gap-2 text-sm font-medium text-gray-400 dark:text-gray-500">
              <svg
                className="h-4 w-4 text-emerald-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
              No sign-in required • Public profiles only
            </div>

            <div className="pt-4 space-y-3">
              <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                Everything Included
              </p>
              <div className="flex flex-wrap gap-3">
                {[
                  "AI Repository Review",
                  "Contribution Heatmaps",
                  "Language Analysis",
                  "PDF Reports",
                ].map((feature) => (
                  <motion.div
                    key={feature}
                    whileHover={{ y: -3, scale: 1.02 }}
                    className="group flex cursor-default items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold text-gray-600 shadow-neo-outset transition-shadow hover:shadow-[0_0_15px_rgba(99,102,241,0.15)] dark:bg-[#20232c] dark:text-gray-300 dark:shadow-[4px_4px_8px_#15171d,-4px_-4px_8px_#2b2f3b]"
                  >
                    <Check
                      strokeWidth={3}
                      className="h-4 w-4 text-indigo-500 transition-transform duration-300 group-hover:rotate-12 group-hover:scale-110"
                    />{" "}
                    {feature}
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* RIGHT COLUMN */}
        <motion.div
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.5, ease: "easeOut" }}
          className="relative mx-auto mt-8 hidden w-full max-w-[420px] lg:block [perspective:1000px]"
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        >
          {/* Main 3D Container (Added scale: 1.01 on hover) */}
          <motion.div
            style={{ rotateX, rotateY }}
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
            whileHover={{ scale: 1.01 }}
            className="group relative w-full"
          >
            {/* AI Scanning Line */}
            <motion.div
              animate={{ top: ["-10%", "110%"], opacity: [0, 1, 1, 0] }}
              transition={{
                duration: 2.5,
                ease: "linear",
                repeat: Infinity,
                repeatDelay: 8,
              }}
              className="absolute left-0 right-0 z-50 h-[2px] bg-indigo-500 shadow-[0_0_20px_2px_#6366f1]"
            />

            {/* Floating Grade Badge */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{
                opacity: 1,
                scale: 1,
                y: [0, -4, 0],
                rotate: [-1, 1, -1],
              }}
              transition={{
                opacity: { delay: 1, duration: 0.5 },
                scale: { delay: 1, duration: 0.5 },
                y: { duration: 5, repeat: Infinity, ease: "easeInOut" },
                rotate: { duration: 6, repeat: Infinity, ease: "easeInOut" },
              }}
              className="absolute -left-10 top-8 z-20 rounded-2xl border border-transparent bg-neo-light p-4 shadow-neo-outset dark:border-white/5 dark:bg-[#20232c] dark:shadow-[6px_6px_12px_#15171d,-6px_-6px_12px_#2b2f3b]"
            >
              <div className="text-sm font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-br from-indigo-400 to-purple-500 drop-shadow-[0_2px_4px_rgba(99,102,241,0.4)]">
                GRADE A-
              </div>
            </motion.div>

            {/* Main Card Element */}
            <div className="relative z-10 flex w-full flex-col gap-6 rounded-[2.5rem] border border-transparent bg-neo-light p-8 shadow-neo-outset transition-shadow duration-500 group-hover:shadow-[20px_20px_40px_rgba(21,23,29,0.8),-20px_-20px_40px_rgba(43,47,59,0.5)] dark:border-white/5 dark:bg-[#20232c] dark:shadow-[12px_12px_24px_#15171d,-12px_-12px_24px_#2b2f3b]">
              <div className="flex items-center gap-5">
                <div className="h-16 w-16 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 shadow-neo-outset dark:from-[#1a1d24] dark:to-[#1a1d24] dark:shadow-[inset_4px_4px_8px_#121419,inset_-4px_-4px_8px_#22262f]" />
                <div className="flex flex-col gap-3">
                  <div className="h-4 w-32 rounded-full bg-gradient-to-r from-gray-200 to-gray-100 shadow-neo-inset dark:from-[#1a1d24] dark:to-[#1a1d24] dark:shadow-[inset_2px_2px_4px_#121419,inset_-2px_-2px_4px_#22262f]" />
                  <div className="h-3 w-20 rounded-full bg-gradient-to-r from-gray-200 to-gray-100 shadow-neo-inset dark:from-[#1a1d24] dark:to-[#1a1d24] dark:shadow-[inset_2px_2px_4px_#121419,inset_-2px_-2px_4px_#22262f]" />
                </div>
              </div>

              {/* Heatmap Matrix */}
              <div className="flex w-full flex-col gap-4 rounded-3xl bg-gray-50/50 p-6 shadow-neo-inset dark:bg-[#1a1d24] dark:shadow-[inset_6px_6px_12px_#121419,inset_-6px_-6px_12px_#22262f]">
                <div className="h-3 w-24 rounded-full bg-gray-200 shadow-[inset_1px_1px_2px_rgba(0,0,0,0.2)] dark:bg-[#15171d]" />
                <div className="grid grid-cols-12 gap-2 opacity-90">
                  {[...Array(36)].map((_, i) => {
                    const isActive = activeCells.includes(i);
                    return (
                      <div
                        key={i}
                        className={`h-3 w-full rounded-[3px] transition-all duration-1000 ${isActive ? "bg-gradient-to-br from-indigo-400 to-purple-500 shadow-[0_0_10px_rgba(139,92,246,0.5)]" : "bg-gray-200 shadow-neo-inset dark:bg-[#20232c] dark:shadow-[inset_1px_1px_3px_#121419]"}`}
                      />
                    );
                  })}
                </div>
              </div>

              {/* Language Bars (Point 3: Only animate once inherently) */}
              <div className="flex-1 space-y-6 rounded-3xl bg-gray-50/50 p-6 shadow-neo-inset dark:bg-[#1a1d24] dark:shadow-[inset_6px_6px_12px_#121419,inset_-6px_-6px_12px_#22262f]">
                <div className="h-3 w-28 rounded-full bg-gray-200 shadow-[inset_1px_1px_2px_rgba(0,0,0,0.2)] dark:bg-[#15171d]" />
                <div className="space-y-5 pt-2">
                  {[
                    { name: "Python", width: "85%", delay: 1.2 },
                    { name: "TypeScript", width: "60%", delay: 1.4 },
                    { name: "C++", width: "40%", delay: 1.6 },
                  ].map((lang) => (
                    <div key={lang.name} className="flex flex-col gap-2">
                      <span className="text-xs font-bold tracking-wide text-gray-500 dark:text-gray-400">
                        {lang.name}
                      </span>
                      <div className="h-2.5 w-full overflow-hidden rounded-full bg-gray-200 shadow-neo-inset dark:bg-[#15171d] dark:shadow-[inset_2px_2px_5px_#101217,inset_-2px_-2px_5px_#1e222a]">
                        <motion.div
                          initial={{ width: "0%" }}
                          animate={{ width: lang.width }}
                          transition={{
                            duration: 1.5,
                            delay: lang.delay,
                            ease: "easeOut",
                          }}
                          className="relative h-full rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-400"
                        >
                          <div className="absolute left-0 right-0 top-0 h-[1px] rounded-t-full bg-white/30" />
                          <div className="absolute inset-0 rounded-full bg-indigo-500 opacity-40 blur-[6px] dark:opacity-60" />
                        </motion.div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Heartbeat Activity Icon */}
            <motion.div
              animate={{ scale: [1, 1.08, 1], opacity: [0.7, 1, 0.7] }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              className="absolute -right-6 bottom-20 z-20 rounded-2xl border border-transparent bg-neo-light p-4 shadow-neo-outset dark:border-white/5 dark:bg-[#20232c] dark:shadow-[6px_6px_12px_#15171d,-6px_-6px_12px_#2b2f3b]"
            >
              <Activity className="h-6 w-6 text-purple-500 drop-shadow-[0_0_8px_rgba(168,85,247,0.6)]" />
            </motion.div>
          </motion.div>
        </motion.div>
      </div>
    </main>
  );
}
