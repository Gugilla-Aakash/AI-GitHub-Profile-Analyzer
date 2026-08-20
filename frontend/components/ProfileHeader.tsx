"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Search, Sparkles, Sun, Moon } from "lucide-react";

interface GitHubUserSuggestion {
  login: string;
  avatar_url: string;
  id: number;
}

export default function ProfileHeader() {
  const [inputUsername, setInputUsername] = useState("");
  const [suggestions, setSuggestions] = useState<GitHubUserSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const query = inputUsername.trim();
    if (!query) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsLoading(true);
      try {
        const res = await fetch(
          `https://api.github.com/search/users?q=${encodeURIComponent(query)}&per_page=5`,
        );
        if (res.ok) {
          const data = await res.json();
          setSuggestions(data.items || []);
          setIsOpen(true);
        }
      } catch (error) {
        console.error("Failed to fetch user suggestions:", error);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [inputUsername]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelectUser = (login: string) => {
    router.push(`/profile/${login}`);
    setInputUsername("");
    setIsOpen(false);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputUsername.trim()) {
      handleSelectUser(inputUsername.trim());
    }
  };

  // Toggle dark mode function
  const toggleTheme = () => {
    document.documentElement.classList.toggle("dark");
  };

  return (
    <header className="flex items-center justify-between gap-6 mb-8 w-full">
      {/* Top Search Bar */}
      <div ref={containerRef} className="relative flex-1 max-w-2xl">
        <form onSubmit={handleSearch} className="flex items-center gap-3">
          <div className="relative w-full">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
            <input
              type="text"
              placeholder="Enter GitHub username..."
              value={inputUsername}
              onChange={(e) => setInputUsername(e.target.value)}
              onFocus={() => suggestions.length > 0 && setIsOpen(true)}
              className="w-full pl-11 pr-4 py-3 text-sm font-medium bg-neo-light dark:bg-neo-dark rounded-xl text-gray-800 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 shadow-neo-inset dark:shadow-neo-inset-dark focus:outline-none transition-all"
            />
            {isLoading && (
              <div className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            )}
          </div>
          <button
            type="submit"
            className="px-5 py-3 text-sm font-bold bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl transition-all shadow-neo-outset dark:shadow-neo-outset-dark flex items-center gap-2 shrink-0"
          >
            <Sparkles size={16} />
            Analyze
          </button>
        </form>

        {/* Live Search Suggestions Dropdown */}
        {isOpen && suggestions.length > 0 && (
          <div className="absolute left-0 w-full mt-3 bg-neo-light dark:bg-neo-dark rounded-xl shadow-neo-outset dark:shadow-neo-outset-dark overflow-hidden z-50 p-2">
            <div className="space-y-1">
              {suggestions.map((user) => (
                <button
                  key={user.id}
                  type="button"
                  onClick={() => handleSelectUser(user.login)}
                  className="w-full text-left px-4 py-3 rounded-lg hover:shadow-neo-inset dark:hover:shadow-neo-inset-dark flex items-center gap-3 transition-all"
                >
                  <img
                    src={user.avatar_url}
                    alt={user.login}
                    className="w-7 h-7 rounded-full"
                  />
                  <span className="text-sm font-bold text-gray-700 dark:text-gray-200">
                    {user.login}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Theme Toggle placeholder (matching top right of reference) */}
      <button
        onClick={toggleTheme}
        className="p-3 rounded-xl bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark text-gray-600 dark:text-gray-300 hover:text-indigo-500 transition-colors shrink-0"
      >
        <span className="hidden dark:block">
          <Sun size={20} />
        </span>
        <span className="block dark:hidden">
          <Moon size={20} />
        </span>
      </button>
    </header>
  );
}
