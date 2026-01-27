'use client';

import { useEffect, useCallback } from 'react';
import confetti from 'canvas-confetti';
import { Developer, TabType } from '@/types';

interface CelebrationModalProps {
  developer: Developer;
  tab: TabType;
  onClose: () => void;
  onShare: () => void;
}

export default function CelebrationModal({
  developer,
  tab,
  onClose,
  onShare,
}: CelebrationModalProps) {
  const fireConfetti = useCallback(() => {
    const duration = 3000;
    const end = Date.now() + duration;

    const colors = ['#ffd700', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96e6a1'];

    (function frame() {
      confetti({
        particleCount: 3,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
        colors: colors,
      });
      confetti({
        particleCount: 3,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
        colors: colors,
      });

      if (Date.now() < end) {
        requestAnimationFrame(frame);
      }
    })();
  }, []);

  useEffect(() => {
    fireConfetti();
  }, [fireConfetti]);

  const tabLabel = tab === 'borderless' ? 'Borderless' : tab === 'github' ? 'GitHub' : 'All';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-md w-full mx-4 p-8 text-center">
        <div className="text-6xl mb-4">
          {developer.rank === 1 ? '\u{1F3C6}' : developer.rank === 2 ? '\u{1F948}' : developer.rank === 3 ? '\u{1F949}' : '\u{1F389}'}
        </div>

        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Congratulations!
        </h2>

        <div className="flex items-center justify-center gap-3 mb-4">
          <img
            src={`https://github.com/${developer.username}.png?size=64`}
            alt={developer.username}
            className="w-16 h-16 rounded-full"
          />
          <div className="text-left">
            <p className="font-semibold text-gray-900 dark:text-gray-100">
              {developer.username}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Rank #{developer.rank} on {tabLabel}
            </p>
          </div>
        </div>

        <p className="text-gray-600 dark:text-gray-300 mb-6">
          You&apos;re in the <span className="font-bold text-amber-600 dark:text-amber-400">Top 100</span> developers!
          Share your achievement and add a badge to your GitHub profile.
        </p>

        <div className="flex flex-col gap-3">
          <button
            onClick={onShare}
            className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
          >
            Share
          </button>
          <button
            onClick={onClose}
            className="w-full px-6 py-3 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium rounded-lg transition-colors"
          >
            Maybe Later
          </button>
        </div>
      </div>
    </div>
  );
}
