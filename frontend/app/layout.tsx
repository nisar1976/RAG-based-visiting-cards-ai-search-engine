import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Visiting Card Search',
  description: 'Offline RAG-based visiting card search system',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
