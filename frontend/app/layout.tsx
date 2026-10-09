import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'MeshGuard – Secure Self-Healing Network Simulator',
  description: 'Advanced NOC Simulator with Dijkstra routing, self-healing, and security monitoring',
  icons: { icon: 'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22><text y=%2218%22 font-size=%2218%22>\uD83D\uDEE1\uFE0F</text></svg>' },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
