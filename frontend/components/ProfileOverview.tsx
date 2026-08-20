"use client";

import { useEffect, useState } from "react";
import {
  MapPin,
  Link as LinkIcon,
  Star,
  Users,
  FolderGit2,
  Rocket,
} from "lucide-react";
import CircularRing from "./CircularRing";

interface ProfileOverviewProps {
  username: string;
  grade: string;
  finalScore: number;
  totalStars: number;
}

export default function ProfileOverview({
  username,
  grade,
  finalScore,
  totalStars,
}: ProfileOverviewProps) {
  const [ghData, setGhData] = useState<any>(null);

  useEffect(() => {
    fetch(`https://api.github.com/users/${username}`)
      .then((res) => res.json())
      .then((data) => setGhData(data))
      .catch((err) => console.error("Failed to fetch GH data", err));
  }, [username]);

  return (
    <div className="flex flex-col md:flex-row items-center md:items-start justify-between p-8 bg-neo-light dark:bg-neo-dark rounded-[2rem] shadow-neo-outset dark:shadow-neo-outset-dark gap-8 w-full">
      {/* Left side: Profile Info */}
      <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 w-full">
        {/* Avatar */}
        <div className="relative p-2 rounded-full bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark shrink-0">
          <div className="w-24 h-24 sm:w-32 sm:h-32 rounded-full overflow-hidden shadow-neo-inset dark:shadow-neo-inset-dark p-1">
            <img
              src={ghData?.avatar_url || `https://github.com/${username}.png`}
              alt={username}
              className="w-full h-full rounded-full object-cover"
            />
          </div>
        </div>

        {/* Info & Stats */}
        <div className="flex flex-col items-center sm:items-start text-center sm:text-left flex-1 w-full">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-black text-gray-800 dark:text-white">
              {ghData?.name || username}
            </h1>
            <span className="p-1 bg-indigo-500 text-white rounded-full">
              <Rocket size={14} />
            </span>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-md">
            {ghData?.bio || "Open Source Enthusiast"}
          </p>

          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-4 mt-3 text-xs font-medium text-gray-500 dark:text-gray-400">
            {ghData?.location && (
              <span className="flex items-center gap-1">
                <MapPin size={14} /> {ghData.location}
              </span>
            )}
            <a
              href={`https://github.com/${username}`}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 hover:text-indigo-500 transition-colors"
            >
              <LinkIcon size={14} /> github.com/{username}
            </a>
          </div>

          {/* Quick Stats Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 w-full">
            {[
              {
                label: "Repositories",
                val: ghData?.public_repos || 0,
                icon: FolderGit2,
              },
              { label: "Followers", val: ghData?.followers || 0, icon: Users },
              { label: "Following", val: ghData?.following || 0, icon: Users },
              { label: "Stars", val: totalStars, icon: Star },
            ].map((stat, i) => (
              <div
                key={i}
                className="flex flex-col items-center justify-center py-3 rounded-2xl bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark"
              >
                <stat.icon size={16} className="text-indigo-500 mb-1" />
                <span className="text-lg font-bold text-gray-800 dark:text-white">
                  {stat.val}
                </span>
                <span className="text-[10px] text-gray-500 uppercase tracking-wider">
                  {stat.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right side: Overall Grade */}
      <div className="flex flex-col items-center justify-center shrink-0">
        <span className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
          Overall Grade
        </span>
        <div className="relative">
          <CircularRing
            percentage={finalScore}
            colorClass="text-indigo-500"
            size={140}
            strokeWidth={14}
          />
          {/* Grade overlay */}
          <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 px-4 py-1 bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark rounded-full">
            <span className="text-lg font-black text-indigo-500">{grade}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
