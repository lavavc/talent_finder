export interface Developer {
  rank: number;
  username: string;
  totalScore: number;
  followers: number;
  location?: string;
  activityScore: number;
  activityDensity: number;
  contributionDensity: number;
  totalContributions: number;
  totalStars: number;
  topLanguages: string[];
  hasSolidity: boolean;
  hasRust: boolean;
  hasGo: boolean;
  hasTypescript: boolean;
  hasMobile: boolean;
}

export type TabType = 'borderless' | 'github' | 'all';

export interface LeaderboardData {
  borderless: Developer[];
  github: Developer[];
  all: Developer[];
}
