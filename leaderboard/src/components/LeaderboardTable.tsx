'use client';

import { Developer } from '@/types';

interface LeaderboardTableProps {
  developers: Developer[];
  onUserClick: (developer: Developer) => void;
}

function getMedalEmoji(rank: number): string {
  switch (rank) {
    case 1:
      return '\u{1F947}';
    case 2:
      return '\u{1F948}';
    case 3:
      return '\u{1F949}';
    default:
      return '';
  }
}

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

export default function LeaderboardTable({
  developers,
  onUserClick,
}: LeaderboardTableProps) {
  return (
    <div className="table-container overflow-x-auto">
      <table className="w-full min-w-[800px]">
        <thead>
          <tr className="border-b border-gray-200 dark:border-gray-700">
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600 dark:text-gray-300">
              Rank
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600 dark:text-gray-300">
              Developer
            </th>
            <th className="px-4 py-3 text-right text-sm font-semibold text-gray-600 dark:text-gray-300">
              Score
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600 dark:text-gray-300">
              Languages
            </th>
            <th className="px-4 py-3 text-right text-sm font-semibold text-gray-600 dark:text-gray-300">
              Contributions
            </th>
            <th className="px-4 py-3 text-right text-sm font-semibold text-gray-600 dark:text-gray-300">
              Stars
            </th>
          </tr>
        </thead>
        <tbody>
          {developers.map((dev) => (
            <tr
              key={dev.username}
              onClick={() => onUserClick(dev)}
              className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer transition-colors"
            >
              <td className="px-4 py-3">
                <span className="flex items-center gap-2">
                  <span
                    className={`font-mono text-sm ${
                      dev.rank <= 3
                        ? 'font-bold text-amber-600 dark:text-amber-400'
                        : 'text-gray-600 dark:text-gray-400'
                    }`}
                  >
                    {dev.rank}
                  </span>
                  {dev.rank <= 3 && (
                    <span className="text-lg">{getMedalEmoji(dev.rank)}</span>
                  )}
                </span>
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-3">
                  <img
                    src={`https://github.com/${dev.username}.png?size=40`}
                    alt={dev.username}
                    className="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700"
                    loading="lazy"
                  />
                  <div>
                    <a
                      href={`https://github.com/${dev.username}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="font-medium text-gray-900 dark:text-gray-100 hover:text-blue-600 dark:hover:text-blue-400"
                    >
                      {dev.username}
                    </a>
                    {dev.location && (
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {dev.location}
                      </p>
                    )}
                  </div>
                </div>
              </td>
              <td className="px-4 py-3 text-right">
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  {dev.totalScore.toFixed(2)}
                </span>
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1">
                  {dev.topLanguages.slice(0, 3).map((lang) => (
                    <span
                      key={lang}
                      className="px-2 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                    >
                      {lang}
                    </span>
                  ))}
                  {dev.topLanguages.length > 3 && (
                    <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
                      +{dev.topLanguages.length - 3}
                    </span>
                  )}
                </div>
              </td>
              <td className="px-4 py-3 text-right">
                <span className="text-gray-700 dark:text-gray-300">
                  {formatNumber(dev.totalContributions)}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <span className="text-gray-700 dark:text-gray-300">
                  {formatNumber(dev.totalStars)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
