"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  Bot,
  Home,
  Activity,
  FolderGit2,
  Code2,
  GitCommit,
  GitPullRequest,
  CircleDot,
  Sparkles,
  Settings,
} from "lucide-react";
import SettingsModal from "./SettingsModal";

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Extract active profile username from pathname if available (e.g. /profile/gugilla-aakash)
  const isProfilePage = pathname.startsWith("/profile/");
  const activeUsername = isProfilePage ? pathname.split("/")[2] : null;

  const handleNavClick = (sectionId: string) => {
    if (sectionId === "repositories") {
      if (isProfilePage && activeUsername) {
        const params = new URLSearchParams(searchParams.toString());
        params.set("modal", "repos");
        router.push(`${pathname}?${params.toString()}`);
        return;
      }
    }

    if (pathname === "/") {
      if (sectionId === "overview")
        window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    } else {
      router.push(`/#${sectionId}`);
    }
  };

  const navItems = [
    { name: "Overview", id: "overview", icon: Home },
    { name: "Activity", id: "activity", icon: Activity },
    { name: "Repositories", id: "repositories", icon: FolderGit2 },
    { name: "Languages", id: "languages", icon: Code2 },
    { name: "Commits", id: "activity", icon: GitCommit },
    { name: "Pull Requests", id: "activity", icon: GitPullRequest },
    { name: "Issues", id: "activity", icon: CircleDot },
    { name: "AI Insights", id: "ai-insights", icon: Sparkles },
    { name: "Settings", id: "settings", icon: Settings },
  ];

  return (
    <>
      <aside className="w-64 h-screen flex-shrink-0 flex flex-col justify-between p-6 bg-neo-light dark:bg-neo-dark z-20 hidden md:flex border-r border-gray-200/50 dark:border-gray-800/50">
        <div>
          {/* Logo Area */}
          <Link
            href="/"
            className="flex items-center gap-3 mb-10 px-2 cursor-pointer"
          >
            <div className="p-2 rounded-xl bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark text-indigo-500">
              <Bot size={24} strokeWidth={2.5} />
            </div>
            <div>
              <h1 className="font-bold text-gray-800 dark:text-gray-100 leading-tight">
                GitHub Reviewer
              </h1>
              <p className="text-xs text-indigo-500 font-semibold">
                AI Powered
              </p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="space-y-3">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isSettings = item.id === "settings";

              return (
                <button
                  key={item.name}
                  onClick={() => {
                    if (isSettings) {
                      setIsSettingsOpen(true);
                    } else {
                      handleNavClick(item.id);
                    }
                  }}
                  className="w-full flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 font-medium text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-500 dark:hover:text-indigo-400 hover:shadow-neo-inset dark:hover:shadow-neo-inset-dark cursor-pointer text-left"
                >
                  <Icon size={18} />
                  {item.name}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Dynamic User Session Card (Bottom Left) */}
        <div className="flex items-center gap-3 p-3 rounded-2xl bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark">
          <div className="w-10 h-10 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-500 font-bold shadow-neo-inset dark:shadow-neo-inset-dark uppercase shrink-0">
            {activeUsername ? activeUsername.slice(0, 2) : "ME"}
          </div>
          <div className="truncate">
            <p className="text-sm font-bold text-gray-800 dark:text-gray-100 truncate">
              {activeUsername ? activeUsername : "Guest"}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
              {activeUsername ? `@${activeUsername}` : "@developer"}
            </p>
          </div>
        </div>
      </aside>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </>
  );
}
