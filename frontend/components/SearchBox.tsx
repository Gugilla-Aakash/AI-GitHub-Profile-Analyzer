"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { searchUsers } from "../lib/api";
import { Search, Sparkles, Loader2 } from "lucide-react";

export default function SearchBox() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [isFocused, setIsFocused] = useState(false);

  // New state to handle the intentional loading delay UX
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Your existing React Query logic
  const { data, isLoading } = useQuery({
    queryKey: ["searchUsers", query],
    queryFn: () => searchUsers(query),
    enabled: query.trim().length >= 2,
  });

  const items = Array.isArray(data)
    ? data
    : data && Array.isArray((data as any).items)
      ? (data as any).items
      : [];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      // Trigger the physical loading state
      setIsAnalyzing(true);
      // Intentional delay for perceived AI value
      setTimeout(() => {
        router.push(`/profile/${encodeURIComponent(query.trim())}`);
      }, 600);
    }
  };

  const handleDropdownClick = (username: string) => {
    setQuery(username);
    setIsAnalyzing(true);
    setTimeout(() => {
      router.push(`/profile/${encodeURIComponent(username)}`);
    }, 600);
  };

  return (
    <div className="relative mx-auto w-full max-w-xl">
      {/* 1. Updated Form Wrapper: Includes the focus-within glow and flex layout */}
      <form
        onSubmit={handleSubmit}
        className="group relative flex h-14 w-full items-center justify-between rounded-2xl bg-neo-light p-1.5 pl-4 shadow-neo-inset transition-all duration-300 focus-within:ring-1 focus-within:ring-indigo-500/30 focus-within:shadow-[inset_2px_2px_6px_#121419,inset_-2px_-2px_6px_#22262f,0_0_20px_rgba(99,102,241,0.15)] dark:bg-[#1a1d24] dark:shadow-[inset_4px_4px_8px_#121419,inset_-4px_-4px_8px_#22262f]"
      >
        <div className="flex h-full flex-1 items-center">
          {/* 2. Icon glows on focus */}
          <Search className="h-5 w-5 text-gray-400 transition-colors duration-300 group-focus-within:text-indigo-500 dark:text-gray-500" />

          {/* 3. Input with custom caret */}
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setTimeout(() => setIsFocused(false), 200)}
            placeholder="Enter GitHub username..."
            disabled={isAnalyzing}
            className="ml-3 h-full w-full bg-transparent text-sm font-medium text-gray-800 outline-none caret-indigo-500 placeholder:text-gray-500 disabled:opacity-50 dark:text-white dark:placeholder-gray-500"
          />
        </div>

        {/* 4. Physical Neumorphic Button */}
        <button
          type="submit"
          disabled={isAnalyzing || !query.trim()}
          className="flex h-full min-w-[120px] items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-500 px-5 text-sm font-bold text-white shadow-neo-outset transition-all duration-300 hover:-translate-y-[2px] hover:shadow-[0_8px_16px_rgba(99,102,241,0.3)] hover:brightness-110 active:translate-y-[1px] active:shadow-[inset_0_4px_8px_rgba(0,0,0,0.2)] disabled:pointer-events-none disabled:opacity-70 dark:shadow-neo-outset-dark"
        >
          {isAnalyzing ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Sparkles size={14} />
              Analyze
            </>
          )}
        </button>
      </form>

      {/* 5. Your Unchanged Autocomplete Dropdown Logic */}
      {isFocused && query.trim().length >= 2 && (
        <div className="absolute left-0 right-0 z-50 mt-4 overflow-hidden rounded-2xl bg-neo-light p-2 shadow-neo-outset dark:bg-[#1a1d24] dark:shadow-[10px_10px_20px_#121419,-10px_-10px_20px_#22262f]">
          {isLoading ? (
            <div className="p-4 text-center text-xs font-medium text-gray-500 dark:text-gray-400">
              Searching GitHub users...
            </div>
          ) : items.length > 0 ? (
            <div className="space-y-1">
              {items.slice(0, 6).map((item: any) => (
                <button
                  key={item.login}
                  onClick={() => handleDropdownClick(item.login)}
                  className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left transition-all hover:shadow-neo-inset dark:hover:shadow-[inset_4px_4px_8px_#121419,inset_-4px_-4px_8px_#22262f]"
                >
                  {item.avatar_url && (
                    <img
                      src={item.avatar_url}
                      alt={item.login}
                      className="h-8 w-8 rounded-full shadow-sm"
                    />
                  )}
                  <span className="text-sm font-bold text-gray-700 dark:text-gray-200">
                    @{item.login}
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <div className="p-4 text-center text-xs font-medium text-gray-500 dark:text-gray-400">
              No matching users found.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
