'use client';

import { TabType } from '@/types';

interface LeaderboardTabsProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  counts: {
    borderless: number;
    github: number;
    all: number;
  };
}

const tabs: { id: TabType; label: string }[] = [
  { id: 'borderless', label: 'Borderless' },
  { id: 'github', label: 'GitHub' },
  { id: 'all', label: 'All' },
];

export default function LeaderboardTabs({
  activeTab,
  onTabChange,
  counts,
}: LeaderboardTabsProps) {
  return (
    <div className="flex gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
            activeTab === tab.id
              ? 'bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
          }`}
        >
          {tab.label}
          <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
            ({counts[tab.id].toLocaleString()})
          </span>
        </button>
      ))}
    </div>
  );
}
