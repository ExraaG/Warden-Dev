import React from 'react';
import type { Metadata, Viewport } from 'next';
import './globals.css';
import { RootLayoutClient } from '../components/layout/RootLayoutClient';

export const metadata: Metadata = {
  title: 'Warden - Minecraft Server & Mod Ops',
  description: 'Self-hosted Minecraft server and mod management tool',
  icons: {
    icon: '/logo.svg',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className="dark"
      data-theme="emerald"
      suppressHydrationWarning
      style={{ backgroundColor: '#0d0e11' }}
    >
      <head>
        <link rel="icon" href="/logo.svg" type="image/svg+xml" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const t = localStorage.getItem('warden-theme') || 'emerald';
                document.documentElement.setAttribute('data-theme', t);
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body
        suppressHydrationWarning
        style={{ backgroundColor: '#0d0e11' }}
        className="bg-[var(--bg-main)] text-slate-100 min-h-screen flex flex-col font-sans transition-colors duration-200"
      >
        <RootLayoutClient>{children}</RootLayoutClient>
      </body>
    </html>
  );
}
