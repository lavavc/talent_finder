import { parse } from 'csv-parse/sync';
import * as fs from 'fs';
import * as path from 'path';

interface RawBorderlessRow {
  username: string;
  total_score: string;
  followers: string;
  location?: string;
  activity_score: string;
  activity_density: string;
  contribution_density: string;
  total_contributions: string;
  total_stars: string;
  top_languages: string;
  has_solidity: string;
  has_rust: string;
  has_go?: string;
  has_typescript: string;
  has_mobile: string;
  source?: string;
  source_user?: string;
  error?: string;
}

interface RawGayanRow {
  username: string;
  total_score: string;
  followers: string;
  activity_score: string;
  activity_density: string;
  contribution_density: string;
  total_contributions: string;
  total_stars: string;
  top_languages: string;
  has_solidity: string;
  has_rust: string;
  has_typescript: string;
  has_mobile: string;
  error?: string;
}

interface Developer {
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

function parseBoolean(value: string | undefined): boolean {
  if (!value) return false;
  const lower = value.toLowerCase().trim();
  return lower === 'true' || lower === '1' || lower === 'yes';
}

function parseLanguages(value: string): string[] {
  if (!value) return [];
  // Remove quotes and split by comma
  return value
    .replace(/^["']|["']$/g, '')
    .split(',')
    .map((lang) => lang.trim())
    .filter((lang) => lang.length > 0);
}

function processBorderlessCSV(filePath: string): Developer[] {
  const content = fs.readFileSync(filePath, 'utf-8');
  const records = parse(content, {
    columns: true,
    skip_empty_lines: true,
    relax_quotes: true,
    relax_column_count: true,
  }) as RawBorderlessRow[];

  return records
    .filter((row) => row.username && !row.error)
    .map((row, index) => ({
      rank: index + 1,
      username: row.username.trim(),
      totalScore: parseFloat(row.total_score) || 0,
      followers: parseInt(row.followers) || 0,
      location: row.location?.replace(/^['"]|['"]$/g, '').trim() || undefined,
      activityScore: parseFloat(row.activity_score) || 0,
      activityDensity: parseFloat(row.activity_density) || 0,
      contributionDensity: parseFloat(row.contribution_density) || 0,
      totalContributions: parseInt(row.total_contributions) || 0,
      totalStars: parseInt(row.total_stars) || 0,
      topLanguages: parseLanguages(row.top_languages),
      hasSolidity: parseBoolean(row.has_solidity),
      hasRust: parseBoolean(row.has_rust),
      hasGo: parseBoolean(row.has_go),
      hasTypescript: parseBoolean(row.has_typescript),
      hasMobile: parseBoolean(row.has_mobile),
    }))
    .sort((a, b) => b.totalScore - a.totalScore)
    .map((dev, index) => ({ ...dev, rank: index + 1 }));
}

function processGayanCSV(filePath: string): Developer[] {
  const content = fs.readFileSync(filePath, 'utf-8');
  const records = parse(content, {
    columns: true,
    skip_empty_lines: true,
    relax_quotes: true,
    relax_column_count: true,
  }) as RawGayanRow[];

  return records
    .filter((row) => row.username && !row.error)
    .map((row, index) => ({
      rank: index + 1,
      username: row.username.trim(),
      totalScore: parseFloat(row.total_score) || 0,
      followers: parseInt(row.followers) || 0,
      location: undefined,
      activityScore: parseFloat(row.activity_score) || 0,
      activityDensity: parseFloat(row.activity_density) || 0,
      contributionDensity: parseFloat(row.contribution_density) || 0,
      totalContributions: parseInt(row.total_contributions) || 0,
      totalStars: parseInt(row.total_stars) || 0,
      topLanguages: parseLanguages(row.top_languages),
      hasSolidity: parseBoolean(row.has_solidity),
      hasRust: parseBoolean(row.has_rust),
      hasGo: false,
      hasTypescript: parseBoolean(row.has_typescript),
      hasMobile: parseBoolean(row.has_mobile),
    }))
    .sort((a, b) => b.totalScore - a.totalScore)
    .map((dev, index) => ({ ...dev, rank: index + 1 }));
}

function deduplicateAndMerge(borderless: Developer[], gayan: Developer[]): Developer[] {
  const userMap = new Map<string, Developer>();

  // Add borderless first (they take precedence if same score)
  for (const dev of borderless) {
    const key = dev.username.toLowerCase();
    if (!userMap.has(key) || userMap.get(key)!.totalScore < dev.totalScore) {
      userMap.set(key, dev);
    }
  }

  // Add gayan, keeping higher scores
  for (const dev of gayan) {
    const key = dev.username.toLowerCase();
    if (!userMap.has(key) || userMap.get(key)!.totalScore < dev.totalScore) {
      userMap.set(key, dev);
    }
  }

  return Array.from(userMap.values())
    .sort((a, b) => b.totalScore - a.totalScore)
    .map((dev, index) => ({ ...dev, rank: index + 1 }));
}

function main() {
  const rootDir = path.resolve(__dirname, '../..');
  const outputDir = path.resolve(__dirname, '../src/data');

  // Ensure output directory exists
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const borderlessPath = path.join(rootDir, 'borderless_processed.csv');
  const gayanPath = path.join(rootDir, 'gayan_processed.csv');

  console.log('Processing borderless_processed.csv...');
  const borderless = processBorderlessCSV(borderlessPath);
  console.log(`  Found ${borderless.length} developers`);

  console.log('Processing gayan_processed.csv...');
  const gayan = processGayanCSV(gayanPath);
  console.log(`  Found ${gayan.length} developers`);

  console.log('Merging and deduplicating for "All" tab...');
  const all = deduplicateAndMerge(borderless, gayan);
  console.log(`  Combined total: ${all.length} unique developers`);

  // Write JSON files
  fs.writeFileSync(
    path.join(outputDir, 'borderless.json'),
    JSON.stringify(borderless, null, 2)
  );
  console.log('Written: src/data/borderless.json');

  fs.writeFileSync(
    path.join(outputDir, 'github.json'),
    JSON.stringify(gayan, null, 2)
  );
  console.log('Written: src/data/github.json');

  fs.writeFileSync(
    path.join(outputDir, 'all.json'),
    JSON.stringify(all, null, 2)
  );
  console.log('Written: src/data/all.json');

  console.log('\nData processing complete!');
}

main();
