"use client";

interface CircularRingProps {
  percentage: number;
  colorClass: string;
  size?: number;
  strokeWidth?: number;
}

export default function CircularRing({
  percentage,
  colorClass,
  size = 120,
  strokeWidth = 12,
}: CircularRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div
      className="relative flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      {/* Background Track (Neumorphic Inset) */}
      <svg className="absolute transform -rotate-90" width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-gray-300 dark:text-gray-800"
        />
        {/* Progress Fill */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={`transition-all duration-1000 ease-out ${colorClass}`}
        />
      </svg>
      {/* Center Text */}
      <div className="absolute flex flex-col items-center justify-center">
        <span className="text-xl font-black text-gray-800 dark:text-white">
          {Math.round(percentage)}
          <span className="text-sm">%</span>
        </span>
      </div>
    </div>
  );
}
