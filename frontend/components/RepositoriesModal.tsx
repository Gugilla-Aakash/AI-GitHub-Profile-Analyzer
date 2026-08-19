"use client";

import { useEffect, useState } from "react";
import {
  X,
  Star,
  GitFork,
  ExternalLink,
  FolderGit2,
  Search,
} from "lucide-react";

interface Repository {
  id: number;
  name: string;
  description: string | null;
  html_url: string;
  stargazers_count: number;
  forks_count: number;
  language: string | null;
  updated_at: string;
}

interface RepositoriesModalProps {
  username: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function RepositoriesModal({
  username,
  isOpen,
  onClose,
}: RepositoriesModalProps) {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    if (!isOpen || !username) return;

    let isMounted = true;
    setIsLoading(true);

    fetch(
      `https://api.github.com/users/${username}/repos?sort=updated&per_page=100`,
    )
      .then((res) => res.json())
      .then((data) => {
        if (isMounted && Array.isArray(data)) {
          setRepos(data);
        }
      })
      .catch((err) => console.error("Failed to fetch repositories:", err))
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, username]);

  if (!isOpen) return null;

  const filteredRepos = repos.filter(
    (repo) =>
      repo.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (repo.description &&
        repo.description.toLowerCase().includes(searchQuery.toLowerCase())),
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 sm:p-6 animate-in fade-in duration-200">
      <div className="w-full max-w-4xl max-h-[85vh] flex flex-col bg-neo-light dark:bg-neo-dark rounded-[2rem] shadow-neo-outset dark:shadow-neo-outset-dark overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 sm:p-8 border-b border-gray-200 dark:border-gray-800 shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark text-indigo-500">
              <FolderGit2 size={20} />
            </div>
            <div>
              <h2 className="text-lg font-black text-gray-800 dark:text-white">
                Repository Insights
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Public repositories for @{username}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2.5 rounded-xl bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark active:shadow-neo-inset dark:active:shadow-neo-inset-dark text-gray-500 hover:text-indigo-500 transition-all cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        {/* Search Bar */}
        <div className="px-6 sm:px-8 pt-6 pb-2 shrink-0">
          <div className="relative w-full">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search repositories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark rounded-xl text-xs font-medium text-gray-800 dark:text-white placeholder-gray-400 focus:outline-none"
            />
          </div>
        </div>

        {/* Repositories Grid Body */}
        <div className="p-6 sm:p-8 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-400 dark:scrollbar-thumb-gray-700 flex-1">
          {isLoading ? (
            <div className="py-20 flex flex-col items-center justify-center text-center">
              <div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3" />
              <p className="text-xs text-gray-400 font-medium">
                Fetching repositories from GitHub...
              </p>
            </div>
          ) : filteredRepos.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredRepos.map((repo) => (
                <div
                  key={repo.id}
                  className="flex flex-col justify-between p-5 bg-neo-light dark:bg-neo-dark rounded-2xl shadow-neo-outset dark:shadow-neo-outset-dark transition-all hover:scale-[1.01]"
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <a
                        href={repo.html_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-sm font-bold text-gray-800 dark:text-white hover:text-indigo-500 flex items-center gap-1.5 transition-colors truncate"
                      >
                        {repo.name}{" "}
                        <ExternalLink size={12} className="shrink-0" />
                      </a>
                      {repo.language && (
                        <span className="px-2.5 py-0.5 text-[10px] font-bold rounded-full bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark text-indigo-500 shrink-0">
                          {repo.language}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 leading-relaxed">
                      {repo.description ||
                        "No description provided for this repository."}
                    </p>
                  </div>

                  <div className="flex items-center gap-4 pt-4 mt-4 border-t border-gray-200/50 dark:border-gray-800/50 text-xs font-semibold text-gray-500 dark:text-gray-400">
                    <span className="flex items-center gap-1">
                      <Star size={14} className="text-amber-500" />{" "}
                      {repo.stargazers_count}
                    </span>
                    <span className="flex items-center gap-1">
                      <GitFork size={14} className="text-indigo-500" />{" "}
                      {repo.forks_count}
                    </span>
                    <span className="ml-auto text-[10px] text-gray-400">
                      Updated {new Date(repo.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-20 text-center text-xs text-gray-400 font-medium">
              No repositories found matching your search.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
