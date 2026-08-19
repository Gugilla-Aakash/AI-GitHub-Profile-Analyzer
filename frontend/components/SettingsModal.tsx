"use client";

import { X, Moon, Sun, Database } from "lucide-react";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  if (!isOpen) return null;

  const toggleTheme = () => {
    document.documentElement.classList.toggle("dark");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-md p-8 bg-neo-light dark:bg-neo-dark rounded-[2rem] shadow-neo-outset dark:shadow-neo-outset-dark space-y-6 relative">
        <div className="flex items-center justify-between pb-4 border-b border-gray-200 dark:border-gray-800">
          <h3 className="text-lg font-black text-gray-800 dark:text-white">
            Dashboard Settings
          </h3>
          <button
            onClick={onClose}
            className="p-2.5 rounded-xl bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark text-gray-500 hover:text-indigo-500 transition-all cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 rounded-2xl bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark">
            <div className="flex items-center gap-3">
              <Sun size={18} className="text-indigo-500 dark:hidden" />
              <Moon size={18} className="text-indigo-500 hidden dark:block" />
              <span className="text-sm font-bold text-gray-700 dark:text-gray-200">
                Appearance Mode
              </span>
            </div>
            <button
              onClick={toggleTheme}
              className="px-4 py-2 text-xs font-bold bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark active:shadow-neo-inset dark:active:shadow-neo-inset-dark rounded-xl text-indigo-500 transition-all cursor-pointer"
            >
              Toggle Theme
            </button>
          </div>

          <div className="flex items-center justify-between p-4 rounded-2xl bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark">
            <div className="flex items-center gap-3">
              <Database size={18} className="text-indigo-500" />
              <span className="text-sm font-bold text-gray-700 dark:text-gray-200">
                Clear Local Cache
              </span>
            </div>
            <button
              onClick={() => {
                localStorage.clear();
                window.location.reload();
              }}
              className="px-4 py-2 text-xs font-bold bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark active:shadow-neo-inset dark:active:shadow-neo-inset-dark rounded-xl text-red-500 transition-all cursor-pointer"
            >
              Clear Storage
            </button>
          </div>
        </div>

        <div className="pt-2">
          <button
            onClick={onClose}
            className="w-full py-3 bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-bold rounded-xl shadow-neo-outset dark:shadow-neo-outset-dark transition-all cursor-pointer"
          >
            Save & Close
          </button>
        </div>
      </div>
    </div>
  );
}
