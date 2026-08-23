import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Five by Five — Tactical Card Table',
  description: 'A chaotic two-player tactical card game of memory, risk, and questionable figures.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
