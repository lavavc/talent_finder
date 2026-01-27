'use client';

import { useState } from 'react';
import { Developer, TabType } from '@/types';

interface ShareModalProps {
  developer: Developer;
  tab: TabType;
  onClose: () => void;
}

export default function ShareModal({ developer, tab, onClose }: ShareModalProps) {
  const [copied, setCopied] = useState<'tweet' | 'badge' | null>(null);

  const tabLabel = tab === 'borderless' ? 'Borderless' : tab === 'github' ? 'GitHub' : 'All';
  const badgeUrl = `https://img.shields.io/badge/Borderless-Top 100-red.svg`;
  const leaderboardUrl = 'https://lavavc.github.io/talent_finder/';

  const tweetText = `Talent is borderless. Come build the future with me and see if you can beat my ranking of #${developer.rank} on the ${tabLabel} Developer Leaderboard! \u{1F3C6}\n\nCheck out the full leaderboard: ${leaderboardUrl}`;

  const badgeMarkdown = `[![Top 100 Borderless Developer](${badgeUrl})](${leaderboardUrl})`;

  const shareOnX = () => {
    const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}`;
    window.open(url, '_blank', 'width=550,height=420');
  };

  const copyToClipboard = async (text: string, type: 'tweet' | 'badge') => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(type);
      setTimeout(() => setCopied(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-lg w-full mx-4 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
            Share Your Achievement
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Share on X */}
        <div className={tab === 'borderless' ? 'mb-6' : ''}>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
            Share on X (Twitter)
          </h3>
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 mb-3">
            <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
              {tweetText}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={shareOnX}
              className="flex-1 px-4 py-2 bg-black text-white font-medium rounded-lg hover:bg-gray-800 transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
              Post on X
            </button>
            <button
              onClick={() => copyToClipboard(tweetText, 'tweet')}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              {copied === 'tweet' ? 'Copied!' : 'Copy'}
            </button>
          </div>
        </div>

        {/* GitHub Badge - only for Borderless tab */}
        {tab === 'borderless' && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Add Badge to GitHub Profile
            </h3>
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 mb-3">
              <div className="flex items-center gap-3 mb-3">
                <img
                  src={badgeUrl}
                  alt="Top 100 Borderless Badge"
                  className="h-8"
                />
                <span className="text-sm text-gray-500 dark:text-gray-400">Preview</span>
              </div>
              <code className="block text-xs text-gray-600 dark:text-gray-400 break-all font-mono bg-gray-100 dark:bg-gray-700 p-2 rounded">
                {badgeMarkdown}
              </code>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
              Add this to your GitHub profile README.md
            </p>
            <button
              onClick={() => copyToClipboard(badgeMarkdown, 'badge')}
              className="w-full px-4 py-2 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 font-medium rounded-lg hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors"
            >
              {copied === 'badge' ? 'Copied!' : 'Copy Badge Markdown'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
