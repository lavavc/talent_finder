'use client';

import { useState, useMemo, useCallback } from 'react';
import { Developer, TabType } from '@/types';
import LeaderboardTabs from './LeaderboardTabs';
import LeaderboardTable from './LeaderboardTable';
import SearchBar from './SearchBar';
import Pagination from './Pagination';
import CelebrationModal from './CelebrationModal';
import ShareModal from './ShareModal';

import borderlessData from '@/data/borderless.json';
import githubData from '@/data/github.json';
import allData from '@/data/all.json';

const ITEMS_PER_PAGE = 25;

export default function Leaderboard() {
  const [activeTab, setActiveTab] = useState<TabType>('borderless');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [celebratingUser, setCelebratingUser] = useState<Developer | null>(null);
  const [shareUser, setShareUser] = useState<Developer | null>(null);
  const [showShareModal, setShowShareModal] = useState(false);

  const data: Record<TabType, Developer[]> = useMemo(
    () => ({
      borderless: borderlessData as Developer[],
      github: githubData as Developer[],
      all: allData as Developer[],
    }),
    []
  );

  const filteredData = useMemo(() => {
    const currentData = data[activeTab];
    if (!searchQuery.trim()) return currentData;

    const query = searchQuery.toLowerCase();
    return currentData.filter((dev) =>
      dev.username.toLowerCase().includes(query)
    );
  }, [data, activeTab, searchQuery]);

  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    return filteredData.slice(start, end);
  }, [filteredData, currentPage]);

  const totalPages = Math.ceil(filteredData.length / ITEMS_PER_PAGE);

  const handleTabChange = useCallback((tab: TabType) => {
    setActiveTab(tab);
    setCurrentPage(1);
    setSearchQuery('');
  }, []);

  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
    setCurrentPage(1);
  }, []);

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const handleUserClick = useCallback((developer: Developer) => {
    // Check if user is in top 100 for current tab
    if (developer.rank <= 100) {
      setCelebratingUser(developer);
    }
  }, []);

  const handleCloseCelebration = useCallback(() => {
    setCelebratingUser(null);
  }, []);

  const handleShowShare = useCallback(() => {
    setShareUser(celebratingUser);
    setCelebratingUser(null);
    setShowShareModal(true);
  }, [celebratingUser]);

  const handleCloseShare = useCallback(() => {
    setShowShareModal(false);
    setShareUser(null);
  }, []);

  const counts = useMemo(
    () => ({
      borderless: data.borderless.length,
      github: data.github.length,
      all: data.all.length,
    }),
    [data]
  );

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Borderless Talent
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Discover top developers from around the world
        </p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <SearchBar onSearch={handleSearch} />
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <LeaderboardTabs
          activeTab={activeTab}
          onTabChange={handleTabChange}
          counts={counts}
        />
      </div>

      {/* Results info */}
      {searchQuery && (
        <div className="mb-4 text-sm text-gray-600 dark:text-gray-400">
          Found {filteredData.length} developer{filteredData.length !== 1 ? 's' : ''} matching &quot;{searchQuery}&quot;
        </div>
      )}

      {/* Table */}
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden mb-6">
        {paginatedData.length > 0 ? (
          <LeaderboardTable developers={paginatedData} onUserClick={handleUserClick} />
        ) : (
          <div className="p-12 text-center text-gray-500 dark:text-gray-400">
            No developers found matching your search.
          </div>
        )}
      </div>

      {/* Pagination */}
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={handlePageChange}
      />

      {/* Celebration Modal */}
      {celebratingUser && (
        <CelebrationModal
          developer={celebratingUser}
          tab={activeTab}
          onClose={handleCloseCelebration}
          onShare={handleShowShare}
        />
      )}

      {/* Share Modal */}
      {showShareModal && shareUser && (
        <ShareModal
          developer={shareUser}
          tab={activeTab}
          onClose={handleCloseShare}
        />
      )}
    </div>
  );
}
