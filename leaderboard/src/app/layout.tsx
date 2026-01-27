import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Borderless Talent - Developer Leaderboard',
  description: 'Discover top developers from around the world',
  openGraph: {
    title: 'Borderless Talent - Developer Leaderboard',
    description: 'Discover top developers from around the world',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Borderless Talent - Developer Leaderboard',
    description: 'Discover top developers from around the world',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 dark:bg-gray-950 min-h-screen">
        {children}
      </body>
    </html>
  );
}
